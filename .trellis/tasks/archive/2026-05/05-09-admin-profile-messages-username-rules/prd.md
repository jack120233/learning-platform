# fix: admin profile messages and role username rules

## Goal

Fix the remaining admin profile/message-center mismatch and role-specific username-change behavior so admin uses the newer message-center experience inside `/profile/messages`, and both teacher/admin roles are exempt from username-change limits and limit hints.

## What I already know

* User verified that admin login at `http://127.0.0.1:3000/profile` still sees old message center behavior at `/profile/messages`.
* The newer admin message-center UI already exists from previous work and should be merged into the old `/profile/messages` page, similar to teacher message center style.
* Admin should not be limited by username-change opportunities.
* Admin should not see the username input hint `剩余 1 次修改机会`.
* Backend/database-facing username-change fields/rules should treat teacher/admin roles appropriately.

## Assumptions (temporary)

* `/profile/messages` is shared by roles and needs role-specific admin rendering rather than redirecting admin to `/admin/messages`.
* Teacher/admin username change should be unlimited in service logic even if `username_change_remaining` is 0/null.
* For profile API responses, `can_change_username` should be true for teacher/admin, while the frontend should suppress opportunity-count hints for those roles.

## Open Questions

* None currently blocking; inspect code first.

## Requirements

* Admin `/profile/messages` must render the newer admin message-center experience inside the existing profile message page area.
* The integrated admin message center should visually align with the teacher message center style where applicable.
* Admin and teacher profile username editing must not be blocked by `username_change_remaining`.
* Admin and teacher profile username input must not show `剩余 N 次修改机会` hints.
* Backend username-change service/schema behavior must explicitly handle teacher/admin as exempt roles.
* Update frontend/backend operation logs if files change.

## Acceptance Criteria

* [ ] Logging in as admin and visiting `/profile/messages` shows the newer admin message center, not the old personal-message list.
* [ ] Admin profile username field is editable regardless of remaining rename count.
* [ ] Admin profile does not show `剩余 1 次修改机会` under the username field.
* [ ] Teacher profile remains editable regardless of remaining rename count and shows no opportunity-count hint.
* [ ] Backend tests cover teacher/admin username-change exemption or existing tests are updated accordingly.
* [ ] Frontend build/type validation and relevant backend tests pass.

## Definition of Done

* Tests added/updated where appropriate.
* Frontend build or typecheck passes.
* Backend user/message-related tests pass.
* Browser smoke verifies admin `/profile/messages` and profile username UI.
* Operations logs updated for changed frontend/backend files.

## Out of Scope

* Reworking unrelated admin sidebar navigation.
* Changing the one-time username-change policy for student users.
* Replacing all message-center internals beyond the admin `/profile/messages` integration.

## Technical Notes

* Likely frontend files: `UI/src/views/profile/MessagesPage.vue`, `UI/src/views/admin/AdminMessagePage.vue`, `UI/src/views/teacher/TeacherMessageCenterPage.vue`, `UI/src/views/profile/ProfileInfoPage.vue`, `UI/src/router/index.ts`, `UI/src/api/*`.
* Likely backend files: `project_code/backend/app/api/v1/users.py`, `project_code/backend/app/services/user_service.py`, `project_code/backend/app/schemas/user.py`, `project_code/backend/tests/test_users.py`.
