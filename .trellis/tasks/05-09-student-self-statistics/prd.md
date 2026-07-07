# Student Self-Statistics

## Goal

Replace the student personal-center “学习记录” content area with a new “学习统计” page that combines personal learning overview, growth feedback, daily trend, course distribution, and the existing visible learning-record list. This task must build on the completed `05-09-learning-statistics-foundation` instead of redefining learning duration, course completion, or deletion semantics.

## Foundation Baseline

The first subtask `05-09-learning-statistics-foundation` is completed. Its `task.json` notes record that the implementation was validated in the working tree with backend targeted tests passing, frontend build passing, `compileall` passing, and `git diff --check` passing.

Confirmed foundation capabilities now available:

* Backend `POST /api/v1/learning/sessions` exists and records analytics session facts without updating progress snapshots.
* Backend `learning_sessions`, `learning_progress`, `learning_record_entries`, `student_daily_learning_stats`, `student_course_daily_stats`, `course_daily_learning_stats`, and `platform_daily_learning_stats` models exist.
* `learning_progress` is formalized as the user-course summary with course progress, last resource, last learn time, and first `completed_at` semantics.
* `learning_record_entries` backs visible learning records, while hidden/deleted records stay hidden and later learning creates a new visible row.
* `GET /api/v1/users/me/learning-records` already reads visible `learning_record_entries` first, with a legacy fallback only when no visible entries exist on the first page.
* `POST /api/v1/users/me/learning-records/delete` already accepts `{ "record_ids": [...] }`, validates all IDs as current-user visible records, and hides rows without deleting progress/statistics.
* `learning_statistics_service.aggregate_date()` / `aggregate_range()` can rebuild daily aggregate tables and filters aggregate data to `student` users.
* Frontend learning-session collection and required-resource support were included in the foundation task.

Implication for this task: do not rebuild session collection, record-entry semantics, required-resource completion, or aggregate table infrastructure. This task should add student-facing statistics read APIs and replace the profile UI.

## Requirements

### 1. Student-only statistics APIs

Add student personal statistics endpoints under the existing learning API namespace:

* `GET /api/v1/learning/statistics/me/overview`
* `GET /api/v1/learning/statistics/me/trend?range=7d|30d`
* `GET /api/v1/learning/statistics/me/course-distribution`

Authorization rules:

* Only `student` role can call these endpoints.
* `teacher` and `admin` receive 403.
* Endpoints never accept a `user_id`; they always use the authenticated current user.

Response format must remain the project standard `{ code, message, data }`.

### 2. Overview metrics

`GET /api/v1/learning/statistics/me/overview` returns:

* `total_duration_seconds` — total accepted effective duration for the current student.
* `last_7_days_duration_seconds` — total accepted effective duration over the last 7 natural days including today.
* `learning_course_count` — courses started but not completed.
* `completed_course_count` — courses with `learning_progress.completed_at` set.
* `continuous_learning_days` — consecutive active natural days ending today if today is active, otherwise ending at the latest active day.
* `active_learning_days` — number of natural days where the student has positive effective learning duration.

Data source preference:

* Use `learning_sessions` as the source of truth for total duration and active days.
* Use `student_daily_learning_stats` for historical daily duration when rows exist.
* Include current-day session facts directly so the student page is timely even before the daily aggregation script runs.
* Use `learning_progress` for learning/completed course counts.
* Count only the current student; role check ensures the current user is a student.

### 3. Trend metrics

`GET /api/v1/learning/statistics/me/trend?range=7d|30d` returns:

* `range`
* `items: [{ date, duration_seconds }]`

Rules:

* Default range is `7d`.
* Allowed ranges are only `7d` and `30d`; invalid values should fail validation.
* Missing dates must be filled with `duration_seconds = 0`.
* Dates use natural days consistently with the foundation aggregation service.
* Include current-day realtime sessions if aggregate rows for today are absent or stale enough that direct session supplement is needed.

### 4. Course distribution

`GET /api/v1/learning/statistics/me/course-distribution` returns:

* `learning_count`
* `completed_count`

Rules:

* Count only courses the current student has started, using `learning_progress`.
* Completed means `completed_at IS NOT NULL`.
* Learning means started and not completed.
* Do not include not-started courses.

### 5. Learning record list remains inside the new statistics page

The existing learning-record list stays available, but as a section inside the new “学习统计” page rather than a standalone old page.

Rules:

* Continue using `GET /api/v1/users/me/learning-records`.
* Continue using `POST /api/v1/users/me/learning-records/delete` for both single and batch delete.
* Single delete sends `{ "record_ids": [id] }`.
* Batch delete sends `{ "record_ids": [id1, id2] }`.
* Any invalid, hidden, or non-owned record ID makes the delete request fail as a whole.
* Delete hides display records only and must not affect `resource_progress`, `learning_progress`, `learning_sessions`, aggregate stats, or continue-learning data.
* If the same course is learned again after deletion, the foundation must create a new visible record and leave the old hidden record unchanged.
* Keep existing time filters: recent 7 days, recent 30 days, all.
* Default page size remains 10.
* Continue-learning remains available for published courses; archived courses remain visible but cannot continue.

