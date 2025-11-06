import argparse
import asyncio
import json

import websockets
from fastapi import WebSocket

from group_terminal.terminal import MessageSender, TerminalInterface


class ChatClient(MessageSender):
    """Terminal-based chat client for testing and demonstration purposes.

    Provides a [Rich](https://github.com/Textualize/rich)-based terminal
    interface for interacting with a group of users and services connected to
    a [ChatServer][group_terminal.server.ChatServer] instance.
    Intended for testing and demonstration only, not for production use in applications.
    The client is typically started from the command line using:
    `python -m group_terminal.client --username <username>`.

    Note:
        This client uses [termios](https://docs.python.org/3/library/termios.html) for terminal
        control and is Unix-specific. It will not work on Windows systems.
    """

    def __init__(self, username: str, host: str = "localhost", port: int = 8723, **terminal_kwargs):
        """Initialize the chat client.

        Args:
            username: The name of the this client's user.
            host: The hostname or IP address of the chat server.
            port: The port number of the chat server.
        """
        self.username = username
        self.host = host
        self.port = port

        self._websocket: WebSocket | None = None

        self._terminal_interface: TerminalInterface | None = None
        self._terminal_kwargs = terminal_kwargs

        self._receiver_task: asyncio.Task | None = None
        self._terminal_task: asyncio.Task | None = None

    async def join(self):
        """Join a connected client until disconnected."""
        if self._terminal_task is None:
            raise RuntimeError("Not connected")
        await self._terminal_task

    async def connect(self) -> bool:
        """Connect to the chat server."""
        try:
            # Create WebSocket connection
            self._websocket = await websockets.connect(f"ws://{self.host}:{self.port}/ws/{self.username}")

            # Send connect message
            await self._websocket.send(json.dumps({"type": "connect", "username": self.username}))

            # Wait for connect response
            response = await self._websocket.recv()
            data = json.loads(response)

            if data.get("type") == "connect_response" and data.get("success"):
                print(f"User {self.username} connected.")

                # Start terminal
                self._terminal_task = asyncio.create_task(self._start_interface())

                # Start message receiver loop
                self._receiver_task = asyncio.create_task(self._receive_messages())

                return True
            else:
                await self._websocket.close()
                print(f"Connection failed: {data.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def _start_interface(self):
        self._terminal_interface = TerminalInterface(self, self.username, **self._terminal_kwargs)
        await self._terminal_interface.run()

    async def _receive_messages(self):
        """Continuously receive messages from WebSocket."""
        try:
            while self._websocket:
                data = await self._websocket.recv()
                message = json.loads(data)

                if message.get("type") == "chat_message":
                    content = message.get("content", "")
                    sender = message.get("sender", "unknown")
                    agent = message.get("agent", False)
                    self.handle_message(content, sender, agent)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server")
            if self._terminal_interface:
                self._terminal_interface.shutdown()
        except Exception as e:
            print(f"Error receiving messages: {e}")

    def handle_message(self, content: str, sender: str, agent: bool):
        if self._terminal_interface is not None:
            self._terminal_interface.add_chat_message(content, sender, agent)

    async def send_message(self, content: str):
        if self._websocket:
            message = {"type": "chat_message", "content": content}
            await self._websocket.send(json.dumps(message))
        else:
            print("Not connected to server")
            pass


async def main(args):
    if args.username is None:
        username = await asyncio.get_running_loop().run_in_executor(None, input, "Enter username: ")
    else:
        username = args.username

    client = ChatClient(username=username, host=args.host, port=args.port)

    if await client.connect():
        await client.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", type=str, default=None)
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8723)
    asyncio.run(main(args=parser.parse_args()))
