from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from uuid import uuid4

from desktop_control_panel import ipc, win32


class IpcAndWin32Tests(unittest.TestCase):
    def test_named_pipe_delivers_restore_command(self) -> None:
        received: list[str] = []
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            server = ipc.NamedPipeCommandServer(root, received.append)
            try:
                server.start()
                self.assertTrue(ipc.send_pipe_command(root, "restore"))
                deadline = time.monotonic() + 2
                while not received and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertEqual(received, ["restore"])
            finally:
                server.close()

    def test_mutex_reports_existing_instance(self) -> None:
        name = f"Local\\LearningPlatformControlPanelTest_{uuid4().hex}"
        first = win32.NamedMutex(name)
        second = win32.NamedMutex(name)
        try:
            self.assertFalse(first.already_exists)
            self.assertTrue(second.already_exists)
        finally:
            second.close()
            first.close()

    def test_process_image_path_and_path_comparison(self) -> None:
        image_path = win32.get_process_image_path(os.getpid())

        self.assertIsNotNone(image_path)
        self.assertTrue(win32.paths_match(image_path, image_path))
        self.assertTrue(win32.is_process_descendant(os.getpid(), os.getpid()))


if __name__ == "__main__":
    unittest.main()
