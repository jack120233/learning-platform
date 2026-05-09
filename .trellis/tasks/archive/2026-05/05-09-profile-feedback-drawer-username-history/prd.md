# brainstorm: remove feedback delete and preserve username history

## Goal

Polish the current profile and admin feedback details UX by removing a distracting delete action from the admin feedback detail drawer, hiding username history from the personal profile page, and ensuring backend username history is retained append-only rather than overwritten.

## What I already know

* Admin `/profile/messages` user feedback detail drawer currently shows a “删除反馈” button that should be removed because it is visually突兀.
* `/profile` personal information page should not display “原用户名”; that history is for database/audit record only.
* Multiple username changes should preserve all historical usernames by appending to the stored field instead of overwriting it.
* Previous task already touched `UI/src/views/admin/AdminMessagePage.vue`, `UI/src/views/profile/ProfileInfoPage.vue`, backend user profile update logic, and operations logs may need updates again.

## Assumptions (temporary)

* The admin feedback list/table delete and batch delete controls should remain; only the detail drawer delete button should be removed.
* The profile API may still return username history for internal/admin/debug use, but `/profile` UI must not show it.
* Username history can be stored in the existing `original_username` field as an appended textual history unless current code reveals a better existing format.

## Open Questions

* None.

## Requirements

* Remove the “删除反馈” button from admin `/profile/messages` user feedback detail drawer.
* Keep admin feedback list single delete and batch delete behavior unchanged.
* Remove “原用户名” display from `/profile` personal information page.
* Preserve username history in backend storage when username is changed multiple times by appending the previous current username to the existing `original_username` history instead of overwriting prior values.
* Expand/adjust backend storage compatibility so `original_username` can hold multiple historical usernames.
* Keep username change permissions and confirmation behavior unchanged.

## Acceptance Criteria (evolving)

* [ ] Admin `/profile/messages` feedback detail drawer has no “删除反馈” button.
* [ ] Admin feedback list still supports single delete and batch delete.
* [ ] `/profile` no longer displays an “原用户名” row for any role.
* [ ] Multiple username changes preserve all prior usernames in the backend `original_username`/history field.
* [ ] Relevant frontend build/typecheck passes.
* [ ] Relevant backend tests pass or are added/updated for username history append behavior.

## Definition of Done (team quality bar)

* Tests added/updated where appropriate.
* Frontend build/typecheck passes for UI changes.
* Backend pytest passes for backend behavior changes.
* `operations-log.md` updated in every modified subproject.
* No unrelated changes or commits.

## Out of Scope (explicit)

* Redesigning the admin feedback drawer beyond removing the detail delete action.
* Changing username modification limits or role-based permissions.
* Adding a new username-history UI unless explicitly requested.

## Decision (ADR-lite)

**Context**: The existing `original_username` field is exposed in API responses and currently records only the first pre-change username. The user wants this to remain database-only history and preserve all prior usernames across repeated changes.
**Decision**: Keep using `original_username` as the backend history field for now, expand it to text-like storage, and append the previous current username on each username change if it is not already the latest recorded entry.
**Consequences**: This avoids adding a new migration-heavy table, but the field becomes a delimited history string rather than a single username. Frontend `/profile` must stop rendering it.

## Technical Notes

* Inspected `UI/CLAUDE.md`; frontend changes require `UI/operations-log.md` update.
* Inspected `project_code/CLAUDE.md`; backend changes require `project_code/operations-log.md` update.
* Frontend files: `UI/src/views/admin/AdminMessagePage.vue`, `UI/src/views/profile/ProfileInfoPage.vue`, `UI/operations-log.md`.
* Backend files: `project_code/backend/app/services/user_service.py`, `project_code/backend/app/models/user.py`, `project_code/backend/app/core/db_schema.py`, `project_code/backend/app/schemas/user.py`, `project_code/backend/tests/test_users.py`, `project_code/operations-log.md`.
* Current admin feedback detail delete button is in `UI/src/views/admin/AdminMessagePage.vue` drawer action area; list row delete remains separate.
* Current profile page renders `profile.original_username` in `UI/src/views/profile/ProfileInfoPage.vue` and should remove that row only.
* Current `User.original_username` model is `String(50)` with comment “首次改名前用户名”; compatibility script adds `VARCHAR(50)`. Need expand/comment to support history.
* Current `_change_username()` only sets `original_username` if empty, so granted second changes do not append history.
