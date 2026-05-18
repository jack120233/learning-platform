# Windows 课堂版视频与静态资源分发实施方案

> 更新时间：2026-05-13  
> 目标分支：`future/windows-classroom`  
> 容量目标：至少 50 人课堂可用，目标 70 路视频并发尽力达到  
> 关联文档：[`windows-classroom-implementation-details.md`](./windows-classroom-implementation-details.md)、[`windows-classroom-development-checklist.md`](./windows-classroom-development-checklist.md)

## 1. 文档定位

本方案在课堂版实施细则之上，把“视频如何走 Range、上传媒体如何走静态、前端构建产物如何缓存、FastAPI 业务接口走什么”这件事写到可落地的颗粒度。

只用于 `windows_classroom`，不适用于单机版和 Linux 服务器版。

## 2. 现状评估

当前后端已经具备：

- `/uploads` 通过 `StaticFiles(directory=settings.resolved_upload_dir)` 挂载。
- Windows 版本下 `/assets` 通过 `StaticFiles(directory=frontend_dist_dir/"assets")` 挂载。
- 上传服务通过 `upload_service` 落盘到本地目录，生成 `/uploads/...` URL。
- FastAPI 业务接口不直接读取视频文件内容。

Starlette `StaticFiles` 默认会返回 `Accept-Ranges: bytes`，并对带 `Range` 请求返回 `206 Partial Content`。因此课堂版视频分发的基础已经存在，本方案重点是**确认、约束、验证、不再倒退**，而不是从零搭一套新的静态服务。

## 3. 实施目标

- 视频资源能够通过浏览器原生 `<video>` 拖动播放。
- 视频请求按需返回 `206 Partial Content`。
- 视频原文件不进入 `diskcache`。
- 课堂版下首页/课程/学习页相关 API 仍走 `/api/v1`，不掺杂大文件流量。
- 视频在并发场景下的瓶颈可被定位为磁盘、网卡、文件大小或视频码率，而不是业务层。
- 默认视频规格按普通 720p / 1080p 低中码率 MP4 设计。
- 默认硬件按普通办公电脑或教师笔记本设计，不假设专用服务器。

## 4. 分发路径约束

课堂版下，资源类型与分发路径必须按下表对齐：

| 资源类型 | 分发路径 | 承载方式 | 是否进缓存 |
| --- | --- | --- | --- |
| 课程视频 | `/uploads/...` | `StaticFiles` Range 响应 | 不进 `diskcache` |
| 课件 / 大图片 / 大资源原文件 | `/uploads/...` | `StaticFiles` Range 响应 | 不进 `diskcache` |
| 课程封面 / 头像 / 反馈图片等小图片 | `/uploads/...` | `StaticFiles` | 不进 `diskcache` |
| 前端构建 JS/CSS | `/assets/...` | `StaticFiles` + 文件名 hash | 浏览器长期缓存 |
| 业务 API | `/api/v1/...` | FastAPI 路由 | 元数据可进 `diskcache` |
| 业务元数据（课程列表 / 公告 / 分类） | `/api/v1/...` | FastAPI 路由 | 可进 `diskcache` |

禁止：

- 通过 `/api/v1/...` 业务接口整文件读取并返回视频。
- 把视频或大文件的二进制内容写入 `diskcache`。
- 用 Python 把整个视频读进内存再 `return`。
- 前端用 `fetch` 拉全量视频内容到内存里再交给 `<video>`。

鉴权边界：

- `/uploads/...` 静态文件不做文件级鉴权。
- 课程、章节、资源元数据、学习页入口仍必须经过登录态和业务权限控制。
- 如果未来要求视频 URL 本身也鉴权，需要另起阶段评估受控静态文件或签名 URL，不混入当前课堂版第一阶段。

## 5. 验证 Range 是否生效

课堂版上线视频分发前，必须验证：

```bash
curl -I -H "Range: bytes=0-1023" http://127.0.0.1:8000/uploads/<some-video.mp4>
```

预期返回：

- 状态码：`206 Partial Content`
- 包含 `Content-Range: bytes 0-1023/<total>`
- 包含 `Accept-Ranges: bytes`

如果返回 `200 OK` 且没有 `Content-Range`，说明：

- 该路径不是 `StaticFiles` 提供
- 或者中间被自定义路由覆盖
- 或者被反向代理改写

任一情况都必须先修复，再继续视频并发验证。

## 6. 后端实施细则

### 6.1 不要把视频接入业务路由

`project_code/backend/app/api/v1/*` 中的接口只返回：

- JSON 业务数据
- 元数据中包含 `/uploads/...` URL 字符串

不应出现：

- `FileResponse(video_file)`
- `StreamingResponse(open(video_file, "rb"), ...)`
- 任何把 `with open(video_file) as f: f.read()` 后 `return` 的写法

### 6.2 保持 `/uploads` 默认 `StaticFiles`

`project_code/backend/app/main.py` 中：

