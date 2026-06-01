# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 工作区概述

这是一个在线学习视频项目的联合开发工作区，包含两个已经独立演进过的子项目：

- `E:\video_project\proj_ui\UI\`：前端项目
- `E:\video_project\proj_ui\project_code\`：后端项目

从当前开始，Claude 在 `E:\video_project\proj_ui` 根目录工作时，必须先按任务类型定位到正确子目录，再读取并遵循对应子项目规则。

## 常用开发命令

根目录本身不是统一的 npm、Python 或 Git 项目；命令必须在对应子目录执行。

### 前端命令

在 `E:\video_project\proj_ui\UI` 下执行：

```bash
# 安装依赖
npm install

# 启动 Vite 开发服务（端口 3000，/api 代理到 http://localhost:8000）
npm run dev

# Windows 上遇到 Vite 预构建缓存异常时重置缓存后启动
npm run dev:reset

# 类型检查并构建生产包
npm run build

# 预览构建产物
npm run preview

# 仅运行 Vue/TypeScript 类型检查
npx vue-tsc -b
```

### 后端命令

在 `E:\video_project\proj_ui\project_code\backend` 下执行：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 FastAPI 开发服务
uvicorn app.main:app --reload --port 8000

# 运行全部测试
pytest tests/ -v

# 运行单个测试模块
pytest tests/test_auth.py -v

# 运行单个测试用例
pytest tests/test_auth.py::test_register -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 初始化数据库表结构
python scripts/init_db.py

# 导入种子数据
python scripts/seed_data.py
```

## 高层架构

- 工作区由两个独立子项目组成：`UI` 是 Vue 3 + TypeScript + Vite 前端，`project_code/backend` 是 FastAPI + SQLAlchemy + Pydantic 后端。
- 前端入口是 `UI/src/main.ts`，创建 Vue 应用并挂载 Pinia、Vue Router 与 Element Plus；页面按角色和业务域组织在 `UI/src/views`。
- 前端 API 层集中在 `UI/src/api`，`index.ts` 创建 Axios 实例，默认 `baseURL` 为 `/api/v1`，开发环境由 `UI/vite.config.ts` 将 `/api` 代理到后端 `http://localhost:8000`。
- 登录态和权限判断以 `UI/src/store/user.ts` 为单一数据源，路由守卫在 `UI/src/router/index.ts` 中根据 `meta.public`、`meta.requiresAuth` 和 `meta.permissionCode` 控制访问。
- 后端入口是 `project_code/backend/app/main.py`，负责配置 CORS、请求日志中间件、异常处理、上传静态目录，并用 `settings.api_v1_prefix` 挂载 v1 路由。
- 后端路由聚合在 `project_code/backend/app/api/v1/router.py`，各业务模块通常按 `api/v1/*.py`、`schemas/*.py`、`services/*.py`、`models/*.py` 分层协作。
- 后端配置由 `project_code/backend/app/config.py` 通过 `pydantic-settings` 从环境变量或 `.env` 加载；测试默认使用内存 SQLite，见 `project_code/backend/tests/conftest.py`。
- 前后端联调统一口径是 `/api/v1`、Bearer Token、角色 `student`/`teacher`/`admin`、响应结构 `{ code, message, data }`。

## 联调测试账号

种子数据导入后可用。AI 做 API、前端联调或浏览器测试时应直接使用这些账号，不要再要求用户手动输入账号密码。

| 角色 | 用户名 | 密码 | 邮箱 |
|------|--------|------|------|
| 管理员 | `admin1` | `Admin123456` | `admin1@example.com` |
| 教师 | `teacher1` | `Test123456` | `teacher1@example.com` |
| 学生 | `student1` | `Test123456` | `student1@example.com` |
| 学生 | `student2` | `Test123456` | `student2@example.com` |

## 强制目录路由规则

### 前端任务必须优先检查的目录

凡是涉及以下内容，必须先到 `E:\video_project\proj_ui\UI` 下查找：
- 页面
- 布局
- 组件
- 路由
- Store
- 前端 API 封装
- 样式
- Vite 构建配置
- 前端联调逻辑