### 6. Frontend profile replacement

Replace the personal-center menu/content label from “学习记录” to “学习统计”.

Recommended frontend behavior:

* Keep route path `/profile/records` for compatibility unless there is a strong reason to rename. Change route/menu title and component display name/title to “学习统计”.
* Replace or refactor `UI/src/views/profile/LearningRecordsPage.vue` into a statistics page that includes the record list section.
* The page top shows overview cards:
  * 总学习时长
  * 近 7 天学习时长
  * 在学课程数
  * 已完成课程数
* Growth feedback shows:
  * 连续学习天数
  * 累计活跃天数
* Trend chart section defaults to 7 days and can switch to 30 days.
* Course distribution shows only “学习中 / 已完成”. Do not show not-started courses.
* Learning records appear below the statistics sections.
* Batch delete uses list checkboxes and a selected-count action area.
* Single delete should reuse the same backend delete endpoint.
* After successful delete, remove rows from the current UI and refresh the current page if needed. If the current page becomes empty, prefer refreshing the current page and allowing pagination to settle rather than inventing complex client-side page correction.
* No nickname should appear in this page, API responses, tables, or export-like content.

### 7. Mobile adaptation

The student “学习统计” page requires full mobile adaptation:

* Overview cards wrap cleanly on tablet/mobile.
* Trend section fits small screens without horizontal overflow.
* Course distribution remains readable on mobile.
* Learning record list should become card-like or compact on small screens.
* Batch selection and delete actions must remain usable on mobile.
* PC layout should remain the primary/default layout.

## Acceptance Criteria

### Backend acceptance

* [ ] Student overview API returns total duration, last 7 days duration, learning/completed course counts, continuous days, and active days.
* [ ] Student trend API returns 7d/30d daily duration with missing dates filled as 0.
* [ ] Student distribution API returns learning/completed course counts only.
* [ ] Student statistics APIs reject teacher/admin with 403.
* [ ] Student statistics APIs do not accept arbitrary user IDs.
* [ ] Statistics duration uses the foundation session/aggregate口径 and does not redefine progress-derived duration.
* [ ] Current-day learning can appear without waiting for the next manual aggregate run.
* [ ] Existing learning-record delete endpoint still accepts single and batch array payloads.
* [ ] Any invalid/non-owned/hidden record ID makes delete fail as a whole.
* [ ] Deleting records does not affect progress, sessions, statistics, or continue-learning.

### Frontend acceptance

* [ ] Personal-center menu label changes from “学习记录” to “学习统计”.
* [ ] The student statistics page shows overview cards, growth feedback, trend, course distribution, and learning-record list.
* [ ] Trend defaults to 7 days and can switch to 30 days.
* [ ] Course distribution shows only learning/completed courses.
* [ ] Learning-record list keeps time filters, pagination size 10, and continue-learning action.
* [ ] Single and batch delete call `POST /api/v1/users/me/learning-records/delete` with `record_ids` array.
* [ ] Successful delete updates the visible list without affecting statistics totals.
* [ ] Empty state guides the student to browse courses.
* [ ] PC and mobile layouts have no obvious horizontal overflow or broken controls.

### Validation acceptance

* [ ] Backend targeted tests pass, including learning statistics and record deletion tests.
* [ ] Frontend build passes in `UI`.
* [ ] If frontend typing is substantially changed, `npx vue-tsc -b` passes.
* [ ] Browser validation is performed as student on the personal-center statistics page for PC and mobile viewport.
* [ ] Backend `project_code/operations-log.md` is updated if backend files change.
* [ ] Frontend `UI/operations-log.md` and API docs are updated if frontend files/API contracts change.

## Technical Approach

### Backend implementation plan

1. Add student statistics schemas, likely in `project_code/backend/app/schemas/learning.py` or a new focused schema module if existing learning schemas become too broad:
   * `StudentStatisticsOverviewResponse`
   * `StudentStatisticsTrendResponse`
   * `StudentStatisticsTrendItem`
   * `StudentCourseDistributionResponse`

2. Add service methods, preferably in `project_code/backend/app/services/learning_statistics_service.py` because this file already owns student daily aggregate models:
   * `get_student_overview(db, user_id)`
   * `get_student_trend(db, user_id, range)`
   * `get_student_course_distribution(db, user_id)`
   * A small role guard helper can live in route/service, but follow existing permission style.

3. Add routes in `project_code/backend/app/api/v1/learning.py`:
   * `GET /learning/statistics/me/overview`
   * `GET /learning/statistics/me/trend`
   * `GET /learning/statistics/me/course-distribution`

4. Use the completed foundation instead of new tables:
   * `LearningSession` for source-of-truth duration and today supplement.
   * `StudentDailyLearningStats` for daily rows.
   * `LearningProgress` for course status distribution and counts.
   * Existing `LearningRecordEntry`/`users.py` delete/list routes for records.