```python
app.mount(
    settings.upload_url_prefix,
    StaticFiles(directory=settings.resolved_upload_dir),
    name="uploads",
)
```

不要替换成自定义 Range 实现，除非证明 `StaticFiles` 在课堂版下不满足要求。任何替换必须保留：

- `Accept-Ranges: bytes`
- 对 `Range` 请求返回 `206`
- 默认 MIME 推断
- 默认 `Last-Modified` / `ETag` 行为

### 6.3 上传仍走业务接口，但落盘后只用静态路径访问

`upload_service` 的现有行为已经满足要求：

- 上传写盘后返回 `/uploads/<subdir>/<filename>` 形式的 URL
- 前端通过该 URL 直接走静态访问

不需要为课堂版再补另一层包装。

### 6.4 不要把视频元数据相关查询变成大请求

业务接口中：

- 课程详情、章节列表、小节列表只返回元数据
- 不要把视频时长、视频文件大小、视频码率等信息合在一起一次性返回过多字段

如果未来需要展示视频时长，可以在上传阶段记录并落库，避免每次请求重新读文件头。

## 7. 前端实施细则

### 7.1 视频元素

学习页：

- `UI/src/views/learn/LearningPage.vue`
- `UI/src/api/learning.ts`

要求：

- 使用原生 `<video>` 元素或基于原生 `<video>` 的库
- `src` 指向 `/uploads/...` 形式的 URL
- 不要用 `fetch` / `axios` 把视频拉成 Blob 再喂给 `<video>`
- 不要在前端缓存视频 Blob

### 7.2 资源 URL 来源

- 资源 URL 必须从后端业务接口返回的元数据中取
- 不要在前端拼接业务 ID 直接猜路径
- 不要把视频 URL 通过 `localStorage` 长期缓存（缓存元数据即可）

### 7.3 静态资源缓存

- 前端构建产物保持文件名 hash
- 浏览器侧自然走长期缓存
- 课堂版不需要为前端构建产物额外加 Service Worker

## 8. 缓存层约束

`project_code/backend/app/core/cache.py`：

- 允许缓存：
  - 课程列表元数据
  - 课程详情元数据
  - 分类、标签、公告
  - 权限码、角色权限
- 禁止缓存：
  - 视频字节
  - 大图片字节
  - 大课件字节
  - 任何 `bytes` 类型的文件原始内容

代码侧约束：

- 不要把 `open(path, "rb").read()` 的结果通过 `cache_set` 写入 `diskcache`
- 不要把 `FileResponse` 内部内容序列化进缓存
- 不要把上传请求的原始文件流缓存

## 9. 并发与瓶颈定位

70 路视频并发是目标验收，按尽力达到处理；未达到时必须记录瓶颈，不直接把 50 人基础课堂能力判为不可用。

瓶颈优先级：

1. 网卡上行带宽（千兆 vs 百兆）
2. 磁盘连续读取速度（机械 vs SSD）
3. 视频码率与文件大小
4. Windows 主机 CPU（少量影响）
5. SQLite 学习进度写入（间接影响）

实施时必须做到：

- 视频文件大小、码率、磁盘类型、网卡速率有记录
- 课堂版规模验证时可以按指标定位失败原因
- 在视频并发未达 70 时，能在文档中说明是哪一项瓶颈

不要做的事情：

- 把 70 路视频并发失败的原因归结为 `diskcache` 或业务接口
- 在没有定位瓶颈的情况下，盲目改造 FastAPI 视频路由

## 10. 测试与验收

### 10.1 Range 基础测试

- 启动课堂版后端
- `curl -I -H "Range: bytes=0-1023" http://127.0.0.1:8000/uploads/<video>` 返回 `206`
- 浏览器 DevTools 中视频请求 `Status: 206`，`Content-Range` 存在

### 10.2 拖动播放测试

- 在学习页打开任意带视频的小节
- 拖动进度条到中间和末尾
- 视频可继续播放
- DevTools Network 中看到分段 `Range` 请求

### 10.3 多端并发测试

- 至少 10 个浏览器实例同时播放同一视频
- 后端日志没有 `database locked` 或大文件内存异常
- 缓存目录中没有出现视频原文件副本

### 10.4 50 人 / 70 路目标验证

- 50 人课堂级使用：作为基础验收
- 70 路视频并发：作为目标验收，尽力达到；未达成时记录瓶颈
- 记录文件：参与人数、视频码率、文件大小、磁盘类型、网卡速率、实际结果
- 具体执行步骤见：[`windows-classroom-real-machine-test-checklist.md`](./windows-classroom-real-machine-test-checklist.md)

## 11. 明确不做

课堂版第一阶段不做：

- HLS / DASH 切片
- 视频转码
- 视频鉴权令牌（保持 `/uploads/...` 通过登录态约束业务流，不做单独 URL 签名）
- 反向代理引入（Nginx 等放在后续 Linux 服务器版阶段）
- 自研 Range 实现（除非证明 `StaticFiles` 不满足）

如果未来需要这些能力，应作为独立阶段方案，不混进当前实施。
