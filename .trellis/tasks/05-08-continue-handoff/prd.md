# Optimize Teacher Feedback Detail Chat Layout

## Goal

优化教师查看学生反馈详情时的阅读体验，将反馈内容和教师回复从居中的信息块展示改为类似微信/IM 的两人对话气泡，让教师更直观地区分学生反馈与自己的回复，同时保持现有反馈处理流程、API 和响应式适配不变。

## What I already know

* 用户已确认目标是优化教师角色查看学生反馈详情的页面展示方式。
* 学生反馈内容应靠左展示，老师回复内容应靠右展示。
* 学生反馈气泡显示反馈人的学生用户名，老师回复气泡显示当前登录老师的用户名/昵称。
* 每一条反馈/回复内容都要带时间。
* 图片继续跟随学生反馈展示并保留预览能力。
* 未处理反馈不展示空的老师回复气泡，只保留现有“回复并处理”动作。
* 现有反馈处理流程、API 和刷新逻辑不应改变。
* 这是前端任务，主要修改 `UI/src/views/teacher/TeacherMessageCenterPage.vue`，并视一致性同步 `UI/src/views/teacher/FeedbackManagePage.vue`。
* `UI/CLAUDE.md` 要求业务代码不得直接读取 `localStorage`，登录态和用户信息必须通过 `useUserStore()` 获取。
* 只要 UI 文件发生实际变更，必须更新 `UI/operations-log.md`。

## Assumptions

* 本任务不修改后端接口、数据模型或响应字段。
* 教师侧显示名以当前登录教师为准，而不是反馈目标字段。
* 老教师课程反馈管理页与新教师消息中心入口应保持详情展示一致，避免同一业务入口体验割裂。

## Requirements

* 教师消息中心 `/teacher/messages` 的学生反馈详情 drawer 使用对话流展示反馈主体。
* 学生反馈以左侧气泡展示。
* 学生气泡显示学生用户名和反馈提交时间。
* 学生侧名称优先使用 `currentFeedback.username`，兜底 `用户${currentFeedback.user_id}`。
* 学生截图跟随学生反馈气泡展示，并保留 `el-image` 预览能力。
* 教师回复仅在 `currentFeedback.reply` 存在时展示为右侧气泡。
* 教师气泡显示当前登录教师的昵称或用户名，来源为 `useUserStore().userInfo.nickname || useUserStore().userInfo.username`。
* 教师回复时间优先使用 `currentFeedback.replied_at`，没有则使用 `currentFeedback.processed_at`。
* 气泡内容支持换行和长文本自动换行，避免横向溢出。
* PC 端气泡最大宽度约 72%，移动端最大宽度约 86%。
* 保持现有详情元信息、处理 dialog、回复处理按钮、刷新逻辑、筛选搜索分页逻辑不变。
* 同步将 `UI/src/views/teacher/FeedbackManagePage.vue` 的反馈详情 drawer 调整为一致的对话式样式。
* 前端变更完成后追加 `UI/operations-log.md`。

## Acceptance Criteria

* [ ] 教师在 `/teacher/messages` 打开学生反馈详情时，学生反馈靠左显示。
* [ ] 学生反馈气泡显示学生用户名和反馈提交时间。
* [ ] 有截图的学生反馈仍能在详情中查看并预览截图。
* [ ] 已处理反馈中，教师回复靠右显示。
* [ ] 教师回复气泡显示当前登录教师用户名/昵称和回复时间。
* [ ] 未处理反馈不显示空教师回复气泡，并仍可点击“回复并处理”。
* [ ] 老教师课程反馈管理页的详情 drawer 与消息中心反馈详情展示一致。
* [ ] 移动端宽度下气泡和图片无横向溢出。
* [ ] 未新增后端变更，API 调用路径和响应字段读取保持不变。
* [ ] `npm run build` 通过，或明确记录未执行原因。
* [ ] `UI/operations-log.md` 已追加本次前端变更记录。

## Definition of Done

* Tests/build/typecheck appropriate to the frontend change are run or skipped with a clear reason.
* UI operations log is updated because frontend files change.
* Existing feedback processing flow remains unchanged.
* Responsive behavior is checked at the CSS/code level and, if feasible, in a browser.

## Technical Approach

Implement the chat layout in-place in the existing teacher feedback detail drawers instead of adding a shared component. Add a `teacherDisplayName` computed value from `useUserStore()` in each page that renders the teacher reply. Replace the current `rich-content` / `reply-box` / `feedback-content` / `reply-content` blocks with a `.feedback-chat` structure containing left/right `.chat-message` rows and `.chat-bubble` content. Keep detail metadata and action areas in their existing positions.

## Decision (ADR-lite)

**Context**: Two teacher-facing entry points show feedback details using block-style content, while the user wants an IM-like conversation reading experience.

**Decision**: Update both `TeacherMessageCenterPage.vue` and `FeedbackManagePage.vue` in-place with matching chat-style markup and scoped styles, using Pinia user store for the teacher display name.

**Consequences**: This avoids a new abstraction for a small two-page UI change, keeps behavior local and easy to review, and duplicates a modest amount of page-specific style. If more pages later require feedback conversation rendering, a shared component can be extracted then.

## Out of Scope

* Do not modify backend feedback APIs, schemas, services, or tests.
* Do not modify the student “我的反馈” page.
* Do not change feedback submit, process, filter, search, pagination, or refresh logic.
* Do not add a global store or new dependency.
* Do not directly read `localStorage` in business components.
* Do not redesign the entire teacher message center or feedback management page.

## Technical Notes

* Main file: `UI/src/views/teacher/TeacherMessageCenterPage.vue`.
* Consistency file: `UI/src/views/teacher/FeedbackManagePage.vue`.
* User store: `UI/src/store/user.ts` exposes `userInfo.nickname` and `userInfo.username`.
* Frontend rules: `UI/CLAUDE.md` requires Pinia as auth single source and `UI/operations-log.md` update for UI changes.
* Handoff source: `/Users/jacob/Developer/a3.learn_platform/learning-platform/handoff.md`.
