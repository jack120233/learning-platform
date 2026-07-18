# Windows Python 控制面板实施说明

## 目标

用独立的 Python tkinter 控制面板替换 PowerShell/WPF 启动器。客户端只运行 PyInstaller 打包后的 EXE，正式支持 64 位 Windows 10 和 Windows 11。

## 已确定的实现

- 控制面板、后端均使用当前 Python 3.12 构建为 PyInstaller onedir 产物。
- 控制面板不使用 PowerShell、WPF、系统托盘、pywin32 或代码签名。
- Named Mutex 负责单实例；Named Pipe 是恢复与关闭既有窗口的主 IPC 通道。
- 仅在升级旧版 PowerShell 面板时，才回退使用原有 Named Event。
- 后端固定接收 PORT=0，自行完成 socket bind，并以本次启动令牌写入私有端口报告文件。
- 控制面板只接受报告 PID 为启动根 PID 或其同 EXE 路径子进程的报告，然后检查根页面和健康 API。
- 控制面板启动时优先将自身纳入带 kill-on-close 限制的 Job Object；后端在启动前创建独立 Job Object，并在启动后立即纳入。
- 停止前校验启动根 PID 的真实 EXE 路径；停止服务使用后端 Job Object 或已校验根 PID 的进程树回退。

## 分发

- 便携包根目录直接提供 LearningPlatformControlPanel.exe。
- 安装器、桌面快捷方式和开始菜单快捷方式直接运行该 EXE。
- 卸载器调用 --shutdown-existing，先通过 Named Pipe 通知控制面板关闭服务。
- 构建脚本分别打包后端和控制面板，再把控制面板 EXE 与其 _internal 目录复制到便携包根目录。

## 验证

- 单元测试覆盖命名管道、Mutex、PID 路径查询、端口报告、状态文件和配置。
- 后端测试覆盖端口 0 绑定及原子端口报告。
- 端到端验证在临时便携包中确认：后端报告实际端口、根页面和健康 API 成功、停止后根进程与监听子进程均退出。
