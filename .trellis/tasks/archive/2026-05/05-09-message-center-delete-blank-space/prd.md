# fix: message center delete leaves blank space

## Goal

Fix the message center deletion experience so that when a user deletes historical messages, the visible list compacts immediately without leaving stale blank space, and pagination remains correct across student and other role message-center entry points.

## What I already know

* Student user can reproduce at `http://127.0.0.1:3000/profile/messages` after deleting a message.
* After deletion, the area previously occupied by the deleted message remains as a large blank block.
* Deleting multiple messages appears to accumulate multiple blank blocks.
* The user is concerned pagination may become worse when messages span pages.
* We need to check whether teacher/admin or other role message centers share the same behavior.

## Assumptions (temporary)

* The issue is likely in the frontend list rendering, delete-state update, transition/animation, virtual list, or pagination refresh logic.
* Student and other roles may share the same profile messages component or API, so a single fix may cover all roles.

## Open Questions

* Confirm whether the MVP should only fix deletion compaction and pagination, or also improve related message-center delete UX such as loading/empty-state behavior if discovered.

## Requirements (evolving)

* Deleting a message removes its visual row/card and its occupied space immediately after successful deletion.
* Repeated deletions do not accumulate blank space.
* Pagination state remains coherent after deletion, including page counts and current page behavior.
* The fix applies to all roles that use the same message-center/history deletion flow.

## Acceptance Criteria (evolving)

* [ ] Student message center deletion compacts the list with no blank region left behind.
* [ ] Repeated deletion of multiple messages leaves no accumulated blank space.
* [ ] If deletion changes page contents, the list refreshes or reflows without stale items or empty pages.
* [ ] Shared message-center behavior for other roles is checked and fixed if affected.
* [ ] Frontend validation is run or the reason it could not be run is documented.

## Definition of Done (team quality bar)

* Tests added/updated where appropriate.
* Lint / typecheck / build green where practical for the touched package.
* Docs/notes updated if behavior changes.
* Rollout/rollback considered if risky.

## Out of Scope (explicit)

* Redesigning the full message center UI.
* Changing message API contracts unless the frontend bug is caused by a backend contract issue.
* Adding unrelated message features.

## Technical Notes

* Task created from user-reported bug on 2026-05-09.
* Need inspect frontend message center files under `UI/src/views/profile`, related API/store/router files, and possibly admin/teacher message center routes.
