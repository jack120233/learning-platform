# 当前项目技术架构文档

> 更新时间：2026-05-11  
> 范围：根工作区、`UI` 前端、`project_code/backend` 后端、前后端联调约定。

## 1. 文档目的与资料可信度

与 Windows 部署相关的进一步实施细则请优先参考：

- [Windows 部署与版本实施文档索引](./windows-deployment-index.md)
- [Windows 单机版实施细则](./windows-local-implementation-details.md)
- [Windows 单机版开发任务清单](./windows-local-development-checklist.md)
- [Windows 局域网课堂版实施细则](./windows-classroom-implementation-details.md)
- [Windows 局域网课堂版开发任务清单](./windows-classroom-development-checklist.md)

如果你要查 Windows 相关资料，优先从“Windows 部署与版本实施文档索引”进入；如果你要直接推进实现，优先阅读对应版本的“开发任务清单”；如果你要确认边界和验收，优先阅读对应版本的“实施细则”。

这两份细则和根级分支约束一起使用：`future/windows-base` 只放共享基础层，`future/windows-local` 只放单机版专属改动，`future/windows-classroom` 只放课堂版专属改动。


本文档用于梳理当前项目实际开发逻辑、功能模块和联调口径，作为后续开发、排查和验收的当前技术入口。

项目历史上已有多份前端、后端和接口文档，但部分内容已经落后于当前代码。阅读资料时按以下优先级判断：

1. **当前代码优先**：`UI/src/**`、`project_code/backend/app/**`、`project_code/backend/tests/**` 是最终事实来源。
2. **当前协作规则优先**：根 `CLAUDE.md`、`UI/CLAUDE.md`、`project_code/CLAUDE.md` 记录当前目录路由、开发命令、统一口径和验证要求。
3. **接口清单需复核**：`project_code/docs/api-endpoint-inventory.md` 是较完整的后端接口索引，但接口总数统计存在不一致，引用精确数量前应重新核对代码。
4. **旧文档只作历史参考**：早期接口文档、架构设计文档、差异对照文档可以帮助理解演进背景，但不能直接作为当前实现依据。

常见过期点包括：

- 登录字段旧文档可能写 `login_id`，当前前端登录请求字段为 `username`。
- 课程 ID 曾经有 `id` / `course_id` 差异，当前前端在部分 API/store 中做兼容映射。
- 旧文档中的接口数量、模块数量少于当前实现，尤其缺少上传、权限、消息等后续扩展；部分消费型文档还保留了过期的统计口径。
- 前端认证状态必须以 `UI/src/store/user.ts` 为单一来源，不应让业务组件直接读写登录态 localStorage。

## 2. 工作区总览

当前仓库是一个在线学习平台联合开发工作区，由两个已经独立演进过的子项目组成：

```text
learning-platform/
├── UI/                       # Vue 3 + TypeScript + Vite 前端
├── project_code/backend/     # FastAPI + SQLAlchemy + Pydantic 后端
├── project_code/docs/        # 后端历史架构、接口、测试文档
├── UI/docs/                  # 前端联调、接口和问题复盘文档
├── docs/                     # 根级全栈当前技术文档
├── README.md                 # 本地启动入口
└── CLAUDE.md                 # 根级协作和目录路由规则
```

本地联调默认运行关系：

| 服务 | 默认地址/端口 | 说明 |
|---|---:|---|
| 前端 Vite | `http://localhost:3000` | `UI/vite.config.ts` 中配置开发代理 |
| 后端 FastAPI | `http://localhost:8000` | `uvicorn app.main:app --reload --port 8000` |
| API 前缀 | `/api/v1` | 前端默认 baseURL 与后端挂载前缀一致 |
| 上传静态文件 | 后端配置决定 | 后端 `StaticFiles` 挂载上传目录 |

根目录不是统一 npm 或 Python 项目。执行命令时必须进入对应子目录。

## 3. 前后端共享联调契约

前后端当前统一口径：

| 项 | 当前约定 |
|---|---|
| API 前缀 | `/api/v1` |
| 鉴权方式 | `Authorization: Bearer <access_token>` |
| 用户角色 | `student`、`teacher`、`admin` |
| 统一响应 | `{ code, message, data }` |
| 分页数据 | `{ items, total, page, page_size, total_pages }` |
| 登录态来源 | 前端 `useUserStore()`，后端 JWT + 当前用户依赖 |

