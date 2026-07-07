# brainstorm: fix manual frontend test issues

## Goal

Fix the frontend issues found during manual testing so teacher statistics pages look more polished, teacher-only navigation/access is enforced correctly, and admin feedback management avoids unnecessary screenshot-table noise.

## What I already know

* The user manually tested the project on 2026-05-10 and reported four frontend issues.
* `/teacher/statistics/courses/2` looks too white/plain and should have a better course statistics detail presentation.
* The sentence “学生明细仅显示学生ID、用户名和学习行为指标，不展示邮箱、手机号、昵称等隐私字段。” should not appear in the user-facing page.
* Admin users should not see a top-right “课程统计” entry, and `/teacher/statistics` should not be accessible to admin users.
* `/admin/feedbacks` does not need a table column for screenshots.

## Assumptions (temporary)

* These are frontend-only fixes unless code inspection shows backend authorization changes are required.
* The teacher statistics page should remain available to teachers.
* Admin feedback screenshot details may still exist elsewhere if currently used for detail viewing; only the table column is in scope.

## Open Questions

* None.

## Requirements

* Improve the visual hierarchy/background/card presentation of the teacher course statistics detail page without changing backend APIs.
* Remove the privacy disclaimer sentence from the teacher course statistics detail page.
* Ensure admin users do not see teacher course statistics navigation in desktop dropdown or mobile drawer.
* Ensure admin users cannot enter teacher statistics routes (`/teacher/statistics` and `/teacher/statistics/courses/:courseId`).
* Remove the screenshot column from the admin feedback table while keeping feedback detail screenshot support intact if currently present.

## Acceptance Criteria

* [ ] `/teacher/statistics/courses/:id` is visually less plain/white and has improved statistics presentation.
* [ ] The privacy disclaimer sentence no longer appears on the course statistics detail page.
* [ ] Admin users do not see “课程统计” in the header/top-right navigation or mobile drawer.
* [ ] Admin users cannot access `/teacher/statistics` or `/teacher/statistics/courses/:courseId`.
* [ ] `/admin/feedbacks` table no longer shows a screenshot column.
* [ ] Frontend validation is run and reported.

## Definition of Done (team quality bar)

* Tests added/updated if appropriate.
* Lint / typecheck / build green where practical.
* Docs/notes updated if behavior changes.
* Rollout/rollback considered if risky.

## Out of Scope (explicit)

* Backend data model changes.
* Reworking the entire statistics information architecture.
* Removing screenshot support from feedback records entirely.

## Technical Approach

* Frontend-only implementation in `UI`.
* Update `CourseStatisticsDetailPage.vue` styles/template to improve visual contrast and remove the user-facing privacy disclaimer.
* Update header menu conditions in `AppHeader.vue` to show teacher statistics entries only for actual teacher users with teacher access, not admin users.
* Update `router/index.ts` with a teacher-only guard/meta for teacher statistics routes so admin users are redirected away.
* Remove only the admin feedback list screenshot column in `FeedbackManagePage.vue`; leave detail drawer image rendering unchanged.

## Decision (ADR-lite)

**Context**: The reported issues are UI polish and role-specific frontend access concerns discovered in manual testing.
**Decision**: Treat this as a small frontend-only fix with targeted route/menu/table/template changes.
**Consequences**: Backend APIs and authorization contracts stay unchanged; frontend prevents confusing admin entry points and improves teacher-facing presentation.

## Technical Notes

* Inspected `UI/src/views/teacher/CourseStatisticsDetailPage.vue`.
* Inspected `UI/src/router/index.ts`.
* Inspected `UI/src/store/user.ts`.
* Inspected `UI/src/components/layout/AppHeader.vue`.
* Inspected `UI/src/views/admin/FeedbackManagePage.vue`.
* Must update `UI/operations-log.md` because frontend files will change.
