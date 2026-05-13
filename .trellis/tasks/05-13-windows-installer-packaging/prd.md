# brainstorm: Windows 一键安装打包方案

## Goal

把当前在线学习平台打包成 Windows 用户可安装的软件，重点是让使用者不需要打开命令行、不需要手动初始化 MySQL 或 Redis，也能完成安装、初始化数据库并启动使用。

## What I already know

* 用户是小白，希望用容易理解的方式判断打包方案。
* 当前项目是 Vue 3 + Vite 前端、FastAPI 后端。
* 后端依赖数据库与缓存：`requirements.txt` 包含 `aiomysql`、`pymysql`、`redis`。
* 后端配置从 `.env` / 环境变量读取，关键项包括 `database_url`、`redis_url`、`jwt_secret_key`。
* 现有数据库初始化脚本包括 `project_code/backend/scripts/init_db.py` 和 `project_code/backend/scripts/seed_data.py`。
* 现有 Windows 启动脚本仍偏开发者使用，会启动后端/前端开发服务，不是面向最终用户的一键安装器。

## Assumptions (temporary)

* 目标用户使用 Windows。
* 目标用户不懂命令行，也不应手动执行初始化数据库命令。
* 打包产物应尽量包含运行所需组件，减少安装前置条件。

## Open Questions

* 目标形态是单机离线一键安装，还是企业/局域网服务器部署后多人访问？

## Requirements (evolving)

* 安装过程不能要求普通用户手动打开命令行初始化数据库。
* 安装器或首次启动程序需要自动完成数据库建表与种子数据初始化。
* 需要处理 MySQL 和 Redis 的安装/启动/配置问题。

## Acceptance Criteria (evolving)

* [ ] 普通用户双击安装包即可安装。
* [ ] 首次运行自动完成数据库初始化。
* [ ] 用户无需手动执行 `python scripts/init_db.py` 或 `seed_data.py`。
* [ ] 安装后能通过桌面入口或开始菜单入口启动系统。

## Definition of Done (team quality bar)

* Tests added/updated if implementation changes code.
* Build/typecheck/pytest according to changed frontend/backend scope.
* Docs/notes updated if packaging behavior changes.
* Rollback/uninstall and data preservation considered.

## Out of Scope (explicit)

* 暂不直接开始改代码或制作安装包，先确认产品形态和技术路线。

## Technical Notes

* Frontend package: `UI/package.json`, build command `npm run build`.
* Backend dependencies: `project_code/backend/requirements.txt`.
* Backend config: `project_code/backend/app/config.py`.
* Existing scripts: `project_code/backend/scripts/init_db.py`, `project_code/backend/scripts/seed_data.py`.
* Existing Windows launchers: `start.bat`, `start-backend-mysql.cmd` are development-style startup scripts, not end-user installers.