5. Add/extend backend tests:
   * Put statistics API tests in `project_code/backend/tests/test_learning.py` unless the file becomes too large.
   * Extend `project_code/backend/tests/test_users.py` only for record delete/list behavior if existing tests live there.
   * Cover student success, teacher/admin 403, 7d/30d trend zero filling, distribution, current-day sessions, and delete all-or-nothing behavior.

### Frontend implementation plan

1. Add API types/functions, preferably in `UI/src/api/learning.ts` because the endpoints are under `/learning/statistics/me/*`:
   * `fetchMyLearningStatisticsOverview()`
   * `fetchMyLearningStatisticsTrend(range)`
   * `fetchMyLearningCourseDistribution()`

2. Update profile record API types in `UI/src/api/profile.ts`:
   * Add `id`, `progress`, `total_duration`, `completed_at`, `created_at`, `updated_at` to `LearningRecordItem` if the UI needs them.
   * Add `deleteLearningRecords(recordIds: number[])` for the existing delete endpoint.

3. Replace/refactor `UI/src/views/profile/LearningRecordsPage.vue`:
   * Rename internal title to “学习统计”.
   * Fetch overview/trend/distribution and records.
   * Render top cards, growth feedback, trend, distribution, and record list.
   * Add single/batch delete controls.
   * Keep existing continue-learning behavior.

4. Update navigation metadata:
   * `UI/src/views/profile/ProfileLayout.vue` menu title from “学习记录” to “学习统计”.
   * `UI/src/router/index.ts` route meta title from “学习记录” to “学习统计”.
   * Keep route name/path unless implementation discovers a concrete conflict.

5. Responsive styling:
   * Use scoped SCSS and existing responsive conventions.
   * Avoid introducing a chart library unless already available or clearly justified. For MVP, a lightweight CSS bar trend is acceptable if no charting dependency exists.

## Decision (ADR-lite)

**Context**: The completed foundation already owns learning session facts, aggregate tables, course progress summary, visible learning records, and deletion semantics. The student task should not duplicate those responsibilities.

**Decision**: Implement this subtask as a thin student-facing statistics/read-model layer plus UI replacement. Backend adds student-only read APIs over foundation tables/session facts; frontend replaces the old record-only page with a statistics dashboard that embeds the existing visible record list.

**Consequences**: This keeps the second task smaller and lower-risk. It also means charting/UI may be simple in MVP, while metric correctness remains centralized in the foundation. Any deficiencies found in foundation behavior should be fixed in the foundation services rather than reworked locally in the student page.

## Out of Scope

* Teacher course statistics.
* Admin platform statistics.
* Teacher/admin course-statistics authorization.
* CSV export.
* Advanced resource diagnosis, heatmaps, seek/pause analytics, predictions, or recommendations.
* Rebuilding learning-session collection.
* Rebuilding aggregate table infrastructure or schedulers.
* Destructive cleanup of old learning behavior data.
* Showing not-started course distribution.
* Using nickname in student statistics UI or API contracts.

## Technical Notes

* Parent PRD source: `.trellis/tasks/05-09-student-learning-analytics/prd.md`.
* Foundation PRD source: `.trellis/tasks/05-09-learning-statistics-foundation/prd.md`.
* Confirmed backend route for record list/delete: `project_code/backend/app/api/v1/users.py`.
* Confirmed backend record list/delete service: `project_code/backend/app/services/user_service.py`.
* Confirmed backend aggregate service: `project_code/backend/app/services/learning_statistics_service.py`.
* Confirmed old frontend page to replace/refactor: `UI/src/views/profile/LearningRecordsPage.vue`.
* Confirmed frontend profile menu: `UI/src/views/profile/ProfileLayout.vue`.
* Confirmed frontend profile route metadata: `UI/src/router/index.ts`.
* Confirmed current `UI/src/api/profile.ts` lacks delete wrapper and has an incomplete `LearningRecordItem` type compared with backend response.
* `project_code/CLAUDE.md` requires updating `project_code/operations-log.md` when backend files change.
* `UI/CLAUDE.md` requires updating `UI/operations-log.md`, and API docs when frontend API contracts change.

## Validation Plan

Backend, from `project_code/backend`:

* `pytest tests/test_learning.py -v`
* `pytest tests/test_users.py -v` if learning-record delete/list tests are touched.

Frontend, from `UI`:

* `npm run build`
* `npx vue-tsc -b` if build does not already cover type checking or if API types are substantially changed.

Browser validation:

* Start backend and frontend dev servers.
* Login as `student1` / `Test123456`.
* Open `/profile/records` and verify the menu/title shows “学习统计”.
* Verify overview cards, trend switch, distribution, records, pagination, continue-learning, single delete, and batch delete.
* Verify teacher/admin users cannot call student statistics APIs; UI does not need to expose a student statistics personal page to them beyond profile route behavior already present.
* Check one desktop viewport and one mobile viewport for layout issues.
