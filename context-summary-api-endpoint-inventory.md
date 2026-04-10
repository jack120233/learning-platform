## 项目上下文摘要（实际接口清单）
生成时间：2026-04-10

### 1. 相似实现分析
- **实现 1**: `backend/app/main.py:87-108`
  - 模式：统一由 `app.include_router(api_v1_router, prefix=settings.api_v1_prefix)` 挂载。
  - 可复用：`settings.api_v1_prefix` 作为完整路径前缀来源。
  - 需注意：`GET /`、`/docs`、`/redoc`、`/openapi.json` 不应计入业务接口。

- **实现 2**: `backend/app/api/v1/router.py:16-27`
  - 模式：通过 `include_router` 聚合 12 个业务模块。
  - 可复用：模块分组名称可直接作为文档章节标题。
  - 需注意：仅统计这里实际挂载的模块。

- **实现 3**: `backend/app/api/v1/auth.py:26-208`
  - 模式：`APIRouter(prefix=...) + response_model=ApiResponse[...] + summary/description`。
  - 可复用：每个接口都能直接提取方法、路径、请求模型、响应模型。
  - 需注意：`logout` 使用 `CurrentUserId`，是认证判定的直接证据。

- **实现 4**: `backend/app/api/v1/users.py:37-340`
  - 模式：分页统一使用 `ApiResponse[PageData[T]]`。
  - 可复用：`Query(...)` 里的描述可直接作为查询参数摘要。
  - 需注意：多个接口描述写“管理员权限”，但路由层仅见 `CurrentUserId`。

- **实现 5**: `backend/app/api/v1/courses.py`
  - 模式：公开列表/详情 + 登录后管理操作混合在同一模块。
  - 可复用：课程、资料接口适合作为“POST 承担更新语义”的特殊说明案例。
  - 需注意：`POST /courses/{course_id}`、`POST /courses/{course_id}/publish`、`POST /courses/{course_id}/archive` 不是标准 REST 更新/状态变更写法。

### 2. 项目约定
- **命名约定**: 路由处理函数使用动宾结构，如 `get_courses`、`update_profile`、`process_feedback`。
- **文件组织**: 路由位于 `backend/app/api/v1/`，模型位于 `backend/app/schemas/`，测试位于 `backend/tests/`。
- **路径约定**: 统一前缀为 `/api/v1`。
- **响应约定**: 统一外层为 `ApiResponse[T]`，分页为 `ApiResponse[PageData[T]]`。
- **认证约定**: `CurrentUserId` = 需要 Bearer Token；`OptionalUserId` = 可选登录；未使用认证依赖 = 无需登录。

### 3. 可复用组件清单
- `backend/app/schemas/common.py:15-68`：`ApiResponse`、`PageData` 统一响应包装。
- `backend/app/core/dependencies.py:61-163`：`CurrentUserId`、`OptionalUserId` 认证判定依据。
- `backend/app/api/v1/*`：`summary`、`description`、`response_model` 可直接生成接口表。
- `docs/api-testing-guide.md`：可复用“模块分节”展示思路，但不作为是否实现的判定依据。

### 4. 测试策略
- **测试框架**: `pytest + httpx`。
- **参考文件**:
  - `backend/tests/test_auth.py`
  - `backend/tests/test_users.py`
  - `backend/tests/test_courses.py`
  - `backend/tests/test_content.py`
  - `backend/tests/test_learning.py`
  - `backend/tests/test_feedbacks.py`
  - `backend/tests/test_system.py`
- **覆盖方式**: 用测试文件和手动测试文档交叉校验高频路径，但以路由代码为准。

### 5. 依赖和集成点
- **路由注册链**: `backend/app/main.py` → `backend/app/api/v1/router.py` → 各模块路由文件。
- **模型来源**: `backend/app/schemas/*.py`。
- **测试映射**: 用户/课程/内容/学习/反馈/系统模块均有对应测试文件；消息模块未见独立 `test_messages.py`。

### 6. 技术选型理由
- 采用“代码优先”的文档生成方式，避免把需求文档或手测文档中的理想设计误写成已实现事实。
- 采用“模块总览 + 模块明细 + 模型附录”，方便前后端逐项核对。

### 7. 关键风险点
- 多个接口描述中出现“管理员权限”“讲师权限”，但路由层未见显式 RBAC 依赖。
- 存在 `POST` 承担更新/状态变更/删除语义的接口，需要在文档中特别提示。
- `content.py` 没有统一 `prefix`，但路径字面量仍落在 `/api/v1/courses/...`。
- `learning.py:get_progress` 写成 `user_id: CurrentUserId = None`，认证写法不够一致，但仍带 `CurrentUserId` 依赖。
- 当前已挂载业务接口总数应为 **80**，后续校验必须以此为基线。