优先路径：
- `E:\video_project\proj_ui\UI\src\views\`：页面与页面子组件
- `E:\video_project\proj_ui\UI\src\components\`：公共组件
- `E:\video_project\proj_ui\UI\src\layouts\`：布局组件
- `E:\video_project\proj_ui\UI\src\router\`：前端路由与守卫
- `E:\video_project\proj_ui\UI\src\store\`：Pinia 状态管理
- `E:\video_project\proj_ui\UI\src\api\`：前端接口封装
- `E:\video_project\proj_ui\UI\src\assets\styles\`：样式与变量
- `E:\video_project\proj_ui\UI\vite.config.ts`：开发代理与构建配置
- `E:\video_project\proj_ui\UI\docs\`：前端联调和问题复盘文档

### 后端任务必须优先检查的目录

凡是涉及以下内容，必须先到 `E:\video_project\proj_ui\project_code` 下查找：
- API 路由
- 业务服务
- 数据模型
- 数据校验
- 后端测试
- 数据库初始化
- 脚本
- 后端架构文档

优先路径：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\`：FastAPI 路由入口
- `E:\video_project\proj_ui\project_code\backend\app\services\`：业务逻辑
- `E:\video_project\proj_ui\project_code\backend\app\models\`：数据库模型
- `E:\video_project\proj_ui\project_code\backend\app\schemas\`：Pydantic 模型
- `E:\video_project\proj_ui\project_code\backend\app\core\`：配置与核心能力
- `E:\video_project\proj_ui\project_code\backend\tests\`：后端测试
- `E:\video_project\proj_ui\project_code\backend\scripts\`：初始化与种子脚本
- `E:\video_project\proj_ui\project_code\docs\`：后端架构、接口清单、测试计划

### 联调任务必须同时检查的目录

凡是涉及以下内容，必须同时检查前后端目录：
- 登录与认证
- 角色权限
- 课程详情与学习页
- 上传
- 分页、筛选、搜索
- 字段对齐
- 接口路径与响应格式

联调时至少同时检查：
- 前端：`E:\video_project\proj_ui\UI\src\api\`、`E:\video_project\proj_ui\UI\src\views\`、`E:\video_project\proj_ui\UI\src\store\`、`E:\video_project\proj_ui\UI\src\router\`
- 后端：`E:\video_project\proj_ui\project_code\backend\app\api\v1\`、`E:\video_project\proj_ui\project_code\backend\app\services\`、`E:\video_project\proj_ui\project_code\backend\app\schemas\`

## 常见业务任务的目录定位

### 认证与登录注册
前端优先检查：
- `E:\video_project\proj_ui\UI\src\views\auth\`：登录、注册、找回密码页面
- `E:\video_project\proj_ui\UI\src\api\auth.ts`：认证接口封装
- `E:\video_project\proj_ui\UI\src\store\user.ts`：登录态与用户信息
- `E:\video_project\proj_ui\UI\src\router\index.ts`：登录跳转、公开路由、权限守卫

后端优先检查：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\auth.py`：注册、登录、退出、刷新令牌
- `E:\video_project\proj_ui\project_code\backend\app\services\auth_service.py`：认证业务逻辑
- `E:\video_project\proj_ui\project_code\backend\app\schemas\auth.py`：认证请求与响应模型
- `E:\video_project\proj_ui\project_code\backend\tests\test_auth.py`：认证测试

### 首页、课程列表与课程详情
前端优先检查：
- `E:\video_project\proj_ui\UI\src\views\home\`：首页与首页组件
- `E:\video_project\proj_ui\UI\src\views\course\CourseDetailPage.vue`：课程详情页
- `E:\video_project\proj_ui\UI\src\components\common\CourseCard.vue`：课程卡片
- `E:\video_project\proj_ui\UI\src\api\course.ts`：课程相关接口
- `E:\video_project\proj_ui\UI\src\api\category.ts`：分类筛选接口

后端优先检查：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\courses.py`：课程列表、搜索、首页课程、课程详情
- `E:\video_project\proj_ui\project_code\backend\app\services\course_service.py`：课程查询与写入逻辑
- `E:\video_project\proj_ui\project_code\backend\app\schemas\course.py`：课程相关数据模型
- `E:\video_project\proj_ui\project_code\backend\tests\test_courses.py`：课程测试

### 学习页与学习进度
前端优先检查：
- `E:\video_project\proj_ui\UI\src\views\learn\LearningPage.vue`：沉浸式学习页
- `E:\video_project\proj_ui\UI\src\store\learn.ts`：学习状态
- `E:\video_project\proj_ui\UI\src\composables\useProgressSync.ts`：学习进度同步
- `E:\video_project\proj_ui\UI\src\api\learning.ts`：学习相关接口

