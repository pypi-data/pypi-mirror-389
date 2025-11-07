import argparse
import asyncio
import logging
from typing import Awaitable, Callable

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

MessageHandler = Callable[[str, str], Awaitable[None]]
"""Callback function for handling incoming chat messages.

Handlers receive messages in the order they arrive and are called sequentially.
For long-running operations, implementations should delegate work to background
tasks to avoid blocking the message receiver loop.

Args:
    content (str): The message content sent by a user
    username (str): The username of the user who sent the message
"""


class ChatServer:
    """WebSocket-based group chat server for testing and demonstration purposes.

    Manages client connections, message broadcasting, and custom message handlers.
    Supports multiple clients connecting with distinct usernames to participate
    in a shared chat session. Multiple connections with the same username are
    not allowed.

    Example:
        Basic server with a message handler::

            async def handle_message(content: str, username: str):
                print(f"Received '{content}' from {username}")

            server = ChatServer(host="0.0.0.0", port=8723)
            server.add_handler(handle_message)
            await server.start()
            await server.join()
    """

    def __init__(self, host: str = "localhost", port: int = 8723):
        """Initialize the chat server.

        Args:
            host: The hostname or IP address to bind the server to.
                Use "0.0.0.0" to accept connections from any network interface.
            port: The port number to listen on for WebSocket connections.
        """
        self.host = host
        self.port = port

        self._handlers: list[MessageHandler] = []
        self._connections: dict[str, WebSocket] = {}

        self._server: uvicorn.Server | None = None
        self._task: asyncio.Task | None = None

        self._app = FastAPI()
        self._app.websocket("/ws/{username}")(self.connect)

    def add_handler(self, handler: MessageHandler):
        """Register a callback to handle incoming chat messages.

        Handlers are called sequentially in the order that messages arrive from
        clients. This is the same order that messages appear in chat clients.
        For operations that preserve message arrival order (such as adding to a
        queue), perform them directly in the handler. For long-running message
        processing, delegate to background tasks to avoid blocking the message
        receiver loop.

        Args:
            handler: Callback function that receives message content and username.
                Multiple handlers can be registered and will be called in
                registration order for each message.
        """
        self._handlers.append(handler)

    async def start(self):
        """Start the chat server asynchronously.

        Returns immediately after launching the server task. The server runs
        in the background and begins accepting WebSocket connections.
        """
        config = uvicorn.Config(self._app, host=self.host, port=self.port)

        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve())

    async def join(self):
        """Wait for the server to complete.

        Blocks until [`stop`][group_terminal.server.ChatServer.stop] is called
        from another task. If you have other means to keep your main coroutine alive,
        calling [`join`][group_terminal.server.ChatServer.join] is not necessary.
        """
        if self._task:
            await self._task

    async def stop(self):
        """Stop the server gracefully.

        Signals the server to shut down and waits for the server task to complete.
        """
        if self._server:
            self._server.should_exit = True
            self._server = None
        if self._task:
            await self._task
            self._task = None

    async def connect(self, websocket: WebSocket, username: str):
        """Handle a new WebSocket connection."""
        await websocket.accept()

        try:
            # Wait for connection message
            data = await websocket.receive_json()

            if data.get("type") != "connect":
                await websocket.send_json(
                    {"type": "connect_response", "success": False, "message": "First message must be connect"}
                )
                await websocket.close()
                return

            # Check if user already has a connection
            if username in self._connections:
                await websocket.send_json(
                    {"type": "login_response", "success": False, "message": "User already connected"}
                )
                await websocket.close()
                return

            # Store connection
            self._connections[username] = websocket

            # Send success response
            await websocket.send_json(
                {"type": "connect_response", "success": True, "message": "Connected successfully"}
            )

            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                await self._handle_message(data, username)

        except WebSocketDisconnect:
            # Clean up on disconnect
            if username in self._connections:
                del self._connections[username]
        except Exception:
            # Clean up on any error
            if username in self._connections:
                del self._connections[username]
            raise

    async def send_message(self, content: str, sender: str, agent: bool = True):
        """Send a message to all connected clients.

        Broadcasts the message to every client currently connected to the server.
        Failed sends (due to disconnected clients) are handled automatically by
        removing the disconnected client.

        Args:
            content: The message content to send to all clients.
            sender: Name identifying the application or service sending the message.
                This can be any string that identifies your application (e.g.,
                "agent", "bot", "assistant").
            agent: Whether the sender is an application/bot. Applications should
                always use agent=True to indicate that a bot or service is sending
                the message rather than a human user.
        """
        message = {
            "type": "chat_message",
            "content": content,
            "sender": sender,
            "agent": agent,
        }

        # Broadcast to all connected clients
        disconnected = []
        for username, websocket in self._connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                # Mark for removal if send fails
                disconnected.append(username)

        # Remove disconnected clients
        for username in disconnected:
            del self._connections[username]

    async def _handle_message(self, data: dict, username: str):
        if data.get("type") == "chat_message":
            content = data.get("content", "")
            await self.send_message(content, username, agent=False)
            for handler in self._handlers:
                try:
                    await handler(content, username)
                except Exception:
                    logger.exception("Message handler raised an error")


async def main(args):
    server = ChatServer(host=args.host, port=args.port)

    await server.start()
    await server.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8723)
    asyncio.run(main(args=parser.parse_args()))
