# Windows 部署与版本实施文档索引

> 更新时间：2026-05-13  
> 适用范围：Windows 单机版、Windows 局域网课堂版、共享 Windows 基础层。

## 1. 先读哪份文档

如果你要快速判断读哪份文档：

| 目标 | 优先阅读 |
|---|---|
| 了解当前项目总体架构 | [`current-architecture.md`](./current-architecture.md) |
| 了解 Windows 单机版目标、边界、配置和验收 | [`windows-local-implementation-details.md`](./windows-local-implementation-details.md) |
| 直接推进 Windows 单机版开发 | [`windows-local-development-checklist.md`](./windows-local-development-checklist.md) |
| 安排 Windows 单机版真实环境测试 | [`windows-local-real-machine-test-checklist.md`](./windows-local-real-machine-test-checklist.md) |
| 了解 Windows 局域网课堂版目标、边界、配置和验收 | [`windows-classroom-implementation-details.md`](./windows-classroom-implementation-details.md) |
| 直接推进 Windows 局域网课堂版开发 | [`windows-classroom-development-checklist.md`](./windows-classroom-development-checklist.md) |
| 落地 Windows 局域网课堂版视频与静态分发 | [`windows-classroom-video-delivery-plan.md`](./windows-classroom-video-delivery-plan.md) |
| 安排 Windows 局域网课堂版真实环境和规模验证 | [`windows-classroom-real-machine-test-checklist.md`](./windows-classroom-real-machine-test-checklist.md) |
| 在 Windows 主机快速做课堂版连通性和 Range 自检 | [`verify-windows-classroom.ps1`](../verify-windows-classroom.ps1) |
| 确认开发时应该在哪个分支 | [`.trellis/spec/backend/runtime-editions.md`](../.trellis/spec/backend/runtime-editions.md) |

推荐阅读顺序：先读本索引确认版本和分支，再读对应版本的实施细则，随后按开发任务清单推进；单机版实机测试看 `windows-local-real-machine-test-checklist.md`，课堂版实机与规模验证看 `windows-classroom-real-machine-test-checklist.md`。

## 2. 分支与版本对应关系

Windows 相关开发必须先确认当前分支：

```bash
git branch --show-current
```

版本与分支对应关系：

| 分支 | 用途 | 可以做 | 不应该做 |
|---|---|---|---|
| `future/windows-base` | Windows 共享基础层 | `APP_EDITION`、SQLite/diskcache 抽象、目录初始化、共同测试 | 单机版启动器、课堂版 LAN/视频专项 |
| `future/windows-local` | Windows 单机版 | 本机启动、自动初始化、浏览器自动打开、安装包体验 | 50 人课堂承载、LAN 地址展示、课堂视频优化 |
| `future/windows-classroom` | Windows 局域网课堂版 | LAN 访问、课堂启动器、进度节流、视频/静态分发优化 | localhost-only 单机假设、个人安装器专属体验 |

如果发现某项能力两个 Windows 版本都需要，先回到 `future/windows-base` 做共享实现，再合并到两个版本分支。

## 3. 当前已完成内容

当前 `future/windows-base` 已完成第一阶段后端基础层：

- `APP_EDITION` / `app_edition` 运行形态。
- 支持 `development`、`windows_local`、`windows_classroom`、`server`。
- Windows 版本默认 SQLite 文件数据库。
- Windows 版本默认 `diskcache`。
- server 版默认 Redis 后端。
- 开发环境默认内存缓存。
- 启动时自动创建运行目录。
- SQLite 文件库连接 `timeout`。
- SQLite `busy_timeout` 初始化。
- `windows_classroom` 预留并接入 WAL 初始化。
- 运行配置与缓存抽象测试已通过。

验证命令：

```bash
project_code/.venv/bin/python -m pytest project_code/backend/tests/test_runtime_config.py -q
```

当前结果：

```text
20 passed, 1 warning
```

## 4. Windows 单机版推进顺序

目标分支：

```bash
git switch future/windows-local
```

推荐推进顺序：

1. 单机版配置文件与启动环境。
2. 自动初始化闭环。
3. 前端生产包集成。
4. 单机版启动器体验。
5. 本地数据目录与备份策略。
6. 安装包。

详细任务见：[`windows-local-development-checklist.md`](./windows-local-development-checklist.md)。

## 5. Windows 局域网课堂版推进顺序

目标分支：

```bash
git switch future/windows-classroom
```

推荐推进顺序：

1. 课堂版配置文件与启动环境。
2. LAN 访问地址展示。
3. SQLite 课堂运行验证。
4. 学习进度写入节流。
5. 视频与静态资源分发。
6. 课堂规模验证。

详细任务见：[`windows-classroom-development-checklist.md`](./windows-classroom-development-checklist.md)。

## 6. 与 Linux 服务器版的边界

Windows 单机版和 Windows 局域网课堂版不替代 Linux 服务器版。

Linux 服务器版继续保留：

- MySQL。
- Redis。
- Nginx 或正式静态服务。
- Docker/Compose 或系统服务化部署。
- 后续集群扩容空间。

Windows 版不应引入会破坏服务器版的硬编码逻辑。任何涉及数据库、缓存、静态资源路径的改动，都应通过 `APP_EDITION` 或配置分流。

## 7. 关键禁止项

Windows 相关开发中禁止：

- 在 `master` 上直接做 Windows 版本开发。
- 在 `future/windows-local` 中实现课堂版 LAN/50 人专项能力。
- 在 `future/windows-classroom` 中实现只适合个人本机的 localhost-only 假设。
- 把视频文件、大课件、大图片原文件放进 `diskcache`。
- 要求 Windows 普通用户手动执行数据库初始化命令。
- 要求 Windows 普通用户安装或管理 MySQL/Redis。
- 为 Windows 改动破坏 Linux 服务器版 MySQL/Redis 路线。

## 8. 验收总览

### Windows 单机版

- 普通用户不需要安装 MySQL/Redis。
- 普通用户不需要执行数据库初始化命令。
- 双击启动后可打开页面。
- 首次启动自动建库、建表、初始化必要数据。
- 重复启动不破坏已有数据。
- 核心登录、课程、学习、上传流程可用。

### Windows 局域网课堂版

- 一台 Windows 主机可作为局域网服务端。
- 同一局域网其他设备可访问。
- 视频可播放并支持拖动。
- 学习进度不会每秒高频写库。
- 至少 50 人轻量课堂使用时不出现明显数据库写爆问题。
- 尽力验证 70 路视频并发；未达成时记录瓶颈。

### Linux 服务器版

- MySQL + Redis 路线保持可用。
- 可继续面向正式在线部署和后续集群扩容。
