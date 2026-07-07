# brainstorm: admin message center

## Goal

讨论并定义管理员消息中心应该如何设计：在学生和教师消息中心已有清晰分工的基础上，为管理员提供一个更贴合平台运营/平台问题处理的入口，而不是简单复用个人通知或教师消息中心。

## What I already know

* 用户认为学生和老师的消息中心目前基本没有问题。
* 用户希望管理员消息中心参考老师消息中心的设计风格。
* 用户确认：管理员消息中心主要显示用户反馈，不需要公告通知。
* 管理员视角下，学生和老师都属于“用户”。
* 管理员处理的问题应偏平台功能相关问题，而不是课程内容/学习过程问题。
* 用户倾向让 `/admin/messages` 成为管理员消息中心入口页。
* 用户倾向不再单独保留 `/admin/feedbacks` 作为主要入口页。
* 用户希望教师侧消息入口也更统一，倾向让 `/profile/messages` 成为教师消息入口的统一入口。

## Assumptions (temporary)

* 管理员消息中心更像“平台反馈处理台”，不是管理员个人收件箱。
* 老师消息中心处理的是学生发给老师/课程的反馈；管理员消息中心处理的是学生或老师发给平台的反馈。
* 如果保留公告通知，管理员更适合在后台公告/系统消息管理里创建和管理，而不是在消息中心消费公告。

## Open Questions

* None for MVP scope.

## Requirements (evolving)

* 管理员消息中心应参考教师消息中心的布局和交互风格。
* 管理员消息中心应把学生和老师提交的平台问题统一视为用户反馈。
* 管理员消息中心默认优先展示平台类反馈，包括系统 Bug、账号权限、页面异常、使用体验、功能建议等。
* 学生和老师都可以向管理员提交平台类反馈。
* 管理员保留查看课程类反馈的权限，但课程类反馈不作为管理员消息中心默认主列表；可通过筛选、次级入口或后续升级投诉场景查看。
* 管理员消息中心不包含公告通知消费列表。
* `/admin/messages` 应成为管理员消息中心入口页。
* `/admin/feedbacks` 不再作为管理员反馈处理的主要独立入口；保留为兼容旧链接的重定向入口，跳转到 `/admin/messages`。
* 管理后台菜单不再展示独立“反馈管理”入口，反馈处理聚合到“消息中心”。
* 教师侧消息入口将 `/profile/messages` 与 `/teacher/messages` 整合，减少两个消息中心并存带来的认知成本。
* `/profile/messages` 作为教师消息中心统一入口；教师登录后在该页面看到“学生反馈 + 平台通知”。
* `/teacher/messages` 保留为兼容旧链接的重定向入口，跳转到 `/profile/messages`。

## Acceptance Criteria (evolving)

* [x] 明确管理员消息中心和教师消息中心的职责边界。
* [x] 明确管理员消息中心默认展示平台类反馈，不默认展示课程类反馈。
* [x] 明确管理员保留课程类反馈查看权限。
* [x] 明确管理员消息中心 MVP 包含平台反馈主视图，并可通过筛选查看课程类反馈。
* [x] 明确用户反馈的来源、字段、状态和回复处理方式复用现有反馈模型与处理流程。
* [x] 明确 `/admin/feedbacks` 兼容策略：保留重定向到 `/admin/messages`。
* [x] 明确 `/teacher/messages` 兼容策略：保留重定向到 `/profile/messages`。

## Definition of Done (team quality bar)

* Requirements clarified and recorded.
* UI/UX scope and out-of-scope are explicit.
* Implementation plan can be derived without changing roles/API semantics accidentally.
* If implementation begins later, frontend build and relevant backend tests should be run as appropriate.

## Out of Scope (explicit)

* 当前阶段不直接实现代码。
* 不改变学生和教师消息中心的已确认体验。
* 不默认新增公告通知模块到管理员消息中心。

## Technical Notes

* Existing `/admin/messages` route exists, but current `AdminMessagePage.vue` is a send-only system message form, not a feedback/message center.
* Existing `/admin/feedbacks` route and `UI/src/views/admin/FeedbackManagePage.vue` already provide admin feedback list, filters, detail drawer, reply/process, and batch process.
* Existing feedback API already scopes admin with `admin.feedback` to all feedback, teacher to targeted course feedback, and user to own feedback.
* Existing message API is recipient-inbox oriented (`GET /messages` returns current user's messages) and is not suitable for listing all platform issues for admins without new admin endpoints.
* Feedback is the better data model for platform issues: it has status, reply, processed/replied timestamps, user identity, type (`system`/`course`), screenshots, and processing workflow.
* Messages are better for notifications/announcements: read/unread, delete, optional link, sender/recipient.
* Likely MVP can reuse admin feedback management API and reshape/admin-message-center UI rather than creating a new backend message model.
