# fix: admin profile message routing

## Goal

清理管理员侧消息与反馈个人入口，让管理员通过 `/profile/messages` 使用消息中心，管理后台不再出现独立“消息中心”。

## Requirements

* 从管理后台导航移除“消息中心”。
* `/admin/messages` 不再作为独立页面入口，重定向或合并到 `/profile/messages`。
* `/profile/messages` 不再把管理员强制跳回 `/admin/messages`。
* 管理员不显示 `/profile/feedbacks` 入口。
* 管理员直接访问 `/profile/feedbacks` 时有合理处理（推荐重定向到 `/profile/messages` 或 `/profile`）。

## Acceptance Criteria

* [ ] 管理后台侧栏没有“消息中心”。
* [ ] 管理员进入 `/profile/messages` 能看到消息中心，不跳转到 `/admin/messages`。
* [ ] 管理员看不到“我的反馈”。
* [ ] 管理员直接访问 `/profile/feedbacks` 不展示学生/普通用户反馈页。
* [ ] 前端构建或类型检查通过。

## Technical Notes

* Likely files: `UI/src/router/index.ts`, `UI/src/views/admin/AdminLayout.vue`, `UI/src/views/profile/ProfileLayout.vue`, `UI/src/views/profile/MessagesPage.vue`.
