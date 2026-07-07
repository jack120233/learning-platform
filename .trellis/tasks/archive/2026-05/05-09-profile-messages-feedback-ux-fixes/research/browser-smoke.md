# Research: browser smoke validation

- **Query**: Read-only browser smoke validation for `.trellis/tasks/05-09-profile-messages-feedback-ux-fixes` against running frontend/backend, checking profile/messages/feedback UX for teacher and admin.
- **Scope**: internal
- **Date**: 2026-05-09

## Findings

### Files Found

| File Path | Description |
|---|---|
| `UI/src/views/profile/ProfileInfoPage.vue` | Personal info card and role row UI. |
| `UI/src/views/profile/MessagesPage.vue` | Delegates teacher/admin profile messages to role-specific pages. |
| `UI/src/views/teacher/TeacherMessageCenterPage.vue` | Teacher feedback detail drawer, feedback list controls, username grant search UI. |
| `UI/src/views/profile/MyFeedbacksPage.vue` | Own feedback list with single and batch delete controls. |
| `UI/src/views/admin/AdminMessagePage.vue` | Admin feedback table, chat-style detail drawer, single/batch delete controls. |

### Code Patterns

- Browser smoke used Playwright/Chromium against `http://127.0.0.1:3000` and backend `http://127.0.0.1:8000`; no code or data mutations were performed.
- Teacher `/profile`: personal info section visible; role row text was `角色\n讲师`; role row had no measured overflow.
- Teacher `/profile/messages`: 2 student feedback cards found; each card had a list delete button; batch management was visible. Opening student feedback detail showed title `学生反馈详情`, chat bubbles were present, and no `删除反馈` button appeared in the detail drawer. Username grant search for `student` returned only student users with `状态：正常`; broad search `t` also returned only student users and no teacher-role results.
- Teacher `/profile/feedbacks`: 1 own feedback record found; single delete, batch management, and batch delete controls were visible.
- Admin `/profile/messages`: 1 feedback row found; row delete control, selection checkbox, and batch delete control were visible. Detail drawer title was `用户反馈详情`; chat bubbles were present; `删除反馈` was visible in the detail drawer.

### External References

- None.

### Related Specs

- `.trellis/tasks/05-09-profile-messages-feedback-ux-fixes` — target Trellis task directory for this validation.

## Caveats / Not Found

- Console captured three resource load errors: `Failed to load resource: net::ERR_CONNECTION_CLOSED`. The smoke script did not identify the exact resource from console text.
- Validation was read-only for destructive actions: delete and batch delete controls were only checked for visibility; no deletion confirmation was accepted and no delete requests were triggered.
