# feature: teacher message batch delete

## Goal

为老师消息中心的平台通知列表补齐选择与批量删除能力。

## Requirements

* 老师消息中心“平台通知”支持进入批量管理模式。
* 支持当前页全选/取消全选。
* 支持选择多条通知后批量删除。
* 批量删除后刷新列表和未读统计。
* 若采用现有单条删除 API 并发删除，应处理部分失败提示；若新增后端批量接口，需要补后端测试。

## Acceptance Criteria

* [ ] 老师可勾选多条平台通知。
* [ ] 批量删除前有确认弹窗。
* [ ] 删除后列表、分页和未读数更新正确。
* [ ] 无选择时按钮禁用或提示。
* [ ] 前端构建或类型检查通过；如新增后端接口，后端 pytest 通过。

## Technical Notes

* `UI/src/views/profile/MessagesPage.vue` 已有批量管理逻辑，可复用交互模式。
* `UI/src/views/teacher/TeacherMessageCenterPage.vue` 当前只有单条删除。
* 后端当前只有 `DELETE /messages/{message_id}`，无批量删除接口。
