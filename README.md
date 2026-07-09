# Monorepo

## macOS 开发环境一键启动

首次使用前请先按项目依赖说明安装 Homebrew、前后端依赖，并确认 `project_code/backend/.env` 使用 SQLite 配置。可直接参考 `project_code/backend/.env.example`。

```bash
./start-dev-macos.sh
```

脚本会手动启动并检查：

- FastAPI 后端：`http://127.0.0.1:8000`
- Vite 前端：`http://127.0.0.1:3000/login`

若 `.env` 仍显式指向 MySQL，脚本会直接停止并提示改回 SQLite。

## SQLite 初始化

当前项目的文件型 SQLite 已统一为单一标准首启流程：

- 正常初始化：启动后端，或手动执行 `python project_code/backend/scripts/init_db.py`
- 首启重置：执行 `python project_code/backend/scripts/reset_local_state.py`

首次启动或空状态执行 `init_db.py` 时，会完成标准 SQLite 初始化：建表、默认权限、基础数据和演示数据。  
后续启动只检查 SQLite 文件和 bootstrap 清单，不再自动建表、补字段、补权限、补种子，也不会自动删库重建。  
`reset_local_state.py` 会清空 SQLite、bootstrap 清单、`uploads/`、缓存目录和日志目录。  
如果遇到旧库或非标准库，只能先执行 `reset_local_state.py`，启动过程不会自动修复。

不会使用 `brew services start`，因此不会设置开机启动。按 `Ctrl+C` 会停止本脚本启动的服务；如果某个服务在运行前已经存在，脚本只会复用它，不会在退出时停止它。

查看当前状态：

```bash
./start-dev-macos.sh --status
```

日志目录：`logs/dev/`