前端 Axios 实例位于 `UI/src/api/index.ts`：

- 默认 `baseURL` 为 `import.meta.env.VITE_API_BASE_URL || '/api/v1'`。
- 请求拦截器从 localStorage 读取 `access_token` 注入 Bearer Token。
- 响应拦截器只在后端 `code === 200` 时返回 `data`，否则显示错误并 reject。
- 401 时尝试通过 `/api/v1/auth/refresh` 刷新 token，刷新失败则清理登录态并跳转登录页。

后端统一响应模型位于 `project_code/backend/app/schemas/common.py`：

- `ApiResponse[T]` 用于业务响应包装。
- `PageData[T]` 用于分页列表。
- 业务异常通过 `AppException` 及异常处理器转成统一格式。

## 4. 前端架构

### 4.1 技术栈

前端位于 `UI/`，主要技术栈：

- Vue 3
- TypeScript
- Vite
- Vue Router 4
- Pinia
- Element Plus
- Axios
- SCSS
- `@vue-office/*` 文档预览组件
- `cropperjs`、`vuedraggable` 等业务辅助依赖

常用命令在 `UI/` 下执行：

```bash
npm install
npm run dev
npm run dev:reset
npm run build
npm run preview
npx vue-tsc -b
```

### 4.2 入口与应用壳

关键入口：

| 文件 | 责任 |
|---|---|
| `UI/src/main.ts` | 创建 Vue 应用，挂载 Pinia、Router、Element Plus 中文 locale，注册 Element Plus 图标 |
| `UI/src/App.vue` | 应用壳，包含 `AppHeader`、`router-view`、`AppFooter`；通过路由 meta 控制是否隐藏页头页脚 |
| `UI/vite.config.ts` | Vue 插件、Element Plus 自动导入、别名、全局 SCSS、开发代理 |

`UI/vite.config.ts` 当前约定：

- `@` 指向 `UI/src`。
- `/api` 代理到 `http://localhost:8000`。
- Vite dev server 默认端口为 `3000`。
- SCSS 全局注入 `@/assets/styles/variables.scss`。

### 4.3 前端目录职责

```text
UI/src/
├── api/              # Axios 实例与各业务 API 封装
├── assets/styles/    # 全局样式、变量、响应式样式
├── components/       # 公共组件、布局组件、反馈组件
├── composables/      # 组合式函数，如分页、断点、学习进度同步
├── layouts/          # 独立布局，如认证页布局
├── router/           # 路由表和导航守卫
├── store/            # Pinia store
├── utils/            # 格式化、校验等工具
└── views/            # 页面，按业务域组织
```

页面按业务域组织：

- `views/home`：首页、课程列表、搜索筛选、分页。
- `views/auth`：登录、注册、找回密码。
- `views/course`：课程详情。
- `views/learn`：沉浸式学习页。
- `views/profile`：个人中心、资料、密码、学习记录、消息、我的反馈。
- `views/teacher`：讲师课程管理、课程编辑、章节资源、反馈管理。
- `views/admin`：用户管理、教师审核、公告、反馈、消息、分类、标签等后台功能。

### 4.4 路由与权限守卫

路由集中在 `UI/src/router/index.ts`。

主要路由分组：

| 路由 | 访问规则 | 页面 |
|---|---|---|
| `/` | public | 首页 |
| `/login`、`/register`、`/forgot-password` | public | 认证页面 |
| `/courses/:courseId` | public | 课程详情 |
| `/learn/:courseId` | requiresAuth + hideAppChrome | 沉浸式学习页 |
| `/profile/*` | requiresAuth | 个人中心 |
| `/teacher/*` | `permissionCode: 'teacher.course'` | 讲师中心 |
| `/admin/*` | admin 相关权限 | 管理后台 |

导航守卫职责：

- 根据路由 meta 设置页面标题。
- 已登录用户访问登录/注册/找回密码时重定向首页。
- 公开页面直接放行。
- 未登录访问鉴权页面时跳转登录页并带 `redirect`。
- 访问带 `permissionCode` 的页面前加载当前用户权限。
- `/admin` 默认重定向到当前用户有权限访问的第一个后台子页面。

### 4.5 状态管理

当前 Pinia store：

