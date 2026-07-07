# brainstorm: 修复右上角用户名显示

## Goal

修复登录后页面右上角用户区域显示错误的问题：不再使用用户昵称，统一参考个人中心的身份展示方式，显示为用户名与用户 ID（用户名#id）。

## What I already know

* 用户明确要求当前和未来都不再使用用户昵称，只使用“用户名#id”。
* 个人中心 `UI/src/views/profile/ProfileInfoPage.vue` 已使用 `UserIdentity` 组件展示当前用户名。
* `UI/src/components/common/UserIdentity.vue` 负责将 username 和 userId 展示为用户名 + #id，并通过 `formatUserIdentity` 生成 title 文案。
* `UI/src/components/layout/AppHeader.vue` 当前右上角和移动端抽屉仍使用 `userStore.userInfo.nickname || userStore.userInfo.username`，这是显示错误来源。

## Requirements

* 登录后的桌面端右上角用户名称使用 `userStore.userInfo.username` 与 `userStore.userInfo.userId` 展示。
* 登录后的移动端用户信息同样使用 `userStore.userInfo.username` 与 `userStore.userInfo.userId` 展示。
* 不再在 Header 用户显示中读取或回退到 `nickname`。
* 展示样式尽量复用个人中心现有 `UserIdentity` 组件，保持身份格式一致。

## Acceptance Criteria

* [ ] 桌面端 Header 用户区域显示用户名和用户 ID，不显示昵称。
* [ ] 移动端 Header 抽屉用户区域显示用户名和用户 ID，不显示昵称。
* [ ] 个人中心现有用户名显示不被破坏。
* [ ] 前端类型检查或构建通过。

## Definition of Done

* Tests added/updated where appropriate.
* Frontend typecheck/build passes or failure is documented.
* Frontend operations log updated because UI files changed.

## Out of Scope

* 本次不清理所有 API schema 中遗留的 nickname 字段。
* 本次不调整后端用户模型或登录响应结构。
* 本次不改变用户身份组件的视觉设计。

## Technical Notes

* Impacted file: `UI/src/components/layout/AppHeader.vue`.
* Reference implementation: `UI/src/views/profile/ProfileInfoPage.vue` uses `<UserIdentity :username="profile.username" :user-id="profile.user_id" fallback="用户" />`.
* Reusable component: `UI/src/components/common/UserIdentity.vue`.
* Existing formatter: `UI/src/utils/format.ts` `formatUserIdentity()` returns `username#id` string for title/string-only contexts.
