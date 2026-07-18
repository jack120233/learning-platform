"""Runtime operations for the bundled Windows learning platform."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from desktop_control_panel import win32


DEFAULT_HOST = "127.0.0.1"
STARTUP_TIMEOUT_SECONDS = 90
HEALTH_TIMEOUT_SECONDS = 2
STATE_FILE_NAME = "control-panel-state.json"
LOGGER_NAME = "learning_platform.control_panel"


class RuntimeErrorMessage(RuntimeError):
    """An actionable runtime failure suitable for the control-panel UI."""


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    config_file: Path
    backend_executable: Path
    frontend_index: Path
    data_directory: Path
    cache_directory: Path
    upload_directory: Path
    log_directory: Path
    state_file: Path
    log_file: Path


@dataclass(frozen=True)
class RuntimeConfig:
    host: str
    values: dict[str, str]


@dataclass(frozen=True)
class RuntimeState:
    process_id: int
    port: int
    login_url: str
    backend_executable: str


@dataclass(frozen=True)
class PortReport:
    process_id: int
    port: int
    token: str


@dataclass
class ManagedBackend:
    process: subprocess.Popen[bytes]
    job: win32.JobObject | None
    executable: Path
    port: int = 0
    service_process_id: int | None = None

    @property
    def process_id(self) -> int:
        return int(self.process.pid)

    def has_exited(self) -> bool:
        return self.process.poll() is not None

    def stop(self) -> bool:
        owned = win32.process_matches_executable(self.process_id, self.executable)
        try:
            if not owned:
                return self.has_exited()
            if self.job is not None:
                stopped = self.job.terminate()
            else:
                stopped = win32.terminate_process_tree(
                    self.process_id,
                    self.executable,
                )
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                stopped = False
            return stopped
        finally:
            if self.job is not None:
                self.job.close()


def resolve_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def get_runtime_paths(root: Path | None = None) -> RuntimePaths:
    resolved_root = (root or resolve_runtime_root()).resolve()
    data_directory = resolved_root / "data"
    log_directory = resolved_root / "logs"
    return RuntimePaths(
        root=resolved_root,
        config_file=resolved_root / "config" / "windows-release.env",
        backend_executable=resolved_root / "backend" / "LearningPlatformBackend.exe",
        frontend_index=resolved_root / "frontend" / "dist" / "index.html",
        data_directory=data_directory,
        cache_directory=data_directory / "cache",
        upload_directory=resolved_root / "uploads",
        log_directory=log_directory,
        state_file=data_directory / STATE_FILE_NAME,
        log_file=log_directory / "control-panel.log",
    )


def configure_logger(paths: RuntimePaths) -> logging.Logger:
    paths.log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    desired_path = str(paths.log_file)
    if not any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == desired_path
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(paths.log_file, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
    return logger


def ensure_runtime_layout(paths: RuntimePaths) -> None:
    missing = [
        path
        for path in (paths.backend_executable, paths.frontend_index)
        if not path.is_file()
    ]
    if missing:
        formatted = "、".join(str(path.relative_to(paths.root)) for path in missing)
        raise RuntimeErrorMessage(f"安装文件缺失：{formatted}。请重新安装学习平台。")

    for directory in (
        paths.data_directory,
        paths.cache_directory,
        paths.upload_directory,
        paths.log_directory,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = value.strip()
    return values


def load_runtime_config(paths: RuntimePaths) -> RuntimeConfig:
    values = _read_env_file(paths.config_file)
    raw_host = values.get("HOST", DEFAULT_HOST).strip().lower()
    if raw_host == "localhost":
        host = DEFAULT_HOST
    elif raw_host == DEFAULT_HOST:
        host = raw_host
    else:
        raise RuntimeErrorMessage("安装版仅允许绑定本机地址 127.0.0.1。")
    return RuntimeConfig(host=host, values=values)


def instance_suffix(root: Path) -> str:
    normalized_root = str(root.resolve()).lower()
    return hashlib.sha256(normalized_root.encode("utf-8")).hexdigest().upper()[:24]


def mutex_name(paths: RuntimePaths) -> str:
    return f"Local\\LearningPlatformControlPanel_{instance_suffix(paths.root)}"


def restore_event_name(paths: RuntimePaths) -> str:
    """Legacy fallback event for the prior PowerShell panel during upgrade."""

    return f"Local\\LearningPlatformControlPanelRestore_{instance_suffix(paths.root)}"


def shutdown_event_name(paths: RuntimePaths) -> str:
    """Legacy fallback event for the prior PowerShell panel during upgrade."""

    return f"Local\\LearningPlatformControlPanelShutdown_{instance_suffix(paths.root)}"


def login_url(config: RuntimeConfig, port: int) -> str:
    return f"http://{config.host}:{port}/login"


def root_url(config: RuntimeConfig, port: int) -> str:
    return f"http://{config.host}:{port}/"


def health_url(config: RuntimeConfig, port: int) -> str:
    return f"http://{config.host}:{port}/api/v1/health"


def _build_backend_environment(
    paths: RuntimePaths,
    config: RuntimeConfig,
    session_token: str,
    report_file: Path,
) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(config.values)
    environment.update(
        {
            "HOST": config.host,
            # The backend owns the bind operation.  It chooses an available
            # local port and writes that concrete port to its private report.
            "PORT": "0",
            "LEARNING_PLATFORM_RUNTIME_ROOT": str(paths.root),
            "APP_RUNTIME_ROOT": str(paths.root),
            "LOCAL_DATA_DIR": str(paths.data_directory),
            "LOCAL_CACHE_DIR": str(paths.cache_directory),
            "UPLOAD_DIR": str(paths.upload_directory),
            "LOG_DIR": str(paths.log_directory),
            "FRONTEND_DIST_DIR": str(paths.frontend_index.parent),
            "FRONTEND_INDEX_PATH": str(paths.frontend_index),
            "LOCAL_DATABASE_FILENAME": "windows-local.db",
            "LEARNING_PLATFORM_PORT_REPORT_FILE": str(report_file),
            "LEARNING_PLATFORM_SESSION_TOKEN": session_token,
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    return environment


def create_launcher_job(paths: RuntimePaths) -> win32.JobObject | None:
    """Join the GUI to a kill-on-close job before it spawns the backend."""

    logger = configure_logger(paths)
    job = win32.JobObject()
    try:
        job.assign_current_process()
    except win32.Win32Error as exc:
        logger.warning(
            "Could not assign the control panel to a launcher Job Object: %s",
            exc,
        )
        job.close()
        return None
    logger.info("Control panel joined launcher Job Object")
    return job


def launch_backend(
    paths: RuntimePaths,
    config: RuntimeConfig,
    session_token: str,
    report_file: Path,
    launcher_job_active: bool,
) -> ManagedBackend:
    """Create a backend Job Object first, then start and attach the backend."""

    logger = configure_logger(paths)
    backend_job = win32.JobObject()
    process = subprocess.Popen(
        [str(paths.backend_executable)],
        cwd=str(paths.backend_executable.parent),
        env=_build_backend_environment(paths, config, session_token, report_file),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        if not win32.process_matches_executable(process.pid, paths.backend_executable):
            raise RuntimeErrorMessage("后端进程路径校验失败，已拒绝启动。")
        try:
            backend_job.assign_process(process.pid)
        except win32.Win32Error as exc:
            backend_job.close()
            backend_job = None
            if not launcher_job_active:
                raise RuntimeErrorMessage(
                    "无法将后端纳入进程生命周期监管，已取消启动。"
                ) from exc
            logger.warning(
                "Backend-specific Job Object unavailable; using inherited launcher job: %s",
                exc,
            )
        logger.info("Started backend PID=%s with port=0", process.pid)
        return ManagedBackend(
            process=process,
            job=backend_job,
            executable=paths.backend_executable,
        )
    except Exception:
        if backend_job is not None:
            backend_job.close()
        if win32.process_matches_executable(process.pid, paths.backend_executable):
            win32.terminate_process_tree(process.pid, paths.backend_executable)
        raise


def _read_port_report(report_file: Path) -> PortReport | None:
    if not report_file.is_file():
        return None
    try:
        raw = json.loads(report_file.read_text(encoding="utf-8"))
        process_id = int(raw["pid"])
        port = int(raw["port"])
        token = str(raw["token"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
    if process_id <= 0 or not 1 <= port <= 65535 or not token:
        return None
    return PortReport(process_id=process_id, port=port, token=token)


def wait_for_port_report(
    backend: ManagedBackend,
    report_file: Path,
    session_token: str,
    deadline: float,
    cancel_event: object | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    while time.monotonic() < deadline:
        if cancel_event is not None and getattr(cancel_event, "is_set")():
            raise RuntimeErrorMessage("启动已取消。")
        if backend.has_exited():
            raise RuntimeErrorMessage("后端在绑定本地端口前已退出。")
        report = _read_port_report(report_file)
        if (
            report is not None
            and report.token == session_token
            and win32.process_matches_executable(
                report.process_id,
                backend.executable,
            )
            and win32.is_process_descendant(
                report.process_id,
                backend.process_id,
            )
        ):
            backend.service_process_id = report.process_id
            return report.port
        sleep(0.1)
    raise RuntimeErrorMessage("后端未在限定时间内回报实际端口。")


def _request_succeeds(url: str) -> bool:
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=HEALTH_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 300
    except (OSError, URLError):
        return False


def is_healthy(config: RuntimeConfig, port: int) -> bool:
    return _request_succeeds(root_url(config, port)) and _request_succeeds(
        health_url(config, port)
    )


def wait_for_health(
    backend: ManagedBackend,
    config: RuntimeConfig,
    deadline: float,
    cancel_event: object | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    while time.monotonic() < deadline:
        if cancel_event is not None and getattr(cancel_event, "is_set")():
            return False
        if backend.has_exited():
            return False
        if is_healthy(config, backend.port):
            return True
        sleep(0.5)
    return False


def write_runtime_state(
    paths: RuntimePaths,
    backend: ManagedBackend,
    config: RuntimeConfig,
) -> None:
    state = {
        "process_id": backend.process_id,
        "service_process_id": backend.service_process_id,
        "port": backend.port,
        "login_url": login_url(config, backend.port),
        "backend_executable": str(backend.executable),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    temporary_file = paths.state_file.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(state, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_file, paths.state_file)


def read_runtime_state(paths: RuntimePaths) -> RuntimeState | None:
    if not paths.state_file.is_file():
        return None
    try:
        raw = json.loads(paths.state_file.read_text(encoding="utf-8"))
        process_id = int(raw["process_id"])
        port = int(raw["port"])
        url = str(raw["login_url"])
        executable = str(raw["backend_executable"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
    if process_id <= 0 or not 1 <= port <= 65535:
        return None
    return RuntimeState(process_id, port, url, executable)


def remove_runtime_state(paths: RuntimePaths) -> None:
    paths.state_file.unlink(missing_ok=True)
    paths.state_file.with_suffix(".tmp").unlink(missing_ok=True)


def clean_stale_runtime(paths: RuntimePaths) -> None:
    state = read_runtime_state(paths)
    if state is None:
        remove_runtime_state(paths)
        return
    if win32.process_matches_executable(state.process_id, paths.backend_executable):
        logger = configure_logger(paths)
        logger.warning("Stopping stale owned backend PID=%s", state.process_id)
        win32.terminate_process_tree(state.process_id, paths.backend_executable)
    remove_runtime_state(paths)


def start_platform(
    paths: RuntimePaths,
    launcher_job_active: bool,
    cancel_event: object | None = None,
) -> tuple[ManagedBackend, RuntimeConfig]:
    ensure_runtime_layout(paths)
    config = load_runtime_config(paths)
    logger = configure_logger(paths)
    clean_stale_runtime(paths)

    session_token = uuid4().hex
    report_file = paths.data_directory / f"backend-port-{session_token}.json"
    report_file.unlink(missing_ok=True)
    backend: ManagedBackend | None = None
    started = False
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    try:
        backend = launch_backend(
            paths,
            config,
            session_token,
            report_file,
            launcher_job_active,
        )
        backend.port = wait_for_port_report(
            backend,
            report_file,
            session_token,
            deadline,
            cancel_event,
        )
        if not wait_for_health(backend, config, deadline, cancel_event):
            raise RuntimeErrorMessage(
                f"后端未能在 {STARTUP_TIMEOUT_SECONDS} 秒内通过健康检查。"
            )
        write_runtime_state(paths, backend, config)
        logger.info("Backend healthy PID=%s port=%s", backend.process_id, backend.port)
        started = True
        return backend, config
    finally:
        report_file.unlink(missing_ok=True)
        if backend is not None and not started:
            backend.stop()


def stop_platform(paths: RuntimePaths, backend: ManagedBackend | None) -> bool:
    logger = configure_logger(paths)
    try:
        if backend is not None:
            return backend.stop()
        state = read_runtime_state(paths)
        if state is None:
            return True
        if not win32.process_matches_executable(
            state.process_id,
            paths.backend_executable,
        ):
            return True
        return win32.terminate_process_tree(
            state.process_id,
            paths.backend_executable,
        )
    finally:
        remove_runtime_state(paths)
        logger.info("Stopped backend service")
