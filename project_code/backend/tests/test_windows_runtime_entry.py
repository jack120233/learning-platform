from __future__ import annotations

import json
from pathlib import Path

from scripts import windows_runtime_entry


def test_runtime_listener_uses_ephemeral_port_and_reports_it(tmp_path, monkeypatch):
    report_file = tmp_path / "runtime-port.json"
    monkeypatch.setenv("LEARNING_PLATFORM_PORT_REPORT_FILE", str(report_file))
    monkeypatch.setenv("LEARNING_PLATFORM_SESSION_TOKEN", "session-token")

    listener = windows_runtime_entry._create_runtime_listener("127.0.0.1", 0)
    try:
        selected_port = int(listener.getsockname()[1])
        windows_runtime_entry._write_runtime_port_report(selected_port)
    finally:
        listener.close()

    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert payload == {
        "pid": windows_runtime_entry.os.getpid(),
        "port": selected_port,
        "token": "session-token",
    }
    assert selected_port > 0


def test_runtime_port_report_is_optional(tmp_path, monkeypatch):
    monkeypatch.delenv("LEARNING_PLATFORM_PORT_REPORT_FILE", raising=False)
    monkeypatch.delenv("LEARNING_PLATFORM_SESSION_TOKEN", raising=False)

    windows_runtime_entry._write_runtime_port_report(12345)

    assert list(Path(tmp_path).iterdir()) == []