后端优先检查：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\learning.py`：学习进度相关接口
- `E:\video_project\proj_ui\project_code\backend\app\services\learning_service.py`：学习业务逻辑
- `E:\video_project\proj_ui\project_code\backend\app\schemas\learning.py`：学习数据模型
- `E:\video_project\proj_ui\project_code\backend\tests\test_learning.py`：学习模块测试

### 个人中心、消息与反馈
前端优先检查：
- `E:\video_project\proj_ui\UI\src\views\profile\`：个人中心页面
- `E:\video_project\proj_ui\UI\src\components\feedback\`：反馈组件
- `E:\video_project\proj_ui\UI\src\api\profile.ts`：个人中心接口
- `E:\video_project\proj_ui\UI\src\store\user.ts`：用户信息读取

后端优先检查：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\users.py`：用户资料、密码等接口
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\messages.py`：消息接口
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\feedbacks.py`：反馈接口
- `E:\video_project\proj_ui\project_code\backend\app\services\user_service.py`
- `E:\video_project\proj_ui\project_code\backend\app\services\message_service.py`
- `E:\video_project\proj_ui\project_code\backend\app\services\feedback_service.py`
- `E:\video_project\proj_ui\project_code\backend\tests\test_users.py`
- `E:\video_project\proj_ui\project_code\backend\tests\test_feedbacks.py`

### 讲师课程管理与课程内容编辑
前端优先检查：
- `E:\video_project\proj_ui\UI\src\views\teacher\CourseListPage.vue`：讲师课程列表
- `E:\video_project\proj_ui\UI\src\views\teacher\CourseFormPage.vue`：课程创建与编辑
- `E:\video_project\proj_ui\UI\src\views\teacher\components\ChapterManager.vue`：章节管理
- `E:\video_project\proj_ui\UI\src\views\teacher\components\ResourceManager.vue`：资源管理
- `E:\video_project\proj_ui\UI\src\api\teacher.ts`：讲师侧接口
- `E:\video_project\proj_ui\UI\src\api\course.ts`：课程接口

后端优先检查：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\courses.py`：课程创建、编辑、讲师课程接口
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\content.py`：章节、小节、资源相关接口
- `E:\video_project\proj_ui\project_code\backend\app\services\course_service.py`
- `E:\video_project\proj_ui\project_code\backend\app\services\content_service.py`
- `E:\video_project\proj_ui\project_code\backend\tests\test_courses.py`
- `E:\video_project\proj_ui\project_code\backend\tests\test_content.py`

### 管理后台
前端优先检查：
- `E:\video_project\proj_ui\UI\src\views\admin\UserManagePage.vue`
- `E:\video_project\proj_ui\UI\src\views\admin\RolePermissionPage.vue`
- `E:\video_project\proj_ui\UI\src\views\admin\AnnouncementPage.vue`
- `E:\video_project\proj_ui\UI\src\views\admin\FeedbackManagePage.vue`
- `E:\video_project\proj_ui\UI\src\api\admin.ts`

后端优先检查：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\users.py`
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\announcements.py`
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\categories.py`
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\tags.py`
- `E:\video_project\proj_ui\project_code\backend\app\services\system_service.py`
- `E:\video_project\proj_ui\project_code\backend\tests\test_system.py`

### 上传能力
前端优先检查：
- `E:\video_project\proj_ui\UI\src\views\teacher\CourseFormPage.vue`
- `E:\video_project\proj_ui\UI\src\api\teacher.ts`
- `E:\video_project\proj_ui\UI\src\api\course.ts`

后端优先检查：
- `E:\video_project\proj_ui\project_code\backend\app\api\v1\uploads.py`：`/api/v1/upload/file`
- `E:\video_project\proj_ui\project_code\backend\app\services\upload_service.py`：上传保存逻辑
- `E:\video_project\proj_ui\project_code\backend\tests\test_courses.py`：上传相关测试

## 子项目规则继承

### 前端规则来源
处理前端任务时，必须继续遵循：
- `E:\video_project\proj_ui\UI\CLAUDE.md`

它负责约束：
- Vue 3、Vite、Pinia、Vue Router、Axios 使用方式
- 认证状态统一通过 Store 管理
- 页面、组件、Store、API 命名方式
- 响应式与移动端适配要求

### 后端规则来源
处理后端任务时，必须继续遵循：
- `E:\video_project\proj_ui\project_code\CLAUDE.md`