| Store | 文件 | 责任 |
|---|---|---|
| 用户/认证 | `UI/src/store/user.ts` | 登录态、用户资料、token、权限码、未读消息数、角色能力判断 |
| 分类 | `UI/src/store/category.ts` | 分类缓存、分类 ID 映射、分类查询辅助 |
| 学习 | `UI/src/store/learn.ts` | 当前课程、当前资源、播放状态、学习进度、资源遍历 |

`useUserStore()` 是前端登录态和权限判断的单一来源：

- 登录后通过 `setLoginInfo()` 写入标准化用户信息和 token。
- `restoreFromStorage()` 在 store 初始化时恢复本地登录态。
- `loadPermissions()` 通过 `/users/me/permissions` 获取权限码并缓存。
- `canAccessTeacherCenter`、`canAccessAdminCenter` 用于页头入口显示。
- `hasPermission()` 用于路由和菜单权限判断。

### 4.6 API 封装

前端 API 按业务模块拆分：

| 文件 | 主要范围 |
|---|---|
| `UI/src/api/index.ts` | Axios 实例、响应解包、token 注入、刷新 token、通用类型 |
| `UI/src/api/auth.ts` | 登录、注册、验证码、邮箱验证码、重置密码、刷新、退出 |
| `UI/src/api/course.ts` | 首页课程、课程列表、课程搜索 |
| `UI/src/api/category.ts` | 分类列表和 `id`/`category_id` 兼容 |
| `UI/src/api/learning.ts` | 课程详情、学习进度、资源播放、反馈、上传 |
| `UI/src/api/profile.ts` | 个人资料、权限、消息、学习记录、我的反馈 |
| `UI/src/api/teacher.ts` | 讲师课程、章节、小节、资源、素材、上传、反馈处理 |
| `UI/src/api/admin.ts` | 用户、教师审核、后台申请、分类、标签、消息、权限、公告、反馈 |

前端 API 层承担一部分兼容和映射职责，例如：

- 将后端消息字段映射为前端消息项。
- 将反馈字段和状态变体转换为页面期望结构。
- 对分类或课程 ID 做 `id` / `category_id` / `course_id` 兼容。

## 5. 后端架构

### 5.1 技术栈

后端位于 `project_code/backend/`，主要技术栈：

- FastAPI
- SQLAlchemy 2.x async
- Pydantic / pydantic-settings
- JWT
- Passlib bcrypt
- `diskcache` 与内存缓存
- pytest / pytest-asyncio / httpx

