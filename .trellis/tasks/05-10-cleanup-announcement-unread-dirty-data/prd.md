# brainstorm: 清理公告重复发布未读脏数据

## Goal

清理管理员登录后右上角显示的 4 条未读消息脏数据，并确认公告发布同步消息逻辑是否仍会把重复公告消息错误推送给管理员，避免页面继续出现误导性的未读角标。

## What I already know

* 用户反馈：管理员登录后右上角仍提示 4 条未读信息。
* 用户判断这些未读消息是之前多次重复发布公告留下的脏数据，希望清除。
* 前端 Header 未读数来自 `fetchUnreadCount()`，调用后端 `/api/v1/messages/unread-count`。
* 后端未读统计由 `message_service.get_unread_count()` 统计 `messages` 表中 `is_read = False` 且 `is_deleted = False` 的记录。
* 公告发布同步逻辑在 `project_code/backend/app/services/system_service.py` 的 `AnnouncementService._sync_messages_for_announcement()`。

## Assumptions (temporary)

* 这 4 条未读来自本地开发数据库的 `messages` 表。
* 清理目标应限定为管理员账号的公告类未读脏数据，避免删除正常学生/教师消息。
* 如果后端仍会向管理员同步公告消息，需要同步修复代码或至少记录范围。

## Open Questions

* 无阻塞问题；优先通过代码和本地数据库定位。

## Requirements

* 定位管理员未读数来源。
* 清除管理员账号中由重复发布公告产生的未读脏数据。
* 不误删正常用户消息。
* 如发现公告同步逻辑与“非管理员用户接收公告消息”口径不一致，进行最小修复。

## Acceptance Criteria

* [ ] 管理员登录后 `/messages/unread-count` 不再返回这 4 条公告脏未读。
* [ ] Header 右上角不再显示 4 条脏未读角标。
* [ ] 公告消息同步逻辑不会继续制造同类管理员脏未读。
* [ ] 后端相关测试通过或明确说明未运行原因。
* [ ] 如修改后端文件，更新 `project_code/operations-log.md`。

## Definition of Done

* Backend tests added/updated where appropriate.
* Relevant pytest passes.
* Dirty data cleanup is targeted and reversible enough to avoid broad data loss.
* Operations log updated for backend changes.

## Out of Scope

* 不重做完整消息中心产品逻辑。
* 不批量清空所有用户的所有未读消息。
* 不清理非公告类型正常消息。

## Technical Notes

* Frontend unread display: `UI/src/components/layout/AppHeader.vue` calls `fetchUnreadCount()` and stores `userStore.unreadMessageCount`.
* Frontend API: `UI/src/api/profile.ts` maps `/messages/unread-count` `total` to `unread_count`.
* Backend route: `project_code/backend/app/api/v1/messages.py` `GET /messages/unread-count`.
* Backend service: `project_code/backend/app/services/message_service.py` counts unread undeleted messages.
* Announcement sync: `project_code/backend/app/services/system_service.py` creates `Message(type='announcement', link='/announcements/{id}')` records.
