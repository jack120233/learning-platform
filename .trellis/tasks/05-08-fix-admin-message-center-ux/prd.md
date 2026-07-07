# Fix Admin Message Center UX

## Goal

修复管理员消息中心入口和页面交互问题：管理员访问个人中心消息页时应进入新版管理员消息中心；管理员消息中心在窄屏下不能右侧大片留白或内容下坠；发送站内信表单要使用正确的用户名选择体验，并移除不需要的互动消息类型和跳转链接字段。

## What I already know

* 管理员访问 `http://127.0.0.1:3000/profile/messages` 时仍看到老版个人消息页。
* 管理员应被重定向到 `/admin/messages`。
* 管理员消息中心窄屏布局存在右侧空白、内容下坠问题。
* 发送站内信当前接收用户控件只有数字加减和“ID”字样，体验不正确。
* 发送站内信应能选择/显示正确用户名。
* 消息类型中应移除“互动消息”。
* 跳转链接字段应去掉。

## Requirements

* 管理员访问 `/profile/messages` 时重定向到 `/admin/messages`。
* 学生访问 `/profile/messages` 仍展示学生个人消息中心。
* 教师访问 `/profile/messages` 仍展示教师消息中心体验。
* 管理员消息中心在较窄浏览器宽度下布局不出现右侧大片空白或内容整体掉到下方。
* 发送站内信的接收用户应通过用户名/昵称可识别地选择，不再只展示数字 ID 加减控件。
* 发送站内信表单不展示“互动消息”类型。
* 发送站内信表单移除跳转链接字段，提交时不发送 link。
* 保留既有平台反馈列表、筛选、详情、回复处理流程。
* 更新 UI 操作日志。

## Acceptance Criteria

* [ ] 管理员访问 `/profile/messages` 会进入 `/admin/messages`。
* [ ] 教师访问 `/profile/messages` 仍看到教师消息中心。
* [ ] 学生访问 `/profile/messages` 仍看到个人消息中心。
* [ ] 管理员消息中心在窄屏下主内容不出现明显右侧空白和下坠。
* [ ] 发送站内信接收用户控件能显示用户名/昵称。
* [ ] 发送站内信消息类型不包含“互动消息”。
* [ ] 发送站内信表单没有跳转链接字段。
* [ ] 前端构建通过。
* [ ] `UI/operations-log.md` 已更新。

## Definition of Done

* Frontend route/page code updated.
* No backend changes unless existing user lookup API is missing.
* Frontend build/typecheck passes.
* UI operations log records the fix and validation.

## Out of Scope

* 不新增管理员公告/通知 inbox。
* 不改变反馈处理 API。
* 不实现批量群发站内信。
* 不重做整个后台布局。

## Technical Notes

* Likely files: `UI/src/views/profile/MessagesPage.vue`, `UI/src/views/admin/AdminMessagePage.vue`, `UI/src/api/admin.ts`, `UI/src/api/profile.ts` or user option API wrappers, `UI/operations-log.md`.