常用命令在 `project_code/backend/` 下执行：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
pytest tests/test_auth.py -v
pytest tests/test_auth.py::test_register -v
pytest tests/ --cov=app --cov-report=html
python scripts/init_db.py
python scripts/seed_data.py
```

### 5.2 应用入口与配置

关键文件：

| 文件 | 责任 |
|---|---|
| `project_code/backend/app/main.py` | FastAPI 应用入口、日志、生命周期、CORS、中间件、异常处理、路由挂载、上传静态文件 |
| `project_code/backend/app/config.py` | `pydantic-settings` 配置，读取环境变量和 `.env` |
| `project_code/backend/app/api/v1/router.py` | v1 路由聚合 |
| `project_code/backend/app/core/dependencies.py` | 数据库会话、当前用户依赖、可选用户依赖 |
| `project_code/backend/app/core/security.py` | 密码哈希、JWT access/refresh token |
| `project_code/backend/app/core/exceptions.py` | 业务异常和异常映射 |
| `project_code/backend/app/core/db_schema.py` | 启动/初始化时的历史 schema 兼容检查 |

后端启动时会：

1. 初始化日志配置。
2. 确保上传目录存在。
3. 执行数据库兼容性检查。
4. 注册 CORS 与请求日志中间件。
5. 注册业务异常和全局异常处理器。
6. 将 v1 router 挂载到 `settings.api_v1_prefix`，默认 `/api/v1`。
7. 挂载上传静态文件目录。

### 5.3 分层结构

后端主路径遵循垂直分层：

```text
API route -> schema -> service -> model -> database
```

目录职责：

```text
project_code/backend/app/
├── api/v1/        # FastAPI 路由层，处理 HTTP、依赖注入、权限检查、响应包装
├── schemas/       # Pydantic 请求/响应模型
├── services/      # 业务逻辑、查询、写入、领域规则
├── models/        # SQLAlchemy ORM 模型
├── core/          # 数据库依赖、安全、异常、日志、schema 兼容
├── middleware/    # 中间件
├── config.py      # 配置
└── main.py        # 应用入口
```

数据库会话由 `get_db()` 提供：

- route 成功返回后 commit。
- route 抛异常时 rollback。
- 最终关闭 session。
- 测试中通过 dependency override 替换为内存 SQLite session。

### 5.4 路由模块

当前 `app/api/v1/router.py` 聚合的业务路由包括：

| 模块 | 主要职责 |
|---|---|
| `health.py` | 健康检查、ping |
| `auth.py` | 注册、登录、退出、刷新 token、验证码、邮箱验证码、重置密码 |
| `categories.py` | 分类列表、创建、更新、删除 |
| `tags.py` | 标签列表、创建、删除、批量删除 |
| `announcements.py` | 公告列表、当前有效公告、详情、创建、更新、删除 |
| `permissions.py` | 权限树、当前用户权限码、角色权限、更新角色权限 |
| `users.py` | 个人资料、密码、学习记录、教师选项、我的反馈、用户管理、教师审核、管理员申请 |
| `courses.py` | 课程列表、搜索、首页、详情、讲师课程、课程创建/更新/发布/归档/删除、素材 |
| `uploads.py` | 文件、头像、反馈图片、分片上传 |
| `content.py` | 章节、小节、资源、排序、章节级资源、兼容删除路由 |
| `learning.py` | 开始学习、保存/读取进度、继续学习、资源播放/预览 URL |
| `feedbacks.py` | 反馈创建、列表、详情、处理、批量处理 |
| `messages.py` | 消息列表、详情、已读、全部已读、删除、未读数、发送消息 |

当前源码中存在若干兼容/历史路由，因此接口数量不应仅看旧文档统计。

### 5.5 模型与核心领域

主要 ORM 领域模型包括：

| 领域 | 代表模型 |
|---|---|
| 用户与认证 | `User`、`RefreshToken`、`CaptchaRecord`、`EmailCode` |
| 权限 | `Permission`、`RolePermission` |
| 系统数据 | `Category`、`Tag`、`Announcement` |
| 课程 | `Course`、`CourseMaterial`、`CourseTag` |
| 内容 | `Chapter`、`Section`、`Resource` |
| 学习 | `LearningProgress`、`ResourceProgress` |
| 反馈 | `Feedback` |
| 消息 | `Message` |
| 审核申请 | `TeacherAudit`、`AdminApplication` |

基础模型能力来自 `models/base.py`：

- `IDMixin`：整型主键。
- `TimestampMixin`：创建/更新时间。
- `SoftDeleteMixin`：软删除字段。
- `BaseModel`：通用抽象基类。

## 6. 核心业务模块

### 6.1 认证与用户

认证能力包括：

- 用户注册。
- 用户登录。
- 退出登录。
- 刷新 token。
- 图形验证码。
- 邮箱验证码。
- 重置密码。

用户相关能力包括：

- 获取/更新个人资料。
- 修改密码。
- 上传头像。
- 获取学习记录。
- 获取教师选项。
- 查看我的反馈。
- 管理员用户管理、状态调整、删除。
- 教师审核和管理员申请审核。

前端对应页面主要在：

- `UI/src/views/auth/`
- `UI/src/views/profile/`
- `UI/src/views/admin/UserManagePage.vue`
- `UI/src/views/admin/TeacherAuditPage.vue`

后端对应入口主要在：

- `project_code/backend/app/api/v1/auth.py`
- `project_code/backend/app/api/v1/users.py`
- `project_code/backend/app/services/auth_service.py`
- `project_code/backend/app/services/user_service.py`

### 6.2 课程发现与课程详情

课程发现能力包括：

- 首页课程加载。
- 课程列表分页。
- 搜索、分类、排序筛选。
- 课程详情。
- 课程大纲、章节、小节、资源和素材展示。

前端：

- `UI/src/views/home/HomePage.vue`
- `UI/src/views/course/CourseDetailPage.vue`
- `UI/src/components/common/CourseCard.vue`
- `UI/src/api/course.ts`
- `UI/src/api/category.ts`

后端：

- `project_code/backend/app/api/v1/courses.py`
- `project_code/backend/app/services/course_service.py`
- `project_code/backend/app/schemas/course.py`

### 6.3 学习页与学习进度

学习能力包括：

- 开始学习课程。
- 根据继续学习记录恢复学习位置。
- 播放视频/音频资源。
- 预览文档、图片等资源。
- 高频本地进度记录、定时上报、切换资源立即保存。
- 页面关闭时 beacon 保存。
- 在线/离线事件处理。

前端核心：

- `UI/src/views/learn/LearningPage.vue`
- `UI/src/store/learn.ts`
- `UI/src/composables/useProgressSync.ts`
- `UI/src/api/learning.ts`

后端核心：

- `project_code/backend/app/api/v1/learning.py`
- `project_code/backend/app/services/learning_service.py`
- `project_code/backend/app/models/learning.py`
- `project_code/backend/app/models/learning_progress.py`

### 6.4 讲师课程管理与内容编辑

讲师/管理员课程管理能力包括：

- 查看我的课程/管理课程。
- 创建和编辑课程。
- 发布、归档、删除课程。
- 批量课程操作。
- 管理章节、小节、资源、素材。
- 资源排序。
- 上传普通文件和分片文件。
- 管理课程反馈。

前端：

- `UI/src/views/teacher/CourseListPage.vue`
- `UI/src/views/teacher/CourseFormPage.vue`
- `UI/src/views/teacher/components/ChapterManager.vue`
- `UI/src/views/teacher/components/ResourceManager.vue`
- `UI/src/views/teacher/FeedbackManagePage.vue`
- `UI/src/api/teacher.ts`

后端：

- `project_code/backend/app/api/v1/courses.py`
- `project_code/backend/app/api/v1/content.py`
- `project_code/backend/app/api/v1/uploads.py`
- `project_code/backend/app/services/course_service.py`
- `project_code/backend/app/services/content_service.py`
- `project_code/backend/app/services/upload_service.py`

### 6.5 管理后台

后台能力包括：

- 用户管理。
- 教师审核。
- 管理员申请。
- 公告管理。
- 反馈管理。
- 系统消息。
- 分类管理。
- 标签管理。
- 角色权限管理相关接口。

前端：

- `UI/src/views/admin/AdminLayout.vue`
- `UI/src/views/admin/UserManagePage.vue`
- `UI/src/views/admin/TeacherAuditPage.vue`
- `UI/src/views/admin/AnnouncementPage.vue`
- `UI/src/views/admin/FeedbackManagePage.vue`
- `UI/src/views/admin/AdminMessagePage.vue`
- `UI/src/views/admin/CategoryManagePage.vue`
- `UI/src/views/admin/TagManagePage.vue`
- `UI/src/api/admin.ts`

注意：源码中存在 `AdminApplicationPage.vue`、`RolePermissionPage.vue` 等页面文件，但当前路由未必全部暴露。判断页面是否可达时以 `UI/src/router/index.ts` 和菜单配置为准。

后端：

- `project_code/backend/app/api/v1/users.py`
- `project_code/backend/app/api/v1/announcements.py`
- `project_code/backend/app/api/v1/categories.py`
- `project_code/backend/app/api/v1/tags.py`
- `project_code/backend/app/api/v1/permissions.py`
- `project_code/backend/app/api/v1/messages.py`
- `project_code/backend/app/api/v1/feedbacks.py`

### 6.6 消息与反馈

消息能力：

- 获取消息列表。
- 获取消息详情。
- 标记单条已读。
- 全部标记已读。
- 删除消息。
- 获取未读数量。
- 管理员发送系统消息。

反馈能力：

- 用户提交反馈。
- 用户查看自己的反馈。
- 教师查看/处理课程相关反馈。
- 管理员查看/处理全局反馈。
- 批量处理反馈。
- 上传反馈图片。

前端 API 对消息和反馈做了较多字段映射，涉及联调时应同时检查：

- `UI/src/api/profile.ts`
- `UI/src/api/admin.ts`
- `UI/src/api/teacher.ts`
- `project_code/backend/app/api/v1/messages.py`
- `project_code/backend/app/api/v1/feedbacks.py`
- `project_code/backend/app/schemas/message.py`
- `project_code/backend/app/schemas/feedback.py`

### 6.7 上传能力

上传能力包括：

- 通用文件上传。
- 头像上传。
- 反馈图片上传。
- 分片上传初始化。
- 上传分片。
- 完成分片上传。
- 上传文件静态访问。

上传相关配置在 `project_code/backend/app/config.py`，实现入口在：

- `project_code/backend/app/api/v1/uploads.py`
- `project_code/backend/app/services/upload_service.py`
- `UI/src/api/teacher.ts`
- `UI/src/api/learning.ts`

教师/管理员文件上传通常要求用户为 active 状态且有教师或管理员身份；头像和反馈图片上传要求用户状态有效。

## 7. 角色、权限与认证流

### 7.1 角色

当前系统角色：

| 角色 | 说明 |
|---|---|
| `student` | 学生，学习课程、查看个人中心、提交反馈 |
| `teacher` | 讲师，包含学生能力，并可管理课程内容和课程反馈 |
| `admin` | 管理员，包含讲师能力，并可进入后台管理用户、系统数据、公告、消息等 |

### 7.2 前端权限流

前端权限判断链路：

1. 用户登录后，登录页把后端返回的用户信息和 token 写入 `useUserStore()`。
2. `useUserStore()` 标准化用户字段并持久化 token、用户信息、权限码。
3. 访问受限路由时，路由守卫检查 `requiresAuth` 和 `permissionCode`。
4. 如果权限码未加载，先调用 `loadPermissions()` 获取当前用户权限。
5. 菜单和页头入口根据 `canAccessTeacherCenter`、`canAccessAdminCenter`、`hasPermission()` 显示或隐藏。

### 7.3 后端权限流

后端权限判断由多层组成：

- `get_current_user_id()`：要求 Bearer access token 合法。
- `get_current_user()`：加载当前用户记录。
- `PermissionService.ensure_permission()`：检查角色是否拥有指定权限码。
- `PermissionService.ensure_admin()`：检查用户角色是否为 admin。
- 具体 service 或 route 内部还会做所有者、教师身份、课程归属、状态等业务校验。

当前代码中不同模块的授权强度不完全相同：

- 管理类、系统配置类、部分消息/反馈处理接口有显式权限码检查。
- 部分课程内容接口主要依赖登录态和业务服务内的所有权/角色判断。
- 上传接口对教师/管理员、active 状态有显式检查。

开发新接口时应优先复用现有依赖和 `PermissionService`，并同步检查前端路由 meta 与菜单权限码。

### 7.4 联调测试账号

种子数据导入后，常用账号：

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin1` | `Admin123456` |
| 教师 | `teacher1` | `Test123456` |
| 教师 | `teacher2` | `Test123456` |
| 学生 | `student1` | `Test123456` |
| 学生 | `student2` | `Test123456` |

