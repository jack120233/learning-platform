# brainstorm: admin profile message feedback fixes

## Goal

修复管理后台、个人中心、消息中心、反馈详情和用户身份展示相关的一组体验与数据一致性问题，减少管理员侧重复入口，统一用户可识别身份展示，并补齐用户名一次性修改以及学生/教师消息批量删除能力。

## What I already know

* 管理后台需要移除独立“消息中心”入口。
* `/admin/messages` 的能力应并入 `/profile/messages`。
* 管理员不需要 `/profile/feedbacks` 页面。
* `/profile` 当前个人信息用户名展示出现 `admin1#undefined`，说明前端身份展示读取 ID 字段存在缺口。
* 项目记忆要求用户展示身份使用 `username#user_id`，因为用户名是真实姓名且可能重复，nickname 不适合做身份标识。
* 全站 `用户名#id` 展示要美化，避免 `#id` 视觉过于突兀。
* 个人信息页用户名支持修改一次，需要二次确认；数据库记录原用户名；预留教师给用户再次开放一次用户名修改的能力。
* 管理员的“用户反馈详情”侧边栏样式要参考老师对学生的“反馈详情”。
* 老师消息中心缺少消息选择和批量删除功能。
* 学生消息中心也必须支持消息选择和批量删除；当前代码显示 `/profile/messages` 已有批量管理逻辑，但需要显式验收学生路径。
* 初步判断这是前后端联调任务：第 1/2/4/6/7 多为前端；第 5 必须涉及后端模型/API/测试；第 7 可能需要后端批量删除接口，需确认现有 API。

## Assumptions (temporary)

* `/profile/messages` 可作为所有角色的统一消息中心入口，管理员也通过个人中心消息页处理消息。
* 管理员访问 `/profile/feedbacks` 应在路由和导航层隐藏/阻止，而不是删除学生/教师使用的反馈功能。
* 用户身份展示应抽成统一前端组件或工具，避免每处手拼 `username#id`。
* 用户名修改一次的限制应由后端强制，前端只做提示和二次确认。
* “预留教师再次开放一次修改用户名”本次按完整入口处理：需要后端接口/权限校验，也需要教师端可操作入口。

## Open Questions

* 已决定：本次直接做出“教师给用户再次开放一次用户名修改”的完整前端入口、后端接口和权限校验。

## Requirements (evolving)

* 管理后台导航不再展示独立消息中心。
* 管理员消息能力统一进入 `/profile/messages`。
* 管理员不显示/不可使用 `/profile/feedbacks`。
* 个人信息页正确展示用户 ID，不再出现 `#undefined`。
* 全站用户身份展示样式统一美化。
* 用户名最多自助修改一次，并需要二次确认。
* 用户名修改后后端记录原用户名。
* 管理员用户反馈详情侧边栏样式与教师侧反馈详情保持一致风格。
* 教师消息中心支持勾选消息并批量删除。
* 学生消息中心支持勾选消息并批量删除。

## Acceptance Criteria (evolving)

* [ ] 管理员侧导航没有“消息中心”菜单项。
* [ ] 访问或使用消息中心时，管理员使用 `/profile/messages`。
* [ ] 管理员看不到个人中心“我的反馈”入口，直接访问 `/profile/feedbacks` 时有合理处理。
* [ ] `/profile` 展示用户名时不出现 `undefined`。
* [ ] 用户身份在主要页面以“用户名 + 弱化 ID 标识”的统一样式展示。
* [ ] 用户第一次修改用户名时出现二次确认，成功后刷新个人资料。
* [ ] 用户第二次自助修改用户名被后端拒绝并有明确前端提示。
* [ ] 数据库可追溯原用户名。
* [ ] 管理员反馈详情侧边栏视觉与教师反馈详情一致或明显接近。
* [ ] 教师消息列表支持多选、批量删除，并更新列表/未读数。
* [ ] 学生消息列表支持多选、批量删除，并更新列表/未读数。

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky
* 前端文件变更时更新 `UI/operations-log.md`
* 后端文件变更时更新 `project_code/operations-log.md`

## Out of Scope (explicit)

* 暂不改变项目统一身份口径：仍使用 username + user ID 进行消歧。
* 暂不引入 nickname 作为身份展示来源。

## Subtasks / Parallelization

### Batch A — can run in parallel after basic context init

* `05-09-admin-profile-message-routing`: 管理后台消息入口、管理员 `/profile/messages`、管理员 `/profile/feedbacks` 路由与导航清理。
* `05-09-admin-feedback-detail-styling`: 管理员用户反馈详情抽屉样式对齐教师反馈详情。
* `05-09-teacher-message-batch-delete`: 教师消息中心“平台通知”批量选择/删除。可先用现有单条删除 API 并发实现；若需要后端批量接口再升级为联调子任务。
* `05-09-student-message-batch-delete`: 学生消息中心批量删除显式验收/修复。当前 `/profile/messages` 已有批量管理代码，重点防回归验证。

### Batch B — should be sequenced together

* `05-09-unified-user-identity-display`: 统一身份展示组件/工具，并修复 `id`/`user_id` 映射导致的 `#undefined`。
* `05-09-one-time-username-change`: 用户名一次性修改。依赖身份展示的 `id` 映射与 profile API 类型统一，且涉及后端模型/API/测试。

### Dependency notes

* 身份展示美化和用户名修改都触碰 `/profile`，建议先做 `unified-user-identity-display`，再做 `one-time-username-change`，减少冲突。
* 管理员路由清理和教师批量删除都触碰消息中心，但文件范围不同；若并行实现，需要最后合并检查 `/profile/messages` 与教师异步组件逻辑。
* 管理员反馈详情样式可能复用统一身份展示组件；如果先做样式任务，保留后续替换空间。

## Technical Notes

* 需检查前端：`UI/src/router`、`UI/src/views/profile`、`UI/src/views/admin`、`UI/src/views/teacher`、`UI/src/api`、用户 store。
* 需检查后端：`project_code/backend/app/api/v1/users.py`、`messages.py`、`feedbacks.py`、`schemas`、`models`、`services`、相关测试。
* 当前代码确认：`/profile/messages` 已有批量管理逻辑，学生端应可复用；但管理员会被 `MessagesPage.vue` 强制跳回 `/admin/messages`。
* 当前代码确认：教师消息中心平台通知只有单条删除，无批量选择。
* 当前代码确认：后端消息接口只有 `DELETE /messages/{message_id}`，暂无批量删除接口。
* 当前代码确认：后端 `UserResponse` 返回 `id`，前端 `UserProfile` 期望 `user_id`，这是 `admin1#undefined` 的直接风险点。
