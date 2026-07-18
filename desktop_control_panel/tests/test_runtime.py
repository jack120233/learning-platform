from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from desktop_control_panel import runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.paths = runtime.get_runtime_paths(self.root)
        self.paths.config_file.parent.mkdir(parents=True)
        self.paths.data_directory.mkdir()
        self.paths.log_directory.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_load_config_normalizes_localhost(self) -> None:
        self.paths.config_file.write_text("HOST=localhost\nPORT=8000\n", encoding="utf-8")

        config = runtime.load_runtime_config(self.paths)

        self.assertEqual(config.host, "127.0.0.1")

    def test_load_config_rejects_non_local_host(self) -> None:
        self.paths.config_file.write_text("HOST=0.0.0.0\n", encoding="utf-8")

        with self.assertRaisesRegex(runtime.RuntimeErrorMessage, "127.0.0.1"):
            runtime.load_runtime_config(self.paths)

    def test_backend_environment_forces_port_zero_and_private_report(self) -> None:
        config = runtime.RuntimeConfig(host="127.0.0.1", values={"PORT": "8000"})
        report_file = self.paths.data_directory / "report.json"

        environment = runtime._build_backend_environment(
            self.paths,
            config,
            "session-token",
            report_file,
        )

        self.assertEqual(environment["PORT"], "0")
        self.assertEqual(environment["LEARNING_PLATFORM_PORT_REPORT_FILE"], str(report_file))
        self.assertEqual(environment["LEARNING_PLATFORM_SESSION_TOKEN"], "session-token")

    def test_read_port_report_requires_valid_payload(self) -> None:
        report_file = self.paths.data_directory / "report.json"
        report_file.write_text(
            json.dumps({"pid": 123, "port": 18000, "token": "token"}),
            encoding="utf-8",
        )

        report = runtime._read_port_report(report_file)

        self.assertEqual(report, runtime.PortReport(123, 18000, "token"))
        report_file.write_text('{"pid":"bad"}', encoding="utf-8")
        self.assertIsNone(runtime._read_port_report(report_file))

    def test_runtime_state_round_trip(self) -> None:
        backend = type(
            "Backend",
            (),
            {
                "process_id": 456,
                "port": 18001,
                "executable": self.paths.backend_executable,
                "service_process_id": 789,
            },
        )()
        config = runtime.RuntimeConfig(host="127.0.0.1", values={})

        runtime.write_runtime_state(self.paths, backend, config)

        self.assertEqual(
            runtime.read_runtime_state(self.paths),
            runtime.RuntimeState(
                process_id=456,
                port=18001,
                login_url="http://127.0.0.1:18001/login",
                backend_executable=str(self.paths.backend_executable),
            ),
        )

    def test_health_requires_frontend_and_api(self) -> None:
        config = runtime.RuntimeConfig(host="127.0.0.1", values={})
        with patch(
            "desktop_control_panel.runtime._request_succeeds",
            side_effect=[True, False],
        ) as request:
            self.assertFalse(runtime.is_healthy(config, 18002))

        self.assertEqual(request.call_count, 2)

    def test_instance_suffix_is_stable_for_same_root(self) -> None:
        self.assertEqual(
            runtime.instance_suffix(self.root),
            runtime.instance_suffix(self.root),
        )
        self.assertNotEqual(
            runtime.instance_suffix(self.root),
            runtime.instance_suffix(self.root / "other"),
        )


if __name__ == "__main__":
    unittest.main()
