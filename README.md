# Monorepo

## macOS 开发环境一键启动

首次使用前请先按项目依赖说明安装 Homebrew、前后端依赖，并确认 `project_code/backend/.env` 使用 SQLite 配置。可直接参考 [project_code/backend/.env.example](/Users/jacob/Developer/a3.learn_platform/learning-platform/project_code/backend/.env.example)。

```bash
./start-dev-macos.sh
```

脚本会手动启动并检查：

- FastAPI 后端：`http://127.0.0.1:8000`
- Vite 前端：`http://127.0.0.1:3000/login`

若 `.env` 仍显式指向 MySQL，脚本会直接停止并提示改回 SQLite。

不会使用 `brew services start`，因此不会设置开机启动。按 `Ctrl+C` 会停止本脚本启动的服务；如果某个服务在运行前已经存在，脚本只会复用它，不会在退出时停止它。

查看当前状态：

```bash
./start-dev-macos.sh --status
```

日志目录：`logs/dev/`
