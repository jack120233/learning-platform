# feature: student message batch delete

## Goal

确保学生个人中心消息中心支持选择多条消息并批量删除，且后续管理员/教师消息中心改造不会破坏学生端能力。

## Requirements

* 学生在 `/profile/messages` 可进入批量管理模式。
* 支持当前页全选/取消全选。
* 支持选择多条消息后批量删除。
* 批量删除前有二次确认。
* 删除后刷新消息列表、分页和未读数。
* 若当前代码已有该能力，本任务至少要做真实验证并修复发现的问题。

## Acceptance Criteria

* [ ] 学生账号进入 `/profile/messages` 能看到“批量管理”。
* [ ] 学生可勾选多条消息并批量删除。
* [ ] 无选择时不能误删。
* [ ] 删除未读消息后未读数同步减少。
* [ ] 删除当前页最后一批消息后分页状态合理。
* [ ] 前端构建或类型检查通过。

## Technical Notes

* `UI/src/views/profile/MessagesPage.vue` 当前已有非教师/非管理员消息列表的批量管理逻辑，后续需重点验证学生路径。
* 后端当前只有 `DELETE /messages/{message_id}`，学生端可继续复用单条删除并发调用，除非后续统一新增批量删除接口。
