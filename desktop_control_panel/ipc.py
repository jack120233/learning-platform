"""Named-pipe IPC for control-panel commands.

The pipe is deliberately separate from the local HTTP service.  It is used
only to restore or shut down the GUI process that owns one installed bundle.
"""

from __future__ import annotations

import hashlib
from multiprocessing.connection import AuthenticationError, Client, Listener
from pathlib import Path
import threading
import time
from typing import Callable

from desktop_control_panel.runtime import instance_suffix


def pipe_address(root: Path) -> str:
    return rf"\\.\pipe\LearningPlatformControlPanel-{instance_suffix(root)}"


def pipe_authkey(root: Path) -> bytes:
    return hashlib.sha256(
        f"LearningPlatformControlPanel:{str(root.resolve()).lower()}".encode("utf-8")
    ).digest()


def send_pipe_command(root: Path, command: str, timeout_seconds: float = 2.0) -> bool:
    """Send one command to an existing panel without involving HTTP."""

    # AF_PIPE connection setup is blocking; the named-pipe server is local and
    # ready before a panel advertises its mutex, so a short retry loop handles
    # only the small creation race during startup.
    attempts = max(1, int(timeout_seconds * 10))
    for _ in range(attempts):
        try:
            connection = Client(
                pipe_address(root),
                family="AF_PIPE",
                authkey=pipe_authkey(root),
            )
            try:
                connection.send({"command": command})
                response = connection.recv()
                return bool(isinstance(response, dict) and response.get("ok"))
            finally:
                connection.close()
        except (AuthenticationError, EOFError, OSError):
            time.sleep(0.1)
    return False


class NamedPipeCommandServer:
    """Receives GUI commands on a daemon thread."""

    def __init__(self, root: Path, on_command: Callable[[str], None]) -> None:
        self._root = root
        self._on_command = on_command
        self._listener = Listener(
            pipe_address(root),
            family="AF_PIPE",
            authkey=pipe_authkey(root),
        )
        self._closing = threading.Event()
        self._thread = threading.Thread(
            target=self._serve,
            name="learning-platform-control-pipe",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        if self._closing.is_set():
            return
        # Wake a blocking accept loop before marking the server as closing.
        # Marking it first can let the loop exit between requests and leave a
        # client blocked waiting for an acknowledgement.
        send_pipe_command(self._root, "__close__", timeout_seconds=1)
        self._closing.set()
        self._listener.close()
        self._thread.join(timeout=2)

    def _serve(self) -> None:
        while not self._closing.is_set():
            try:
                connection = self._listener.accept()
            except (AuthenticationError, EOFError, OSError):
                break
            try:
                message = connection.recv()
                command = message.get("command") if isinstance(message, dict) else None
                if command == "__close__":
                    connection.send({"ok": True})
                    break
                if command in {"restore", "shutdown"}:
                    self._on_command(command)
                    connection.send({"ok": True})
                else:
                    connection.send({"ok": False})
            except (EOFError, OSError):
                continue
            finally:
                connection.close()
