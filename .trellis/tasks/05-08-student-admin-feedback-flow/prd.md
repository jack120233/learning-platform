# Student to Admin Feedback Flow

## Goal

实现并验证学生提交平台反馈给管理员后，管理员能在管理员消息中心查看、回复并处理，学生能在自己的反馈页面看到管理员回复的完整闭环。

## What I already know

* 管理员消息中心已被定义为 `/admin/messages`，默认处理平台类用户反馈。
* `/admin/feedbacks` 应重定向到 `/admin/messages`。
* 平台类反馈使用现有反馈模型 `feedback_type/type = system`。
* 学生提交平台反馈后，管理员应能看到并回复处理。
* 学生应能在“我的反馈”页面看到管理员回复和处理状态。
* 需要检查前后端是否已经打通；如有缺口则修复。

## Assumptions

* 本任务优先复用现有反馈 API，不新增消息表或新通知 API。
* “提交给管理员”的平台反馈不需要 `course_id` 或 `target_user_id`。
* 管理员回复处理后，反馈状态变为 `processed`，回复字段回流给学生端。

## Open Questions

* None for MVP scope.

## Requirements

* 学生可以提交平台类反馈给管理员。
* 平台类反馈提交时不能被课程反馈必填项阻塞。
* 管理员进入 `/admin/messages` 默认能看到待处理/全部平台类反馈。
* 管理员可以打开平台反馈详情，看到提交学生、内容、截图、时间、状态。
* 管理员可以回复并处理该反馈。
* 管理员处理后列表/详情状态更新。
* 学生在自己的反馈页面能看到该反馈已处理，并看到管理员回复内容和时间。
* `/admin/feedbacks` 继续重定向到 `/admin/messages`。
* 不破坏学生/老师现有消息中心和课程反馈流程。

## Acceptance Criteria

* [ ] 学生账号能成功提交 `system` 平台反馈。
* [ ] 管理员账号在 `/admin/messages` 默认列表能看到该平台反馈。
* [ ] 管理员能查看该反馈详情。
* [ ] 管理员能填写回复并处理成功。
* [ ] 处理后管理员侧状态变为已处理，并展示回复。
* [ ] 学生在 `/profile/feedbacks` 能看到该反馈已处理和管理员回复。
* [ ] `/admin/feedbacks` 重定向到 `/admin/messages`。
* [ ] 前端构建通过。
* [ ] 相关后端反馈测试通过或补齐。
* [ ] UI 和后端 operations log 按实际变更更新。

## Definition of Done

* Frontend and backend code paths inspected.
* Missing integration gaps fixed.
* Frontend build/typecheck passes.
* Relevant backend pytest passes if backend files are changed.
* Browser/API validation covers student submit → admin reply → student view reply.
* Operations logs updated for changed subprojects.

## Out of Scope

* 不新增管理员通知 inbox。
* 不新增消息表驱动的反馈流程。
* 不改变课程反馈给老师的既有流程。
* 不实现复杂工单升级、分派、催办或通知推送。

## Technical Notes

* Likely frontend files: `UI/src/components/feedback/FeedbackForm.vue`, `UI/src/components/feedback/FeedbackDialog.vue`, `UI/src/views/admin/AdminMessagePage.vue`, `UI/src/views/profile/MyFeedbacksPage.vue`, `UI/src/api/*`, `UI/operations-log.md`.
* Likely backend files: `project_code/backend/app/api/v1/feedbacks.py`, `project_code/backend/app/services/feedback_service.py`, `project_code/backend/app/schemas/feedback.py`, `project_code/backend/tests/test_feedbacks.py`, `project_code/operations-log.md`.
* Use seeded accounts for validation: `student1` / `Test123456`, `admin1` / `Admin123456`.