不同文档中邮箱后缀可能有 `@example.com` 与 `@test.com` 差异。联调时用户名和密码更稳定，除非当前测试明确依赖邮箱。

## 8. API 与集成资料索引

详细接口不在本文档中重复维护，避免出现多个接口清单互相冲突。当前建议索引：

| 文档 | 用途 | 注意 |
|---|---|---|
| `project_code/docs/api-endpoint-inventory.md` | 后端接口清单、路由、schema、测试映射 | 接口总数统计存在不一致，引用精确数字前要复核代码 |
| `project_code/docs/api-testing-guide.md` | 手工 API 测试流程、curl 示例、上传流程 | 测试账号段落有重复，优先参考顶部和根规则 |
| `UI/docs/前端接口文档.md` | 前端消费视角接口说明 | 部分认证字段和旧接口假设可能过期 |
| `UI/docs/login-auth-issue-review.md` | 登录认证问题复盘和前端状态规则 | 对当前 auth store 规则有较高参考价值 |
| `UI/docs/course-id-mismatch-review.md` | `id` / `course_id` 差异复盘 | 适合作为字段兼容风险提醒 |
| `UI/前后端接口文档差异对照.md` | 历史前后端差异清单 | 只作历史排查线索，不作为当前事实 |
| `project_code/docs/architecture.md` | 后端分层和旧架构说明 | 模块/API 清单偏旧 |
| `project_code/docs/test-plan.md` | 后端测试设计历史 | endpoint 数量和测试文件布局偏旧 |

