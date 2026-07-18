"""Tkinter entry point for the Windows learning-platform control panel."""

from __future__ import annotations

import argparse
from queue import Empty, Queue
import threading
import time
import tkinter as tk
from tkinter import ttk
import webbrowser

from desktop_control_panel import ipc, runtime, win32


POLL_INTERVAL_MS = 150
HEALTH_INTERVAL_SECONDS = 5


class ControlPanel:
    def __init__(
        self,
        root: tk.Tk,
        paths: runtime.RuntimePaths,
        launcher_job: win32.JobObject | None,
    ) -> None:
        self.root = root
        self.paths = paths
        self.launcher_job = launcher_job
        self.command_queue: Queue[str] = Queue()
        self.result_queue: Queue[tuple[str, object]] = Queue()
        self.pipe_server = ipc.NamedPipeCommandServer(
            paths.root,
            self.command_queue.put,
        )
        # New panels use the named pipe.  This event is only observed so an
        # in-place upgrade invoked by the old uninstall launcher can still
        # request a clean shutdown.
        self.legacy_shutdown_event = win32.NamedAutoResetEvent(
            runtime.shutdown_event_name(paths)
        )
        self.backend: runtime.ManagedBackend | None = None
        self.config: runtime.RuntimeConfig | None = None
        self.cancel_start = threading.Event()
        self.state = "not_started"
        self.close_after_stop = False
        self.health_inflight = False
        self.last_health_check = 0.0
        self.stop_failure_detail = ""
        self._destroyed = False

        self._configure_window()
        self._build_widgets()
        self.pipe_server.start()
        self.root.protocol("WM_DELETE_WINDOW", self.request_exit)
        self.root.after(POLL_INTERVAL_MS, self._poll)
        self.root.after(10, self.request_start)

    def _configure_window(self) -> None:
        self.root.title("学习平台控制面板")
        self.root.geometry("560x390")
        self.root.minsize(500, 350)
        self.root.resizable(True, True)
        self.root.configure(padx=26, pady=24)

    def _build_widgets(self) -> None:
        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Status.TLabel", font=("Microsoft YaHei UI", 15, "bold"))
        style.configure("Detail.TLabel", foreground="#5D6673")
        style.configure("Primary.TButton", font=("Microsoft YaHei UI", 10, "bold"))

        ttk.Label(self.root, text="学习平台", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.root,
            text="本地服务控制面板",
            style="Detail.TLabel",
        ).pack(anchor="w", pady=(4, 24))

        status_row = ttk.Frame(self.root)
        status_row.pack(fill="x")
        self.status_indicator = tk.Label(
            status_row,
            width=2,
            text="●",
            fg="#7A8491",
            font=("Microsoft YaHei UI", 16),
        )
        self.status_indicator.pack(side="left", anchor="n")
        status_copy = ttk.Frame(status_row)
        status_copy.pack(side="left", fill="x", expand=True)
        self.status_text = ttk.Label(status_copy, text="未启动", style="Status.TLabel")
        self.status_text.pack(anchor="w")
        self.detail_text = ttk.Label(
            status_copy,
            text="平台当前未运行。",
            style="Detail.TLabel",
            wraplength=460,
        )
        self.detail_text.pack(anchor="w", pady=(4, 0))

        ttk.Label(self.root, text="访问地址").pack(anchor="w", pady=(28, 6))
        self.url_var = tk.StringVar(value="服务启动后显示实际登录地址")
        self.url_entry = ttk.Entry(
            self.root,
            textvariable=self.url_var,
            state="readonly",
            font=("Consolas", 11),
        )
        self.url_entry.pack(fill="x", ipady=8)

        button_row = ttk.Frame(self.root)
        button_row.pack(fill="x", pady=(30, 0))
        self.primary_button = ttk.Button(
            button_row,
            text="启动平台",
            command=self.on_primary_action,
            style="Primary.TButton",
        )
        self.primary_button.pack(side="left", fill="x", expand=True)
        self.open_button = ttk.Button(
            button_row,
            text="打开平台",
            command=self.open_platform,
            state="disabled",
        )
        self.open_button.pack(side="left", fill="x", expand=True, padx=(12, 0))

    def _set_state(self, state: str, detail: str = "") -> None:
        self.state = state
        labels = {
            "not_started": ("未启动", "#7A8491", "平台当前未运行。"),
            "starting": ("启动中", "#B97818", "正在启动本地服务。"),
            "running": ("已启动", "#237A4B", "平台可正常访问。"),
            "failed": ("启动失败", "#B43A3A", "服务未能正常启动。"),
            "stopping": ("停止中", "#4D6680", "正在关闭本地服务。"),
        }
        title, color, default_detail = labels[state]
        self.status_text.configure(text=title)
        self.status_indicator.configure(fg=color)
        self.detail_text.configure(text=detail or default_detail)

        if state in {"not_started", "failed"}:
            self.primary_button.configure(text="启动平台", state="normal")
            self.open_button.configure(state="disabled")
        elif state == "running":
            self.primary_button.configure(text="停止平台", state="normal")
            self.open_button.configure(state="normal")
        elif state == "starting":
            self.primary_button.configure(text="正在启动…", state="disabled")
            self.open_button.configure(state="disabled")
        else:
            self.primary_button.configure(text="正在关闭…", state="disabled")
            self.open_button.configure(state="disabled")

    def on_primary_action(self) -> None:
        if self.state in {"not_started", "failed"}:
            self.request_start()
        elif self.state == "running":
            self.request_stop()

    def request_start(self) -> None:
        if self.state in {"starting", "stopping"}:
            return
        if self.backend is not None:
            self.request_stop(restart_after_stop=True)
            return
        self.cancel_start.clear()
        self._set_state("starting")
        threading.Thread(
            target=self._start_worker,
            name="learning-platform-start",
            daemon=True,
        ).start()

    def _start_worker(self) -> None:
        try:
            backend, config = runtime.start_platform(
                self.paths,
                launcher_job_active=self.launcher_job is not None,
                cancel_event=self.cancel_start,
            )
            self.result_queue.put(("start_ok", (backend, config)))
        except Exception as exc:
            self.result_queue.put(("start_error", str(exc)))

    def request_stop(
        self,
        *,
        close_after_stop: bool = False,
        restart_after_stop: bool = False,
        failure_detail: str = "",
    ) -> None:
        self.close_after_stop = self.close_after_stop or close_after_stop
        self.stop_failure_detail = failure_detail
        if self.state == "starting":
            self.cancel_start.set()
            self._set_state("stopping", "正在取消启动并关闭本地服务。")
            return
        if self.state == "stopping":
            return
        self._set_state("stopping")
        backend = self.backend
        self.backend = None
        threading.Thread(
            target=self._stop_worker,
            args=(backend, restart_after_stop),
            name="learning-platform-stop",
            daemon=True,
        ).start()

    def _stop_worker(
        self,
        backend: runtime.ManagedBackend | None,
        restart_after_stop: bool,
    ) -> None:
        try:
            stopped = runtime.stop_platform(self.paths, backend)
            self.result_queue.put(("stop_ok", (stopped, restart_after_stop)))
        except Exception as exc:
            self.result_queue.put(("stop_error", str(exc)))

    def open_platform(self) -> None:
        if self.config is None or self.backend is None or self.backend.port <= 0:
            return
        webbrowser.open(runtime.login_url(self.config, self.backend.port))

    def request_exit(self) -> None:
        self.request_stop(close_after_stop=True)

    def _restore_window(self) -> None:
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()
        win32.restore_and_focus_window(self.root.winfo_id())

    def _poll(self) -> None:
        if self._destroyed:
            return
        if self.legacy_shutdown_event.is_set():
            self.request_exit()

        while True:
            try:
                command = self.command_queue.get_nowait()
            except Empty:
                break
            if command == "restore":
                self._restore_window()
            elif command == "shutdown":
                self.request_exit()

        while True:
            try:
                kind, payload = self.result_queue.get_nowait()
            except Empty:
                break
            self._handle_result(kind, payload)

        self._schedule_health_check()
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _handle_result(self, kind: str, payload: object) -> None:
        if kind == "start_ok":
            backend, config = payload  # type: ignore[misc]
            self.backend = backend
            self.config = config
            if self.close_after_stop or self.cancel_start.is_set():
                self.request_stop(close_after_stop=True)
                return
            self.url_var.set(runtime.login_url(config, backend.port))
            self._set_state("running")
            self.open_platform()
            return

        if kind == "start_error":
            if self.close_after_stop:
                self._finish()
            else:
                self._set_state("failed", str(payload))
            return

        if kind == "stop_ok":
            stopped, restart_after_stop = payload  # type: ignore[misc]
            if self.close_after_stop:
                self._finish()
                return
            if not stopped:
                self._set_state("failed", "未能完全关闭后端服务，请查看控制面板日志。")
                return
            self.url_var.set("服务启动后显示实际登录地址")
            if self.stop_failure_detail:
                self._set_state("failed", self.stop_failure_detail)
                self.stop_failure_detail = ""
            else:
                self._set_state("not_started")
            if restart_after_stop:
                self.request_start()
            return

        if kind == "stop_error":
            if self.close_after_stop:
                self._finish()
            else:
                self._set_state("failed", f"关闭服务失败：{payload}")
            return

        if kind == "health_result":
            self.health_inflight = False
            if not bool(payload) and self.state == "running":
                self.request_stop(
                    failure_detail="服务健康检查失败，已停止后端；请重新启动。",
                )

    def _schedule_health_check(self) -> None:
        if (
            self.state != "running"
            or self.backend is None
            or self.config is None
            or self.health_inflight
            or time.monotonic() - self.last_health_check < HEALTH_INTERVAL_SECONDS
        ):
            return
        self.last_health_check = time.monotonic()
        self.health_inflight = True
        backend = self.backend
        config = self.config

        def check() -> None:
            healthy = not backend.has_exited() and runtime.is_healthy(config, backend.port)
            self.result_queue.put(("health_result", healthy))

        threading.Thread(
            target=check,
            name="learning-platform-health",
            daemon=True,
        ).start()

    def _finish(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        self.pipe_server.close()
        self.legacy_shutdown_event.close()
        # Do not close launcher_job here.  Its kill-on-close rule is retained
        # until this GUI process exits, guaranteeing cleanup on a crash.
        self.root.destroy()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--shutdown-existing", action="store_true")
    return parser.parse_args()


def _signal_existing_panel(
    paths: runtime.RuntimePaths,
    shutdown: bool,
) -> int:
    command = "shutdown" if shutdown else "restore"
    if ipc.send_pipe_command(paths.root, command):
        if shutdown:
            win32.wait_for_named_mutex_release(runtime.mutex_name(paths), 30)
        return 0

    # The fallback is deliberately only for the former PowerShell panel while
    # an installed copy is being upgraded.  New panels never use HTTP here.
    event_name = (
        runtime.shutdown_event_name(paths)
        if shutdown
        else runtime.restore_event_name(paths)
    )
    if win32.signal_named_event(event_name):
        if shutdown:
            win32.wait_for_named_mutex_release(runtime.mutex_name(paths), 30)
        return 0
    return 1


def main() -> int:
    args = _parse_args()
    paths = runtime.get_runtime_paths()
    mutex = win32.NamedMutex(runtime.mutex_name(paths))
    if mutex.already_exists:
        try:
            return _signal_existing_panel(paths, args.shutdown_existing)
        finally:
            mutex.close()

    if args.shutdown_existing:
        mutex.close()
        return 0

    launcher_job = runtime.create_launcher_job(paths)
    root = tk.Tk()
    try:
        ControlPanel(root, paths, launcher_job)
        root.mainloop()
        return 0
    finally:
        mutex.close()
        # launcher_job intentionally remains open until process termination.


if __name__ == "__main__":
    raise SystemExit(main())
