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

WINDOW_BACKGROUND = "#F4F7FB"
CARD_BACKGROUND = "#FFFFFF"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#667085"
TEXT_MUTED = "#98A2B3"
BRAND_BLUE = "#1769E0"
BRAND_BLUE_HOVER = "#0F5CCB"
BORDER_COLOR = "#DCE4EE"


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
        self.root.geometry("680x500")
        self.root.minsize(620, 470)
        self.root.resizable(True, True)
        self.root.configure(background=WINDOW_BACKGROUND)

    def _build_widgets(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Primary.TButton", background=BRAND_BLUE, foreground="#FFFFFF",
            borderwidth=0, focusthickness=2, focuscolor="#9CC4FF",
            font=("Microsoft YaHei UI", 10, "bold"), padding=(18, 12),
        )
        style.map(
            "Primary.TButton",
            background=[("disabled", "#AFC8EA"), ("active", BRAND_BLUE_HOVER)],
            foreground=[("disabled", "#F3F7FC")],
        )
        style.configure(
            "Secondary.TButton", background="#FFFFFF", foreground=TEXT_PRIMARY,
            bordercolor=BORDER_COLOR, borderwidth=1, focusthickness=2,
            focuscolor="#9CC4FF", font=("Microsoft YaHei UI", 10, "bold"),
            padding=(18, 11),
        )
        style.map(
            "Secondary.TButton",
            background=[("disabled", "#F2F4F7"), ("active", "#EDF4FF")],
            foreground=[("disabled", "#A8B1BF")],
            bordercolor=[("active", "#8CB8F5")],
        )
        style.configure(
            "Link.TButton", background="#F2F6FC", foreground=BRAND_BLUE,
            borderwidth=0, font=("Microsoft YaHei UI", 9, "bold"), padding=(14, 9),
        )
        style.map(
            "Link.TButton",
            background=[("disabled", "#F2F4F7"), ("active", "#E4EEFC")],
            foreground=[("disabled", "#A8B1BF")],
        )

        shell = tk.Frame(self.root, background=WINDOW_BACKGROUND)
        shell.pack(fill="both", expand=True, padx=34, pady=28)

        header = tk.Frame(shell, background=WINDOW_BACKGROUND)
        header.pack(fill="x", pady=(0, 24))

        heading = tk.Frame(header, background=WINDOW_BACKGROUND)
        heading.pack(side="left")
        tk.Label(
            heading, text="学习平台", background=WINDOW_BACKGROUND,
            foreground=TEXT_PRIMARY, font=("Microsoft YaHei UI", 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            heading, text="本地服务管理中心", background=WINDOW_BACKGROUND,
            foreground=TEXT_SECONDARY, font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(3, 0))



        status_shadow = tk.Frame(shell, background="#E4EAF2")
        status_shadow.pack(fill="x", padx=(2, 0), pady=(0, 20))
        status_card = tk.Frame(
            status_shadow, background=CARD_BACKGROUND,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
        )
        status_card.pack(fill="x", padx=(0, 2), pady=(0, 3))
        self.status_accent = tk.Frame(status_card, width=5, background="#8A94A3")
        self.status_accent.pack(side="left", fill="y")
        status_row = tk.Frame(status_card, background=CARD_BACKGROUND)
        status_row.pack(fill="x", padx=22, pady=20)
        self.status_indicator = tk.Label(
            status_row, text="●", foreground="#7A8491", background=CARD_BACKGROUND,
            font=("Microsoft YaHei UI", 13),
        )
        self.status_indicator.pack(side="left", anchor="n", pady=2)
        status_copy = tk.Frame(status_row, background=CARD_BACKGROUND)
        status_copy.pack(side="left", fill="x", expand=True, padx=(12, 0))
        self.status_text = tk.Label(
            status_copy, text="未启动", background=CARD_BACKGROUND,
            foreground=TEXT_PRIMARY, font=("Microsoft YaHei UI", 15, "bold"),
        )
        self.status_text.pack(anchor="w")
        self.detail_text = tk.Label(
            status_copy, text="平台当前未运行。", background=CARD_BACKGROUND,
            foreground=TEXT_SECONDARY, font=("Microsoft YaHei UI", 9),
            justify="left", wraplength=430,
        )
        self.detail_text.pack(anchor="w", pady=(5, 0))
        self.status_badge = tk.Label(
            status_row, text="未运行", background="#F2F4F7", foreground="#667085",
            font=("Microsoft YaHei UI", 8, "bold"), padx=11, pady=6,
        )
        self.status_badge.pack(side="right", anchor="n")

        address_header = tk.Frame(shell, background=WINDOW_BACKGROUND)
        address_header.pack(fill="x", pady=(0, 8))
        tk.Label(
            address_header, text="访问地址", background=WINDOW_BACKGROUND,
            foreground=TEXT_PRIMARY, font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(side="left")
        tk.Label(
            address_header, text="服务启动后可在浏览器中访问",
            background=WINDOW_BACKGROUND, foreground=TEXT_MUTED,
            font=("Microsoft YaHei UI", 8),
        ).pack(side="right")
        address_card = tk.Frame(
            shell, background=CARD_BACKGROUND,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
        )
        address_card.pack(fill="x")
        self.url_var = tk.StringVar(value="服务启动后显示实际登录地址")
        self.url_entry = tk.Entry(
            address_card, textvariable=self.url_var, state="readonly",
            readonlybackground=CARD_BACKGROUND, foreground=TEXT_SECONDARY,
            relief="flat", borderwidth=0, highlightthickness=0,
            font=("Microsoft YaHei UI", 10), cursor="arrow",
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(16, 8), ipady=13)
        self.copy_button = ttk.Button(
            address_card, text="复制地址", command=self.copy_url,
            state="disabled", style="Link.TButton",
        )
        self.copy_button.pack(side="right", padx=(0, 7), pady=7)

        button_row = tk.Frame(shell, background=WINDOW_BACKGROUND)
        button_row.pack(fill="x", pady=(22, 0))
        self.primary_button = ttk.Button(
            button_row, text="启动服务", command=self.on_primary_action,
            style="Primary.TButton",
        )
        self.primary_button.pack(side="left", fill="x", expand=True)
        self.open_button = ttk.Button(
            button_row, text="打开平台", command=self.open_platform,
            state="disabled", style="Secondary.TButton",
        )
        self.open_button.pack(side="left", fill="x", expand=True, padx=(14, 0))
        tk.Label(
            shell, text="关闭窗口将安全停止本地服务",
            background=WINDOW_BACKGROUND, foreground=TEXT_MUTED,
            font=("Microsoft YaHei UI", 8),
        ).pack(anchor="center", pady=(18, 0))

    def _set_state(self, state: str, detail: str = "") -> None:
        self.state = state
        labels = {
            "not_started": (
                "未启动", "#7A8491", "#F2F4F7", "#667085", "未运行",
                "平台当前未运行。",
            ),
            "starting": (
                "启动中", "#D98B18", "#FFF4D6", "#9A6700", "启动中",
                "正在启动本地服务。",
            ),
            "running": (
                "运行正常", "#12A36D", "#E8F8F1", "#087A50", "运行中",
                "平台已就绪，可以正常访问。",
            ),
            "failed": (
                "启动失败", "#E5484D", "#FDEBEC", "#B4232A", "异常",
                "服务未能正常启动。",
            ),
            "stopping": (
                "正在停止", "#55708F", "#EDF2F7", "#40566F", "停止中",
                "正在关闭本地服务。",
            ),
        }
        (
            title,
            color,
            badge_background,
            badge_foreground,
            badge_text,
            default_detail,
        ) = labels[state]
        self.status_text.configure(text=title)
        self.status_indicator.configure(foreground=color)
        self.status_accent.configure(background=color)
        self.status_badge.configure(
            text=badge_text,
            background=badge_background,
            foreground=badge_foreground,
        )
        self.detail_text.configure(text=detail or default_detail)

        if state in {"not_started", "failed"}:
            self.primary_button.configure(text="启动服务", state="normal")
            self.open_button.configure(state="disabled")
            self.copy_button.configure(state="disabled")
        elif state == "running":
            self.primary_button.configure(text="停止服务", state="normal")
            self.open_button.configure(state="normal")
            self.copy_button.configure(state="normal")
        elif state == "starting":
            self.primary_button.configure(text="正在启动…", state="disabled")
            self.open_button.configure(state="disabled")
            self.copy_button.configure(state="disabled")
        else:
            self.primary_button.configure(text="正在关闭…", state="disabled")
            self.open_button.configure(state="disabled")
            self.copy_button.configure(state="disabled")

    def copy_url(self) -> None:
        if self.state != "running":
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url_var.get())
        self.copy_button.configure(text="已复制")
        self.root.after(1400, lambda: self.copy_button.configure(text="复制地址"))

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
