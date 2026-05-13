# Windows 单机版开发任务清单

> 更新时间：2026-05-13  
> 目标分支：`future/windows-local`  
> 依赖基础分支：`future/windows-base`  
> 详细设计：[`windows-local-implementation-details.md`](./windows-local-implementation-details.md)

## 0. 开发前检查

开始任何单机版专属改动前必须确认：

```bash
git branch --show-current
```

必须位于：

```text
future/windows-local
```

如果当前在 `future/windows-base`，只能做共享基础层；如果当前在 `future/windows-classroom`，不能做单机版专属改动。

## 1. 当前已完成基础

这些已在 `future/windows-base` 完成，单机版分支应继承：

- [x] `APP_EDITION` / `app_edition` 运行形态。
- [x] `windows_local` 配置值。
- [x] Windows 版默认 SQLite 文件数据库。
- [x] Windows 版默认 `diskcache`。
- [x] 启动时创建运行目录。
- [x] SQLite 文件库连接 `timeout`。
- [x] 运行配置与缓存抽象测试。

## 2. Phase 1：单机版配置文件与启动环境

目标：提供单机版默认环境配置，避免用户手动设置命令行变量。

建议文件：

- [ ] `config/windows-local.env`
- [ ] `start-windows-local.cmd`
- [ ] 如需跨平台辅助，可新增 `scripts/` 下的启动辅助脚本。

配置要求：

```env
APP_EDITION=windows_local
HOST=127.0.0.1
PORT=8000
CACHE_BACKEND=auto
```

验收项：

- [ ] 启动脚本能设置 `APP_EDITION=windows_local`。
- [ ] 不要求用户手动输入数据库连接串。
- [ ] 不要求用户启动 Redis。
- [ ] 不要求用户启动 MySQL。
- [ ] 启动失败时窗口不直接关闭，并提示日志位置。

## 3. Phase 2：自动初始化闭环

目标：首次启动自动完成数据库准备和必要种子数据导入。

重点文件：

- [ ] `project_code/backend/app/main.py`
- [ ] `project_code/backend/app/core/runtime.py`
- [ ] `project_code/backend/app/core/db_schema.py`
- [ ] `project_code/backend/scripts/init_db.py`
- [ ] `project_code/backend/scripts/seed_data.py`

实现要求：

- [ ] 首次启动自动创建 SQLite 文件。
- [ ] 首次启动自动建表。
- [ ] 首次启动自动执行 schema 兼容检查。
- [ ] 首次启动自动导入必要种子数据。
- [ ] 重复启动幂等，不重复插入用户、分类、标签、课程。
- [ ] 初始化失败写入日志，并给启动器返回可理解的失败状态。

验收项：

- [ ] 删除本地 SQLite 文件后，启动程序可自动恢复可用数据库。
- [ ] 连续启动两次，数据数量不重复增长。
- [ ] 上传目录、日志目录、缓存目录自动创建。
- [ ] 后端测试覆盖初始化幂等行为。

## 4. Phase 3：前端生产包集成

目标：单机版不依赖 Vite 开发服务。

重点文件：

- [ ] `UI/package.json`
- [ ] `UI/vite.config.ts`
- [ ] 后续打包输出目录或静态服务配置。

实现要求：

- [ ] 使用 `npm run build` 生成生产静态文件。
- [ ] 启动器能访问生产前端页面。
- [ ] 前端 API 仍指向 `/api/v1`。
- [ ] 上传静态文件仍可通过 `/uploads` 或约定静态路径访问。

验收项：

- [ ] 不启动 `npm run dev` 也能访问页面。
- [ ] 登录、首页、课程详情、学习页可访问。
- [ ] 浏览器刷新页面不出现静态资源 404。

## 5. Phase 4：单机版启动器体验

目标：普通用户双击即可使用。

启动器职责：

- [ ] 设置单机版环境变量。
- [ ] 启动后端。
- [ ] 启动或承载前端静态服务。
- [ ] 等待健康检查。
- [ ] 自动打开浏览器。
- [ ] 后端异常时显示日志路径。

建议健康检查：

- [ ] `GET /`
- [ ] `GET /docs` 或后续专用 health endpoint。

验收项：

- [ ] 双击启动脚本即可进入系统。
- [ ] 用户不需要执行 `python scripts/init_db.py`。
- [ ] 用户不需要执行 `python scripts/seed_data.py`。
- [ ] 用户不需要打开数据库管理工具。

## 6. Phase 5：本地数据目录与备份策略

目标：单机版用户数据可保留、可备份、不会因程序更新丢失。

实现要求：

- [ ] 明确 SQLite 数据库文件位置。
- [ ] 明确上传文件位置。
- [ ] 明确缓存目录位置。
- [ ] 明确日志目录位置。
- [ ] 卸载或更新时默认不删除用户数据。

可选增强：

- [ ] 提供“打开数据目录”入口。
- [ ] 提供“备份数据”说明或脚本。
- [ ] 提供“恢复数据”说明。

## 7. Phase 6：安装包

目标：从启动脚本过渡到可交付安装软件。

可选工具：

- [ ] Inno Setup。
- [ ] NSIS。
- [ ] 压缩包 + 启动器作为第一版轻量交付。

安装器职责：

- [ ] 安装程序文件。
- [ ] 创建桌面快捷方式。
- [ ] 写入默认配置。
- [ ] 提供卸载入口。
- [ ] 卸载时默认保留用户数据。

## 8. 单机版验证命令

后端定向验证：

```bash
project_code/.venv/bin/python -m pytest project_code/backend/tests/test_runtime_config.py -q
```

前端构建验证：

```bash
cd UI
npm run build
```

联调验证：

- [ ] 使用 `admin1 / Admin123456` 登录。
- [ ] 使用 `student1 / Test123456` 登录。
- [ ] 首页课程列表可打开。
- [ ] 课程详情可打开。
- [ ] 学习页可打开。
- [ ] 重启后数据仍存在。

## 9. 禁止项

单机版分支禁止做：

- [ ] 课堂版 50 人承载优化。
- [ ] 局域网访问地址面板。
- [ ] 课堂版视频分发策略。
- [ ] 课堂版学习进度节流专项。
- [ ] 公网部署能力。
- [ ] 集群部署能力。
- [ ] 把视频文件放进 `diskcache`。