它负责约束：
- FastAPI、SQLAlchemy、Pydantic、pytest 相关实现
- `/api/v1/` 路由规范与统一响应格式
- 后端测试入口
- `operations-log.md` 记录要求

## 跨模块统一口径

以下口径在联合开发时必须保持一致：
- 角色名：`student`、`teacher`、`admin`
- API 前缀：`/api/v1`
- 认证方式：Bearer Token
- 响应格式：`{ code, message, data }`

如果一侧修改了这些基础口径，另一侧必须同步检查并更新。

## 当前工作流说明

- 根级 `E:\video_project\proj_ui\.spec-workflow\` 当前只是插件自动创建的目录，暂时不能视为已经投入使用的统一工作流入口。
- `E:\video_project\proj_ui\UI\.spec-workflow\` 与 `E:\video_project\proj_ui\project_code\.spec-workflow\` 目前仍视为各自历史资料。
- 在根级协作规则稳定前，不要因为看到根级 `.spec-workflow` 就假设整个工作区已经完成统一初始化。

## 历史痕迹处理规则

以下内容默认视为历史痕迹或旁路资料，不能当作当前主入口：
- `E:\video_project\proj_ui\project_code\CLAUDE.bak.md`
- `E:\video_project\proj_ui\project_code\.claude\worktrees\`
- 子项目内已经失效的旧 `plan`、旧 `context-summary`

需要引用这些资料时，必须先确认它们仍然反映当前代码状态。

## 日志与验证约定

- 后端文件发生实际变更时，继续遵循 `E:\video_project\proj_ui\project_code\CLAUDE.md` 中的要求，更新 `E:\video_project\proj_ui\project_code\operations-log.md`
- 前端文件发生实际变更时，继续遵循 `E:\video_project\proj_ui\UI\CLAUDE.md` 中的要求，更新 `E:\video_project\proj_ui\UI\operations-log.md`
- 联调任务必须明确说明修改落在前端、后端还是两边
- 根目录协作时，回答中应明确指出实际修改目录，避免在错误子目录下找文件

## 根级验证规则

### 前端任务最小验证
如果改动只发生在 `E:\video_project\proj_ui\UI`，至少优先考虑以下验证：
- 在 `E:\video_project\proj_ui\UI` 下运行 `npm run build`
- 涉及类型变更时运行 `npx vue-tsc`
- 涉及代码规范问题时运行 `npx eslint`

如果是页面或交互改动，还应至少检查：
- 路由是否仍能进入目标页面
- 权限页是否仍受 `E:\video_project\proj_ui\UI\src\router\index.ts` 和 `E:\video_project\proj_ui\UI\src\store\user.ts` 控制
- 页面在 PC 和移动端下是否没有明显布局破坏

### 后端任务最小验证
如果改动只发生在 `E:\video_project\proj_ui\project_code\backend`，至少优先考虑以下验证：
- 在 `E:\video_project\proj_ui\project_code\backend` 下运行对应的 `pytest`
- 改动接口时优先跑对应模块测试，例如 `pytest tests/test_auth.py`、`pytest tests/test_courses.py`、`pytest tests/test_learning.py`
- 改动范围较大时再考虑跑 `pytest tests/ -v`

如果改动涉及后端接口或模型，还应至少检查：
- 路由是否仍挂载在 `E:\video_project\proj_ui\project_code\backend\app\api\v1\router.py`
- 响应格式是否仍符合 `{ code, message, data }`
- 如果后端实际文件发生变更，是否已同步更新 `E:\video_project\proj_ui\project_code\operations-log.md`

### 联调任务最小验证
如果改动同时涉及 `E:\video_project\proj_ui\UI` 和 `E:\video_project\proj_ui\project_code`，至少同时做这两类验证：
- 前端至少执行一次构建或类型检查
- 后端至少执行一次与改动模块对应的 pytest

联调时还必须额外核对：
- 前端调用路径是否仍对应后端 `/api/v1/...`
- 前端字段读取是否与后端 schema 和响应字段一致
- 登录态、角色判断、分页字段、上传返回值等关键口径是否前后端一致

### 验证结果记录要求
- 回答中要明确写出本次验证是前端验证、后端验证还是联调验证
- 如果没有执行某项验证，要明确说明原因
- 不要把前端问题只在后端验证，也不要把后端问题只在前端验证
