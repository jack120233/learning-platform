# Monorepo

## macOS 开发环境一键启动

首次使用前请先按项目依赖说明安装 Homebrew、MySQL 8.4、Redis、前后端依赖，并确认 `project_code/backend/.env` 使用 MySQL 配置。

```bash
./start-dev-macos.sh
```

脚本会手动启动并检查：

- MySQL 8.4：`127.0.0.1:3306`
- Redis：`127.0.0.1:6379`
- FastAPI 后端：`http://127.0.0.1:8000`
- Vite 前端：`http://127.0.0.1:3000/login`

不会使用 `brew services start`，因此不会设置开机启动。按 `Ctrl+C` 会停止本脚本启动的服务；如果某个服务在运行前已经存在，脚本只会复用它，不会在退出时停止它。

查看当前状态：

```bash
./start-dev-macos.sh --status
```

日志目录：`logs/dev/`
