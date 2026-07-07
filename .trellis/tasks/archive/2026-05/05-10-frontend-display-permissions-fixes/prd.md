# brainstorm: frontend display and permissions fixes

## Goal

优化管理员和个人中心的消息/反馈展示，并修复管理员从右上角误入讲师课程管理的问题，让后台入口和权限表现符合角色预期。

## What I already know

* `/admin/messages` 当前菜单里同时有“反馈管理”和“系统消息”，需要去掉重复入口，保留“系统消息”。
* `/admin/messages` 的用户反馈详情抽屉需要参考 `/admin/feedbacks` 的详情展示方式继续优化。
* `/admin/messages` 当前表格里有“截图”列，需要移除；“操作”列需要优化展示。
* `/profile/messages` 在管理员角色下展示有问题，页面内容不全；该表格里的“截图”列也需要移除，“操作”列需要优化。
* `/admin/courses` 不能再允许管理员通过右上角“课程管理”直接进入 `/teacher/courses`。
* 管理员应该通过右上角“后台管理”进入后台，再从左侧“课程管理”管理课程并获得对应授权。
* 相关前端实现集中在 `UI/src/router/index.ts`、`UI/src/components/layout/AppHeader.vue`、`UI/src/views/admin/AdminMessagePage.vue`、`UI/src/views/profile/MessagesPage.vue`、`UI/src/views/admin/FeedbackManagePage.vue`、`UI/src/store/user.ts`。

## Assumptions (temporary)

* 管理员在 `/profile/messages` 看到的是系统消息中心，而不是普通学生消息列表。
* `/admin/messages` 仍然保留“发送站内消息”能力，当前问题主要是入口重复和列表/详情展示，不是删除发消息功能。
* `/teacher/courses` 应继续对真正有讲师中心权限的账号开放，不影响普通讲师。

## Open Questions

* 无。

## Requirements (evolving)

* 保持 `/admin/messages` 的“发送站内消息”面板现状，不改动该功能和入口。
* 消除管理员后台菜单中重复的“反馈管理”入口，只保留“系统消息”。
* 优化系统消息里的用户反馈详情抽屉，使信息结构更接近 `/admin/feedbacks` 的用户反馈详情页。
* 只移除 `/admin/messages` 的“用户反馈处理台”表格中的“截图”列；图片仍保留在详情抽屉中查看。
* 重新设计两处消息列表的“操作”列，让主要操作更清晰、占用更少宽度。
* 修复管理员角色在顶部导航中误进入 `/teacher/courses` 的问题，使课程管理入口与授权路径一致。
* 管理员从“后台管理”进入后，可在后台侧边栏访问课程管理；普通教师继续使用讲师端课程管理。

## Acceptance Criteria (evolving)

* [ ] 管理员后台菜单中只显示一个反馈/消息相关入口，且“系统消息”可访问。
* [ ] `/admin/messages` 的反馈详情抽屉展示清晰，图片仍可在详情中查看。
* [ ] `/admin/messages` 与 `/profile/messages` 的表格不再显示“截图”列。
* [ ] 两个页面的“操作”列在桌面和移动端都不拥挤，主操作易于识别。
* [ ] 管理员从右上角不再直达 `/teacher/courses`，而是通过后台管理进入课程管理。
* [ ] 普通教师课程管理入口不受影响。

## Definition of Done

* 前端代码修改完成并通过构建或类型检查。
* 与权限和路由相关的变化已验证关键路径。
* `UI/operations-log.md` 已追加记录。

## Out of Scope (explicit)

* 不重做整套消息中心信息架构。
* 不修改后端接口契约，除非发现前端现有数据无法支撑展示。
* 不调整与本次三个页面无关的后台菜单结构。

## Technical Notes

* 需要优先检查的文件：`UI/src/router/index.ts`、`UI/src/components/layout/AppHeader.vue`、`UI/src/store/user.ts`、`UI/src/views/admin/AdminMessagePage.vue`、`UI/src/views/profile/MessagesPage.vue`、`UI/src/views/admin/FeedbackManagePage.vue`。
* 权限判断依赖 `useUserStore()` 和 `permissionCodes`，避免直接读 `localStorage`。
* 页面改动需要同时注意桌面与移动端布局。
* 相关前端规则见 `UI/CLAUDE.md`。
