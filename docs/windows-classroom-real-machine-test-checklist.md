# Windows 局域网课堂版实机与规模验证清单

> 更新时间：2026-05-18  
> 目标分支：`future/windows-classroom`  
> 目标：验证课堂版 zip + launcher 在真实 Windows 局域网环境中可启动、可访问、可播放视频，并完成 50 人基础验收与 70 路视频并发目标验收。

验收口径：

- 50 人是基础验收目标。
- 70 路视频并发是目标验收：尽力达到，未达到时记录明确瓶颈。
- 默认主机是普通办公电脑或教师笔记本。
- 默认视频是普通 720p / 1080p 低中码率 MP4。
- `/uploads/...` 静态文件不做文件级鉴权，权限控制放在业务入口和资源元数据访问链路。

## 1. 测试环境记录

请先记录：

- Windows 版本：
- 是否真机 / 虚拟机：
- 主机 CPU：
- 主机内存：
- 磁盘类型：机械硬盘 / SATA SSD / NVMe SSD
- 网卡速率：百兆 / 千兆 / Wi-Fi 5 / Wi-Fi 6 / 其他
- 主机 IP：
- 项目所在路径：
- 路径是否包含中文或空格：
- 测试日期：
- 测试人：

建议至少覆盖：

- 普通路径：`D:\learning-platform`
- 含空格路径：`D:\Test Folder\learning-platform`
- 有线局域网优先，其次 Wi-Fi；如果使用 Wi-Fi，请记录路由器型号和频段。

## 2. 交付包完整性检查

必须存在：

- `start-windows-classroom.cmd`
- `config\windows-classroom.env`
- `project_code\.venv\Scripts\python.exe` 或等价后端运行环境
- `UI\dist\index.html`，或 `UI\package.json` + 可用 npm 构建环境

配置文件必须包含：

```env
APP_EDITION=windows_classroom
HOST=0.0.0.0
PORT=8000
CACHE_BACKEND=auto
SQLITE_BUSY_TIMEOUT_MS=30000
```

预期：

- 不要求用户安装 MySQL。
- 不要求用户安装 Redis。
- 不要求用户手动执行数据库初始化命令。
- 当前阶段按 `zip + launcher` 验证，不要求完整安装器。

## 3. 首次启动测试

操作：

1. 确认端口 `8000` 未被占用。
2. 双击运行 `start-windows-classroom.cmd`。
3. 记录控制台输出的本机 URL 和局域网 URL。
4. 等待浏览器打开本机 URL。

预期：

