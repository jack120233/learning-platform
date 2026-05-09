# fix: post-review profile admin teacher cleanup

## Goal

Fix the UX and behavior issues found after the previous admin/profile/message-center changes, keeping the new user identity and username-change backend capability while removing unnecessary profile exposure, restoring the intended admin message-center experience, and adding teacher-side delete management with soft-delete semantics.

## What I already know

* The previous change added username-change opportunity fields and UI hints to `/profile`.
* The user now wants `/profile` to hide the standalone “改名机会” and “注册时间” rows for all roles.
* Username edit hints should be minimal: only show `剩余 1 次修改机会` when the account currently has a change opportunity; no `提交前需要二次确认。` text.
* If the user has no username-change opportunity, the username input must be disabled and no hint should appear.
* Teachers should not be limited by username-change opportunities.
* Admins currently still see the old admin message center; the previously designed newer admin message center should be merged into the old page’s right side rather than left unused.
* Admin feedback detail drawer currently places `反馈编号 #3` where it visually conflicts with username `#id`; move that metadata elsewhere.
* Teacher message center needs single and batch delete handling under both `学生反馈` and `平台通知`; database deletion must be soft delete.
* `/admin/users` should remove the user nickname column entirely.

## Requirements

* Profile info cleanup:
  * Remove the display rows for `改名机会` and `注册时间` from `/profile` for all roles.
  * Keep username editing available when allowed, but simplify the hint to only `剩余 N 次修改机会`.
  * When a non-teacher user has no username-change opportunity, hide the hint and disable the username input.
  * Teachers must not be blocked by username-change opportunity limits in the frontend or backend.
* Admin message center:
  * Keep `/admin/messages` as the admin management route/page rather than redirecting away.
  * Merge the newer admin message-center composition into the existing admin page’s right-side/main content area.
  * Keep `/profile/messages` as the normal personal message center for non-admins.
* Admin feedback detail styling:
  * Move `反馈编号 #...` away from the current visually conflicting location.
* Teacher message center deletion:
  * `学生反馈` tab supports single delete and batch delete.
  * `平台通知` tab supports single delete and batch delete.
  * Delete operations are soft delete in the database.
* Admin user management:
  * Remove the user nickname column from `/admin/users`.

## Acceptance Criteria

* [ ] `/profile` no longer shows separate `改名机会` or `注册时间` rows.
* [ ] `/profile` username hint shows only `剩余 N 次修改机会` when applicable.
* [ ] `/profile` username input is disabled and has no hint when a non-teacher has no remaining opportunity.
* [ ] Teacher profile username editing is not limited by username-change opportunity count.
* [ ] `/admin/messages` renders the intended admin message-center UI in the admin layout main area.
* [ ] Admin feedback detail no longer shows `反馈编号 #...` next to user identity in a visually confusing way.
* [ ] Teacher `学生反馈` tab has single delete and batch delete controls, and deletion is soft delete.
* [ ] Teacher `平台通知` tab has single delete and batch delete controls, and deletion is soft delete.
* [ ] `/admin/users` no longer includes the `用户昵称` column.
* [ ] Frontend build passes.
* [ ] Backend tests for affected user/feedback/message APIs pass or are added/updated.
* [ ] `UI/operations-log.md` and `project_code/operations-log.md` are updated for actual changes.

## Definition of Done

* Implementation is complete in the correct frontend/backend subprojects.
* Validation results are recorded in the final response.
* No direct business localStorage reads are added outside the API token interceptor.
* API paths remain under `/api/v1` and responses remain `{ code, message, data }`.

## Parallelization Plan

* Batch A: profile cleanup + admin user nickname column removal + admin feedback detail metadata repositioning. Mostly frontend-only and can be done together.
* Batch B: admin message center route/page merge. Frontend-only but should avoid conflicting with Batch A edits in router/admin page files.
* Batch C: teacher feedback/platform notification delete controls + backend soft-delete endpoints/state. Fullstack and should be validated with backend tests.

## Technical Notes

* Likely frontend files: `UI/src/views/profile/ProfileInfoPage.vue`, `UI/src/router/index.ts`, `UI/src/views/admin/AdminMessagePage.vue`, `UI/src/views/admin/UserManagePage.vue`, `UI/src/views/admin/FeedbackManagePage.vue`, `UI/src/views/teacher/TeacherMessageCenterPage.vue`, `UI/src/api/teacher.ts`.
* Likely backend files: `project_code/backend/app/api/v1/feedbacks.py`, `project_code/backend/app/services/feedback_service.py`, `project_code/backend/app/models/feedback.py`, `project_code/backend/app/schemas/feedback.py`, `project_code/backend/app/api/v1/messages.py`, `project_code/backend/app/services/message_service.py` if teacher platform notices use message APIs.
* Existing prior work already introduced user identity display and username-change fields; this task adjusts exposure and role rules rather than removing the backend capability.