联调排查优先顺序：

1. 看前端 API 调用文件，确认路径、请求字段、响应映射。
2. 看后端 route 和 schema，确认实际路径、参数和返回结构。
3. 看 service，确认权限、状态、所有权和业务规则。
4. 看测试，确认已有验证覆盖。
5. 最后再参考历史文档判断差异来源。

## 9. 开发、测试与验证

### 9.1 前端验证

前端代码变更后，优先在 `UI/` 下执行：

```bash
npm run build
npx vue-tsc -b
```

如果改动页面或交互，还应手动检查：

- 路由能否进入目标页面。
- 权限页是否仍受 `UI/src/router/index.ts` 和 `UI/src/store/user.ts` 控制。
- PC 和移动端下是否存在明显布局破坏。
- 登录、退出、刷新 token、权限菜单是否仍正常。

### 9.2 后端验证

后端代码变更后，优先在 `project_code/backend/` 下执行相关 pytest：

```bash
pytest tests/test_auth.py -v
pytest tests/test_courses.py -v
pytest tests/test_learning.py -v
pytest tests/ -v
```

改接口或模型时还应检查：

- 路由是否已挂载在 `project_code/backend/app/api/v1/router.py`。
- 响应是否保持 `{ code, message, data }`。
- schema 是否与前端读取字段一致。
- 权限和角色检查是否与前端路由/menu 一致。

