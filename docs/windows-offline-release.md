# Windows 离线交付说明

## 适用系统与交付内容

本安装包支持 64 位 Windows 10 和 Windows 11。

- 客户端无需安装 Python、PowerShell 模块、.NET Desktop Runtime 或系统托盘组件。
- 包内包含 LearningPlatformControlPanel.exe、后端 EXE、前端静态文件和本地 SQLite 数据。
- 安装包在当前用户目录安装，并创建桌面和开始菜单的 学习平台 快捷方式。
- 便携包可直接双击根目录的 LearningPlatformControlPanel.exe。

## 使用说明

1. 安装 学习平台-Setup.exe。
2. 安装完成后可勾选“立即启动学习平台”，或之后双击快捷方式。
3. 控制面板自动启动本地后端，健康检查成功后打开默认浏览器登录页。
4. 控制面板显示实际登录地址；该地址每次启动可能不同。
5. 点击“停止平台”或直接关闭控制面板，都会停止本地服务。

已打开的浏览器不会被强制关闭；服务停止后，本地页面将无法继续访问。

## 控制面板行为

- 同一安装目录只允许一个控制面板实例。
- 再次启动时，通过 Windows Named Pipe 向已有实例发送恢复命令，不会启动第二个后端或再次自动打开浏览器。
- 后端自行绑定 127.0.0.1:0，由操作系统分配可用端口，并通过仅供本次启动使用的状态文件回报实际端口。
- 控制面板确认根页面与 /api/v1/health 都成功后，才显示“已启动”。
- 控制面板先加入 Windows Job Object；后端再加入独立 Job Object。关闭服务会结束后端及其子进程，控制面板异常退出也会由 Job Object 清理后端。
- 停止前会核验 PID 对应的真实 EXE 路径，只有当前包内的 backend/LearningPlatformBackend.exe 才会被终止。
- 不使用系统托盘；最小化保持在任务栏，关闭窗口即停止服务并退出。

## 构建说明

源码环境执行：

    powershell -ExecutionPolicy Bypass -File .\scripts\build-windows-release.ps1

构建机需要项目的 Python 虚拟环境、npm 和可选的 Inno Setup。交付给客户端的产物不依赖这些工具。

构建脚本会：

- 构建前端 UI/dist；
- 使用 PyInstaller 分别生成后端和 tkinter 控制面板的 onedir 运行时；
- 组装 build/windows-release/bundle/；
- 在检测到 Inno Setup 时输出 学习平台-Setup.exe。

## 卸载策略

卸载器会先以 --shutdown-existing 通知正在运行的控制面板关闭服务；随后清理安装目录下的：

- data/
- logs/
- uploads/

该交付版默认执行完整清理。
