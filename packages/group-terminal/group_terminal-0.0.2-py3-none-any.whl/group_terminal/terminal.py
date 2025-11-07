import asyncio
import os
import sys
import termios
import tty
from abc import ABC, abstractmethod
from contextlib import contextmanager

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text


class MessageSender(ABC):
    @abstractmethod
    async def send_message(self, content: str):
        pass


class TerminalInterface:
    def __init__(
        self,
        message_sender: MessageSender,
        username: str,
        user_color: str = "orange1",
        agent_color: str = "green",
        human_color: str = "cyan",
        input_color: str = "orange1",
        rule_color: str = "grey23",
    ):
        self._message_sender = message_sender
        self._username = username

        self._user_color = user_color
        self._agent_color = agent_color
        self._human_color = human_color
        self._input_color = input_color
        self._rule_color = rule_color
        self._console = Console()

        self._live: Live = None
        self._input_buffer = ""
        self._cursor_pos = 0
        self._pending: list[tuple[str, str, bool]] = []
        self._shutdown: asyncio.Event = asyncio.Event()

    def add_chat_message(self, message: str, sender: str, agent: bool = False):
        if self._live is None:
            # Live not started yet; queue message
            self._pending.append((message, sender, agent))
            return

        if sender == self._username:
            sender_color = self._user_color
        elif agent:
            sender_color = self._agent_color
        else:
            sender_color = self._human_color

        self._live.console.print(Rule(style=self._rule_color))
        self._live.console.print(f"[bold {sender_color}]{sender}[/]: {message}", highlight=False)

    async def run(self):
        with self._raw_mode():
            with Live(
                self._input_panel(),
                console=self._console,
                screen=False,
                auto_refresh=False,
            ) as live:
                self._live = live

                # Flush any pending messages
                for message, sender, agent in self._pending:
                    self.add_chat_message(message, sender, agent)
                self._pending.clear()

                # Keep live display active until shutdown is requested
                while not self._shutdown.is_set():
                    await asyncio.sleep(0.1)

    def shutdown(self):
        self._shutdown.set()

    @contextmanager
    def _raw_mode(self):
        """Context manager that configures terminal in cbreak mode without echo
        and registers the stdin reader callback. Restores settings on exit."""
        loop = asyncio.get_running_loop()
        fd = sys.stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            new_attrs = termios.tcgetattr(fd).copy()
            new_attrs[3] &= ~termios.ECHO  # disable echo
            termios.tcsetattr(fd, termios.TCSANOW, new_attrs)
            loop.add_reader(fd, self._on_key)
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)
            loop.remove_reader(fd)

    def _on_key(self):
        """Handle key presses, cursor moves, and pasted input.

        Reads every available byte from stdin in one shot so that large
        pastes are processed immediately instead of character-by-character
        across multiple event-loop iterations.
        """

        # ----------------------------------------------------------------------------
        #  TODO: replace with a more elaborate solution using an appropriate library
        # ----------------------------------------------------------------------------

        fd = sys.stdin.fileno()
        # `add_reader` guarantees the FD is ready, so this read is non-blocking.
        data = os.read(fd, 4096).decode(errors="ignore")
        if not data:
            return

        updated = False  # Track whether the input panel needs to be refreshed
        i = 0
        length = len(data)

        while i < length:
            ch = data[i]

            # Handle newline / return (submit input)
            if ch in ("\r", "\n"):
                if self._input_buffer:
                    asyncio.create_task(self._on_enter())
                i += 1
                continue

            # Handle backspace
            if ch in ("\x7f", "\b"):
                if self._cursor_pos > 0:
                    self._input_buffer = (
                        self._input_buffer[: self._cursor_pos - 1] + self._input_buffer[self._cursor_pos :]
                    )
                    self._cursor_pos -= 1
                    updated = True
                i += 1
                continue

            # Handle simple ANSI cursor esc sequences (arrow keys)
            if ch == "\x1b" and i + 2 < length and data[i + 1] == "[":
                direction = data[i + 2]
                if direction == "C":  # Right arrow
                    if self._cursor_pos < len(self._input_buffer):
                        self._cursor_pos += 1
                        updated = True
                elif direction == "D":  # Left arrow
                    if self._cursor_pos > 0:
                        self._cursor_pos -= 1
                        updated = True
                # Skip the full escape sequence (ESC [ X)
                i += 3
                continue

            # Default: printable character – insert at cursor
            self._input_buffer = self._input_buffer[: self._cursor_pos] + ch + self._input_buffer[self._cursor_pos :]
            self._cursor_pos += 1
            updated = True
            i += 1

        # Refresh display once per batch to avoid excessive updates
        if updated and self._live is not None:
            self._live.update(self._input_panel(), refresh=True)

    async def _on_enter(self):
        _input = self._input_buffer.strip()
        self._input_buffer = ""
        self._cursor_pos = 0
        self._live.update(self._input_panel(), refresh=True)

        if _input == "/exit":
            self.shutdown()
        else:
            await self._message_sender.send_message(_input)

    def _input_panel(self) -> Panel:
        cursor = Text("█", style="bold")
        txt = Text()

        # Add text before cursor
        if self._cursor_pos > 0:
            txt.append(self._input_buffer[: self._cursor_pos])

        # Add cursor
        txt.append(cursor)

        # Add text after cursor
        if self._cursor_pos < len(self._input_buffer):
            txt.append(self._input_buffer[self._cursor_pos :])

        return Panel(txt, title="Input", border_style=self._input_color)
