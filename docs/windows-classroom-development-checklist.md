# Windows 局域网课堂版开发任务清单

> 更新时间：2026-05-13  
> 目标分支：`future/windows-classroom`  
> 依赖基础分支：`future/windows-base`  
> 详细设计：[`windows-classroom-implementation-details.md`](./windows-classroom-implementation-details.md)

## 0. 开发前检查

开始任何课堂版专属改动前必须确认：

```bash
git branch --show-current
```

必须位于：

```text
future/windows-classroom
```

如果当前在 `future/windows-base`，只能做共享基础层；如果当前在 `future/windows-local`，不能做课堂版专属改动。

## 1. 当前已完成基础

这些已在 `future/windows-base` 完成，课堂版分支应继承：

- [x] `APP_EDITION` / `app_edition` 运行形态。
- [x] `windows_classroom` 配置值。
- [x] Windows 版默认 SQLite 文件数据库。
- [x] Windows 版默认 `diskcache`。
- [x] 启动时创建运行目录。
- [x] SQLite 文件库连接 `timeout`。
- [x] SQLite `busy_timeout` 初始化。
- [x] 课堂版 WAL 初始化入口。
- [x] 运行配置与缓存抽象测试。

## 2. Phase 1：课堂版配置文件与启动环境

目标：提供课堂版默认环境配置，支持局域网访问。

建议文件：

- [ ] `config/windows-classroom.env`
- [ ] `start-windows-classroom.cmd`
- [ ] 如需跨平台辅助，可新增 LAN IP 检测脚本。

配置要求：

```env
APP_EDITION=windows_classroom
HOST=0.0.0.0
PORT=8000
CACHE_BACKEND=auto
SQLITE_BUSY_TIMEOUT_MS=30000
```

验收项：

- [ ] 启动脚本能设置 `APP_EDITION=windows_classroom`。
- [ ] 后端监听局域网可访问地址。
- [ ] 不要求用户手动输入数据库连接串。
- [ ] 不要求用户启动 Redis。
- [ ] 不要求用户启动 MySQL。
- [ ] 启动失败时窗口不直接关闭，并提示日志位置。

## 3. Phase 2：LAN 访问地址展示

目标：教师/管理员启动后知道让学生访问哪个地址。

实现要求：

- [ ] 获取本机局域网 IP。
- [ ] 显示本机地址：`http://127.0.0.1:<port>`。
- [ ] 显示局域网地址：`http://<lan-ip>:<port>`。
- [ ] 提示学生需要连接同一局域网。
- [ ] 提示防火墙可能需要放行应用端口。

显示示例：

```text
学习平台课堂版已启动
本机访问：http://127.0.0.1:8000
局域网访问：http://192.168.1.23:8000
```

验收项：

- [ ] Windows 主机本机可访问。
- [ ] 同一局域网另一台设备可访问。
- [ ] IP 获取失败时有清晰提示，不静默失败。

## 4. Phase 3：SQLite 课堂运行验证

目标：确认课堂版 SQLite WAL 和超时配置实际生效。

重点文件：

- [ ] `project_code/backend/app/core/runtime.py`
- [ ] `project_code/backend/app/config.py`
- [ ] `project_code/backend/tests/test_runtime_config.py`

验收项：

- [ ] `APP_EDITION=windows_classroom` 时启用 SQLite 文件库。
- [ ] `PRAGMA journal_mode=WAL` 生效。
- [ ] `PRAGMA busy_timeout` 生效。
- [ ] 并发读写场景不会轻易触发 database locked。
- [ ] 测试覆盖 classroom 与 local 差异。

## 5. Phase 4：学习进度写入节流

目标：避免 10～50 人课堂中因学习进度高频写入拖垮 SQLite。

重点文件：

- [ ] `UI/src/composables/useProgressSync.ts`
- [ ] `UI/src/store/learn.ts`
- [ ] `UI/src/api/learning.ts`
- [ ] `project_code/backend/app/api/v1/learning.py`
- [ ] `project_code/backend/app/services/learning_service.py`
- [ ] `project_code/backend/tests/test_learning.py`

实现要求：

- [ ] 播放中按 10～30 秒间隔同步。
- [ ] 暂停时立即同步。
- [ ] 切换资源时同步。
- [ ] 页面退出或可捕获关闭事件时尽量同步。
- [ ] 不允许每秒写一次学习进度。

验收项：

- [ ] 前端不会按秒调用学习进度保存接口。
- [ ] 暂停和切换资源仍能保存进度。
- [ ] 后端能处理短时间重复提交，不造成异常。
- [ ] 测试覆盖节流后的核心保存语义。

## 6. Phase 5：视频与静态资源分发

目标：课堂版视频可播放、可拖动，不让 FastAPI 业务接口整文件转发视频。

重点文件：

- [ ] `project_code/backend/app/main.py`
- [ ] 上传/资源相关服务。
- [ ] 未来静态文件服务或反向代理配置。
- [ ] `UI/src/views/learn/LearningPage.vue`
- [ ] `UI/src/api/learning.ts`

实现要求：

- [ ] 视频资源支持 HTTP Range。
- [ ] 视频可拖动进度。
- [ ] 大文件不进入 `diskcache`。
- [ ] Python 不整文件读入内存再返回。
- [ ] JS/CSS/hash 静态资源可长期缓存。

验收项：

- [ ] 浏览器 DevTools 中视频请求返回 `206 Partial Content` 或等价 Range 支持行为。
- [ ] 拖动视频进度可继续播放。
- [ ] 多浏览器访问同一视频无明显后端异常。
- [ ] 缓存目录中不出现视频原文件副本。

## 7. Phase 6：课堂规模验证

目标：验证 10～50 人局域网使用边界。

验证项：

- [ ] 10 人同时访问首页。
- [ ] 10 人同时打开课程详情。
- [ ] 10 人同时播放视频。
- [ ] 多用户同时保存学习进度。
- [ ] 逐步扩展到 30～50 人轻量验证。

观察指标：

- [ ] Windows 主机 CPU。
- [ ] Windows 主机内存。
- [ ] 磁盘读取。
- [ ] 局域网带宽。
- [ ] 后端错误日志。
- [ ] SQLite database locked 相关错误。

验收项：

- [ ] 10～50 人轻量课堂使用时无明显数据库写爆问题。
- [ ] 视频播放瓶颈能被定位为网络/磁盘/静态服务，而不是业务缓存。
- [ ] 学习进度不会高频写库。

## 8. 课堂版验证命令

后端定向验证：

```bash
project_code/.venv/bin/python -m pytest project_code/backend/tests/test_runtime_config.py -q
```

学习模块验证：

```bash
project_code/.venv/bin/python -m pytest project_code/backend/tests/test_learning.py -q
```

前端构建验证：

```bash
cd UI
npm run build
```

联调验证：

- [ ] Windows 主机本机访问。
- [ ] 局域网另一台设备访问。
- [ ] 使用 `teacher1 / Test123456` 登录。
- [ ] 使用 `student1 / Test123456` 登录。
- [ ] 打开课程详情。
- [ ] 打开学习页。
- [ ] 播放视频并拖动。
- [ ] 多用户保存学习进度。

## 9. 禁止项

课堂版分支禁止做：

- [ ] 单机版 localhost-only 启动假设。
- [ ] 只面向个人本机使用的安装器体验。
- [ ] 公网部署承诺。
- [ ] 100 人视频并发承诺。
- [ ] 集群部署能力。
- [ ] 把视频文件放进 `diskcache`。
- [ ] 用 FastAPI 业务接口整文件承载视频流量。
