# brainstorm: 公告提醒逻辑修复

## Goal

修复管理员发布公告后的未读提醒与消息列表不一致问题，确保管理员不会收到自己发布公告产生的未读公告提示，同时其他角色在公告重复发布时能看到与未读计数一致的消息记录。

## What I already know

* 管理员连续发布 4 次公告后，右上角显示 4 条公告提醒，但消息中心没有对应待阅读公告。
* 管理员不应该收到有未读公告的提醒。
* 其他角色在管理员重复发布公告后，未读数量会增加，但消息列表中没有新增重复消息内容。
* 用户期望重复发布公告也重复发送到其他用户消息列表。

## Assumptions (temporary)

* 公告发布会触发消息或未读计数生成逻辑。
* 问题可能同时涉及后端公告/消息生成逻辑和前端未读提醒展示逻辑。

## Open Questions

* 管理员是否应完全排除公告未读提醒和公告消息生成，还是仅排除自己发布的公告？

## Requirements (evolving)

* 管理员发布公告后，不应在管理员身份右上角产生无实际消息对应的未读公告提醒。
* 对非管理员用户，重复发布公告应生成重复可见消息记录，未读计数和消息列表数量应一致。

## Acceptance Criteria (evolving)

* [ ] 管理员连续发布多次公告后，管理员端未读公告提醒不增加。
* [ ] 管理员进入消息中心时，不出现未读计数与消息列表不一致。
* [ ] 学生/教师端重复发布公告后，未读计数增加几次，消息列表就出现几条对应公告消息。
* [ ] 前后端联调口径仍符合 `/api/v1`、Bearer Token、`{ code, message, data }`。

## Definition of Done (team quality bar)

* Tests added/updated where appropriate.
* Frontend typecheck/build and backend pytest按实际改动范围执行。
* 如修改前端，更新 `UI/operations-log.md`；如修改后端，更新 `project_code/operations-log.md`。
* 明确说明改动落在前端、后端还是两边。

## Out of Scope (explicit)

* 不重做整个消息中心 UI。
* 不调整公告内容编辑、发布流程以外的业务规则。

## Technical Notes

* 待检查前端：`UI/src/views/admin/AnnouncementPage.vue`、`UI/src/api/admin.ts`、消息中心相关页面/API/store、右上角提醒组件。
* 待检查后端：`project_code/backend/app/api/v1/announcements.py`、`messages.py`、相关 services/schemas/tests。