- 控制台窗口不闪退。
- 启动失败时显示错误原因和日志路径。
- 后端健康检查通过后才提示启动成功。
- 本机 URL 类似：`http://127.0.0.1:8000/`
- 局域网 URL 类似：`http://192.168.x.x:8000/`
- 自动生成或确认存在：
  - `project_code\backend\data\windows-classroom.db`
  - `project_code\backend\data\cache\`
  - `project_code\backend\logs\`
  - `project_code\backend\uploads\`

失败时收集：

- 控制台截图
- `project_code\backend\logs\windows-classroom-startup.log`
- `project_code\backend\logs\windows-classroom-startup-error.log`
- 浏览器 Console / Network 截图

## 4. 局域网访问测试

操作：

1. 在 Windows 主机本机打开本机 URL。
2. 在同一局域网另一台设备打开局域网 URL。
3. 如果无法访问，临时关闭或放行 Windows 防火墙端口 `8000` 后重试。

预期：

- 本机可访问课堂版前端页面。
- 局域网设备可访问课堂版前端页面。
- 刷新 `/courses`、`/profile`、`/learn/...` 等前端路由不返回后端 404。
- 未命中的 `/api/...` 和 `/uploads/...` 仍返回真实 404，不应返回前端首页。

## 5. SQLite WAL 与 busy_timeout 检查

WAL 是数据库文件级状态，可在 Windows 主机上运行：

```cmd
project_code\.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect(r'project_code\backend\data\windows-classroom.db'); print('journal_mode=', c.execute('PRAGMA journal_mode').fetchone()[0]); c.close()"
```

预期：

- `journal_mode= wal`

如果不是 WAL：

- 收集启动日志。
- 确认启动时确实加载了 `APP_EDITION=windows_classroom`。
- 确认数据库文件不是旧包遗留文件。

`busy_timeout` 是连接级设置，不会持久写入数据库文件。请通过以下方式验证：

- 启动日志中出现 `SQLite busy_timeout=30000ms` 或等价信息。
- 后端聚焦测试通过：`project_code\.venv\Scripts\python.exe -m pytest project_code\backend\tests\test_runtime_config.py -q`
- 如果后续补并发写入测试，以“无持续 database locked”为最终验收口径。

## 6. 登录与核心流程冒烟

使用种子账号：

| 角色 | 用户名 | 密码 | 预期 |
|---|---|---|---|
| 管理员 | `admin1` | `Admin123456` | 可进入管理页面 |
| 教师 | `teacher1` | `Test123456` | 可进入教师课程管理页面 |
| 学生 | `student1` | `Test123456` | 可进入课程学习页面 |

检查：

- 登录成功后不白屏。
- 刷新页面后登录态正常。
- 不同角色菜单和权限大致正确。
- 学生可打开课程详情和学习页。
- 教师可查看课程列表和编辑页。
- 管理员可打开用户、分类、标签、公告、反馈等管理页。

## 7. 视频 Range 与拖动播放测试

准备一个课堂测试视频，建议记录：

- 文件名：
- 文件大小：
- 视频时长：
- 平均码率：
- 分辨率：

Range 命令：

```cmd
curl -I -H "Range: bytes=0-1023" http://127.0.0.1:8000/uploads/<video-path>
```

预期：

- 状态码为 `206 Partial Content`。
- 响应头包含 `Content-Range`。
- 响应头包含 `Accept-Ranges: bytes`。

浏览器操作：

1. 学生账号打开学习页。
2. 播放视频。
3. 拖动到视频中间。
4. 拖动到接近结尾。
5. 刷新页面后再次进入学习页。

预期：

- 视频可播放。
- 拖动后可继续播放。
- DevTools Network 能看到视频请求走 `/uploads/...`。
- 视频请求不走 `/api/v1/...`。
- 缓存目录中不出现视频原文件副本。

## 8. 学习进度节流验证

操作：

1. 学生账号播放视频 2 分钟。
2. 打开浏览器 Network 面板，过滤 `learning/progress`。
3. 暂停视频。
4. 切换到另一个资源。
5. 关闭或刷新学习页。

预期：

- 播放中不会每秒请求一次进度保存接口。
- 播放中按约 10～30 秒间隔同步。
- 暂停、切换资源、离开页面时尽量保存。
- 后端日志没有持续出现 `database locked`。

## 9. 50 人基础验收

目标：证明课堂版能支撑至少 50 人轻量课堂可用。

建议组织方式：

- 真实设备优先；设备不足时，可用多浏览器窗口补充，但必须记录真实设备数量。
- 参与者都连接同一局域网。
- 50 人同时打开首页、课程详情、学习页。
- 至少 20 人同时播放视频，其余人员浏览课程或切换资源。

观察指标：

- Windows 主机 CPU：
- Windows 主机内存：
- 磁盘读取：
- 网络上行：
- 后端错误日志：
- 浏览器白屏 / 卡死数量：
- `database locked` 是否持续出现：

通过标准：

- 首页、课程详情、学习页能正常打开。
- 大部分用户视频可正常播放和拖动。
- 学习进度保存没有持续失败。
- 没有持续增长的 `database locked`。
- 没有明显后端崩溃或启动窗口退出。

## 10. 70 路视频并发目标验收

目标：尽力验证 70 路视频并发；如果未达成，必须定位瓶颈。

测试前记录：

- 视频文件大小：
- 视频码率：
- 视频分辨率：
- 视频格式：MP4 / 其他
- 磁盘类型：
- 网卡速率：
- 局域网类型：
- 真实设备数量：
- 浏览器实例数量：

建议分档推进：

| 档位 | 操作 | 通过后再继续 |
|---|---|---|
| 20 路 | 同时播放同一视频并拖动 | 是 |
| 40 路 | 同时播放同一视频并拖动 | 是 |
| 50 路 | 同时播放同一视频并拖动 | 是 |
| 70 路 | 同时播放同一视频并拖动 | 目标验收 |

每档记录：

- 实际并发路数：
- 视频是否可播放：
- 拖动后是否可继续播放：
- 平均首屏加载时间：
- Windows CPU / 内存 / 磁盘 / 网络：
- 后端错误日志：
- 失败设备数量：
- 失败表现：

未达 70 路时，按顺序判断瓶颈：

1. 网络上行是否打满。
2. 磁盘读取是否打满。
3. 视频码率是否过高。
4. CPU 是否异常升高。
5. 是否出现 SQLite 写入压力或 `database locked`。

结论必须写清楚：通过 / 未达到目标但基础验收通过 / 未通过 / 达到多少路 / 主要瓶颈。

## 11. 重启与数据保留测试

操作：

1. 登录并完成一次课程学习。
2. 上传或确认一个课程资源可访问。
3. 关闭启动窗口或后端进程。
4. 再次双击 `start-windows-classroom.cmd`。
5. 重新登录并访问原课程、学习页、上传资源。

预期：

- 数据库文件保留。
- 上传文件保留。
- 学习进度保留。
- 重复启动不会重复导入种子数据导致重复账号。
- 日志继续写入。

## 12. 端口占用与异常场景

端口占用：

1. 保持第一次启动运行。
2. 再次双击 `start-windows-classroom.cmd`。

预期：

- 提示端口 `8000` 被占用。
- 显示占用 PID。
- 窗口不闪退。

缺配置文件：

1. 临时改名 `config\windows-classroom.env`。
2. 运行启动器。

预期：

- 明确提示缺少配置文件。
- 窗口不闪退。
- 写入错误日志。

缺虚拟环境：

1. 临时改名 `project_code\.venv`。
2. 运行启动器。

预期：

- 明确提示 Python virtual environment not found。
- 窗口不闪退。
- 写入错误日志。

## 13. 测试结论模板

测试环境：

- Windows 版本：
- 主机配置：
- 磁盘类型：
- 网卡 / 局域网：
- 项目路径：
- 是否含空格 / 中文：
- 测试人：
- 测试时间：

结论：

- 首次启动：通过 / 不通过
- LAN 访问：通过 / 不通过
- SQLite WAL：通过 / 不通过
- busy_timeout：通过 / 不通过
- 登录验证：通过 / 不通过
- 学习页：通过 / 不通过
- Range / 206：通过 / 不通过
- 视频拖动：通过 / 不通过
- 学习进度节流：通过 / 不通过
- 50 人基础验收：通过 / 不通过 / 未测
- 70 路视频并发：通过 / 不通过 / 达到多少路 / 未测
- 重启数据保留：通过 / 不通过
- 端口占用提示：通过 / 不通过

问题记录：

1. 问题现象：
   操作步骤：
   预期结果：
   实际结果：
   截图/日志：
   是否可复现：
   影响范围：
   初步判断瓶颈：

2. 问题现象：
   操作步骤：
   预期结果：
   实际结果：
   截图/日志：
   是否可复现：
   影响范围：
   初步判断瓶颈：

必须回传：

- 控制台截图
- `project_code\backend\logs\windows-classroom-startup.log`
- `project_code\backend\logs\windows-classroom-startup-error.log`
- 后端运行日志
- 浏览器 Console / Network 截图
- Range 请求截图或命令输出
- 50 人 / 70 路测试记录表