### 9.3 联调验证

跨前后端改动至少同时做：

- 前端构建或类型检查。
- 后端相关模块 pytest。
- API 路径核对：前端 `/api/v1/...` 是否对应后端 route。
- 字段核对：请求字段、响应字段、分页字段、上传返回值是否一致。
- 角色核对：学生、教师、管理员各自入口和接口权限是否符合预期。

页面或交互改动应启动服务并在浏览器中验证黄金路径。

### 9.4 文档类变更验证

如果只修改文档：

- 不需要运行前端 build 或后端 pytest。
- 需要说明未运行构建/测试的原因。
- 需要保证引用路径和当前文件结构存在。

## 10. 文档维护规则

为了避免再次产生文档漂移：

1. **路由或接口变更**：优先更新后端 route/schema/service，并同步更新 `project_code/docs/api-endpoint-inventory.md` 或相关接口说明。
2. **前端 API 映射变更**：同步更新 `UI/src/api/*` 类型和前端接口文档。
3. **认证/权限口径变更**：同步检查 `UI/src/store/user.ts`、`UI/src/router/index.ts`、后端 `PermissionService`、根级规则和本文档。
4. **业务模块新增**：在本文档的核心业务模块中补充总览，但不要复制完整接口表。
5. **历史文档冲突**：在新文档中明确标注旧资料为历史参考，不要让多个旧入口同时成为“当前事实”。
6. **验证命令变更**：同步更新根 `CLAUDE.md`、子项目 `CLAUDE.md` 或本文档中的命令入口。

## 11. 快速定位表

| 任务类型 | 前端优先看 | 后端优先看 |
|---|---|---|
| 登录/注册/认证 | `UI/src/views/auth/`、`UI/src/api/auth.ts`、`UI/src/store/user.ts`、`UI/src/router/index.ts` | `app/api/v1/auth.py`、`app/services/auth_service.py`、`app/schemas/auth.py`、`tests/test_auth.py` |
| 课程列表/详情 | `UI/src/views/home/`、`UI/src/views/course/CourseDetailPage.vue`、`UI/src/api/course.ts` | `app/api/v1/courses.py`、`app/services/course_service.py`、`app/schemas/course.py`、`tests/test_courses.py` |
| 学习页/进度 | `UI/src/views/learn/LearningPage.vue`、`UI/src/store/learn.ts`、`UI/src/composables/useProgressSync.ts`、`UI/src/api/learning.ts` | `app/api/v1/learning.py`、`app/services/learning_service.py`、`app/schemas/learning.py`、`tests/test_learning.py` |
| 个人中心/消息/反馈 | `UI/src/views/profile/`、`UI/src/api/profile.ts`、`UI/src/components/feedback/` | `app/api/v1/users.py`、`app/api/v1/messages.py`、`app/api/v1/feedbacks.py`、对应 service/tests |
| 讲师课程管理 | `UI/src/views/teacher/`、`UI/src/api/teacher.ts` | `app/api/v1/courses.py`、`app/api/v1/content.py`、`app/services/course_service.py`、`app/services/content_service.py` |
| 管理后台 | `UI/src/views/admin/`、`UI/src/api/admin.ts` | `app/api/v1/users.py`、`app/api/v1/announcements.py`、`app/api/v1/categories.py`、`app/api/v1/tags.py`、`app/api/v1/permissions.py` |
| 上传 | `UI/src/api/teacher.ts`、`UI/src/api/learning.ts`、相关上传组件 | `app/api/v1/uploads.py`、`app/services/upload_service.py`、`tests/test_uploads.py` |
