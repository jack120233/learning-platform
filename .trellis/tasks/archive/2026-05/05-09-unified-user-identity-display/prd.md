# fix: unified user identity display

## Goal

修复 `admin1#undefined` 并统一美化全站 `用户名#id` 身份展示，使 ID 作为弱化消歧标识而不是突兀正文。

## Requirements

* 修复个人信息页读取后端 `id` 与前端 `user_id` 不一致导致的 `#undefined`。
* 建立统一的前端身份展示组件或工具，避免多处手写 `username#id`。
* `username` 保持主视觉，`#id` 用 badge/浅色小号文本展示。
* 适用于个人信息、顶部用户菜单、反馈详情/列表、消息收件人选择、教师反馈等主要身份展示位置。

## Acceptance Criteria

* [ ] `/profile` 不再出现 `#undefined`。
* [ ] 主要用户身份展示位置样式一致。
* [ ] 缺失 ID 时不渲染 `undefined`，缺失用户名时仍有合理 fallback。
* [ ] 前端构建或类型检查通过。

## Technical Notes

* Existing repeated helpers appear in admin feedback, admin message, profile feedback, teacher feedback/message, AppHeader, FeedbackForm.
* Current backend `UserResponse` returns `id` not `user_id`; frontend API mapper likely needs normalization.
