# brainstorm: profile messages feedback UX fixes

## Goal

Improve profile, message center, and feedback management UX across roles so personal information layout is cleaner, feedback detail pages are visually consistent, and teachers/admins can manage historical feedback/message records with single and batch deletion where appropriate.

## What I already know

* `/profile` personal information panel has messy layout under the avatar for all roles; the “角色” row looks odd.
* Teacher `/profile/messages` student feedback detail should remove the extra “删除反馈” action.
* Teacher `/profile/feedbacks` should add historical feedback management, including single delete and batch delete.
* Teacher `/profile/messages` rename-opportunity search should not return teacher users, and user status `active` should display as `正常`.
* Admin `/profile/messages` user feedback detail should visually match the teacher student feedback detail layout.
* Admin `/profile/messages` right-side user feedback processing panel should add historical-message management, including single delete and batch delete.

## Assumptions (temporary)

* Existing permission and role boundaries should remain unchanged.
* Feedback deletion should use the existing backend soft-delete model.
* Message batch deletion can continue using repeated single-message delete calls; no backend batch endpoint is needed for this task.

## Open Questions

* None.

## Requirements (evolving)

* Improve all-role personal information layout on `/profile`, especially the avatar-adjacent list and role display.
* Remove only the teacher feedback-detail drawer delete button from `/profile/messages`; keep list-card deletion and batch deletion for historical management.
* Add single and batch delete for historical submitted feedback records under `/profile/feedbacks` for all logged-in roles; users can delete their own submitted feedbacks.
* Exclude teacher-role users from teacher rename-opportunity search results in `/profile/messages`.
* Display `active` user status as `正常` in teacher rename-opportunity search results.
* Align admin user-feedback detail visual layout with teacher student-feedback detail layout.
* Add single and batch delete management for admin historical user feedback records in `/profile/messages`.

## Acceptance Criteria (evolving)

* [ ] `/profile` personal information layout is visually orderly for student, teacher, and admin roles.
* [ ] Teacher student feedback detail in `/profile/messages` no longer shows a “删除反馈” button.
* [ ] Teacher `/profile/feedbacks` supports deleting one feedback record and deleting multiple selected records.
* [ ] Teacher rename-opportunity search does not show teacher users.
* [ ] Teacher rename-opportunity search shows active status as `正常` instead of `active`.
* [ ] Admin user-feedback detail uses the same layout style as teacher student-feedback detail.
* [ ] Admin message center supports single and batch deletion of historical user-feedback/message records.
* [ ] Frontend validation/build passes for the touched frontend project.
* [ ] Backend tests pass if backend endpoints or schemas are changed.

## Definition of Done (team quality bar)

* Tests added/updated where appropriate.
* Frontend build/typecheck passes for UI changes.
* Backend pytest passes for backend behavior changes, if any.
* `operations-log.md` updated in every modified subproject.
* Role/permission boundaries remain intact.

## Out of Scope (explicit)

* Redesigning the entire profile center navigation or global layout.
* Changing authentication, role names, or permission model.
* Adding new notification channels or feedback workflow statuses beyond requested management actions.

## Decision (ADR-lite)

**Context**: `/profile/feedbacks` is the current user's submitted feedback history, while teacher/admin message centers manage feedback they receive or process.
**Decision**: Enable delete management in `/profile/feedbacks` for all logged-in roles, scoped to records submitted by the current user.
**Consequences**: Backend feedback deletion must allow submitter-owned soft deletion in addition to existing teacher/admin management deletion.

## Technical Notes

* Frontend rules inspected in `UI/CLAUDE.md`; frontend changes must update `UI/operations-log.md`.
* Backend rules inspected in `project_code/CLAUDE.md`; backend changes must update `project_code/operations-log.md`.
* Primary frontend files: `UI/src/views/profile/ProfileInfoPage.vue`, `UI/src/views/profile/MyFeedbacksPage.vue`, `UI/src/views/teacher/TeacherMessageCenterPage.vue`, `UI/src/views/admin/AdminMessagePage.vue`, `UI/src/api/profile.ts`, `UI/src/api/admin.ts`, `UI/src/api/teacher.ts`.
* Existing teacher message center already supports feedback single/batch deletion in list cards; only the detail drawer delete button should be removed.
* Existing feedback backend has `DELETE /feedbacks/{feedback_id}` and `FeedbackService.soft_delete`, but delete currently allows admin/global and teacher-targeted feedback deletion only. It does not allow the submitting user to delete their own feedback yet.
* Existing teacher rename-opportunity user search uses `fetchTeacherUsers()` → `GET /users` without role filtering; frontend can request `role: 'student'` and map status labels locally.
* Existing admin message page has feedback detail drawer and batch process, but not delete/batch delete.
* Existing message deletion uses `DELETE /messages/{message_id}` and frontend batch deletion via repeated single deletes.
