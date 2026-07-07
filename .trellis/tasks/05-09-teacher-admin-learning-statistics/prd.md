# Teacher and Admin Learning Statistics

## Goal

Implement teacher course statistics, course statistics authorization, and admin platform learning statistics on top of the completed shared learning analytics foundation and completed student self-statistics task. This task must consume the existing learning session facts, course progress summaries, visible record semantics, and aggregate tables instead of redefining learning duration, course completion, or student personal statistics.

## Baseline from Completed Subtasks

### Completed `05-09-learning-statistics-foundation`

Confirmed available foundation capabilities:

* `POST /api/v1/learning/sessions` records analytics session facts separately from progress snapshots.
* `learning_sessions` is the source-of-truth fact table for effective learning duration.
* `learning_progress` is formalized as the user-course summary, including course progress, last resource, last learn time, and first `completed_at` semantics.
* `learning_record_entries` backs visible student learning records; hidden rows stay hidden and later learning creates a new visible row.
* Aggregate models/tables exist for:
  * `student_daily_learning_stats`
  * `student_course_daily_stats`
  * `course_daily_learning_stats`
  * `platform_daily_learning_stats`
* `learning_statistics_service.aggregate_date()` / `aggregate_range()` rebuild daily aggregates and filter aggregate data to `student` users.
* `Resource.is_required` and required-resource course completion semantics are already part of the foundation.
* Frontend learning-session collection and required-resource support exist in the learning/resource flow.

Implication for this task: do not rebuild learning session collection, progress snapshot saving, required-resource completion, visible record deletion semantics, or aggregate table infrastructure. Add teacher/admin read models, authorization, routes, pages, and exports on top.

### Completed `05-09-student-self-statistics`

Confirmed student-side capabilities:

* Student-only statistics APIs exist under `/api/v1/learning/statistics/me/*`.
* Personal-center “学习统计” page replaces the old standalone “学习记录” content while embedding the visible record list.
* Single and batch record deletion are validated against real learning records and follow append-after-hide semantics.
* Browser validation passed for desktop and mobile, including no horizontal overflow.

Implication for this task: student personal statistics page/API is out of scope. Teacher/admin pages may link conceptually to shared metrics but must not reuse student-only endpoints or accept arbitrary student user IDs.

## Current Repo Findings for This Task

Backend findings:

* `project_code/backend/app/services/learning_statistics_service.py` already owns aggregate rebuilding and student self-statistics read helpers.
* `project_code/backend/app/api/v1/learning.py` currently exposes student self-statistics under `/learning/statistics/me/*` and should not become the teacher/admin route dumping ground unless route ownership stays clear.
* `project_code/backend/app/api/v1/router.py` currently mounts `courses`, `learning`, `users`, and other existing routers; no teacher/admin learning statistics router exists yet.
* `project_code/backend/app/models/course.py` has `Course.teacher_id` as the owner/primary teacher field, but no course statistics authorization model yet.
* `project_code/backend/app/services/course_service.py` currently restricts course manage/publish/delete to course ownership and already validates required resources on publish.
* `project_code/backend/app/services/permission_service.py` seeds admin/teacher permissions; admin sidebar route permissions currently do not include a dedicated learning-statistics permission.
* `project_code/backend/app/api/v1/courses.py` owns course management and is a plausible place for admin course statistics authorization routes, but statistics read APIs should be separated for clarity if adding a new router.
* Tests for the touched backend areas should extend `tests/test_learning.py`, `tests/test_courses.py`, `tests/test_users.py`, and possibly `tests/test_system.py` depending on permission seeding changes.

Frontend findings:

* `UI/src/components/layout/AppHeader.vue` owns the right-top avatar dropdown and mobile user menu. It currently shows “我的学习”, “课程管理”, and “后台管理”. This is the target for the teacher-only “课程统计” entry.
* `UI/src/router/index.ts` currently has `/teacher` children for courses, create/edit, and feedbacks; no teacher statistics routes exist.
* `UI/src/views/teacher/TeacherLayout.vue` is currently a thin wrapper around `router-view`, so the teacher statistics entry can come from the global avatar menu rather than a teacher sidebar.
* `UI/src/views/admin/AdminLayout.vue` owns admin sidebar/mobile drawer items and filters them by permission code. This is the target for the admin “学习统计” entry.
* `UI/src/router/index.ts` admin children currently include users, teacher audits, announcements, feedbacks, messages, categories, and tags. No admin learning statistics route exists.
* `UI/src/api/teacher.ts` owns teacher-side API wrappers; add teacher statistics wrappers there or in a new focused `teacherStatistics.ts` if size/readability becomes a concern.
* `UI/src/api/admin.ts` likely owns admin API wrappers; add admin learning statistics and statistics-authorization wrappers there or in a focused module if the existing file becomes too broad.
* Existing frontend tables use Element Plus and mobile fallback patterns; teacher/admin statistics pages are table-heavy, so mobile can use horizontal scroll rather than full card conversion.

## Requirements

### 1. Course statistics authorization model

Add a course statistics authorization relation so admin can grant non-owner teachers read/export access to a specific course’s learning statistics.

Recommended backend model name: `CourseTeacherAssignment`.

Recommended table name: `course_teacher_assignments`.

Required fields:

* `id`
* `course_id`
* `teacher_id`
* `permission_type` — MVP fixed value `statistics_viewer`.
* `assigned_by` — admin user ID.
* `assigned_at`
* `revoked_at`
* `is_active`
* standard `created_at` / `updated_at` if inherited by project base model.

Constraints and indexes:

* At most one active `statistics_viewer` authorization for the same `course_id + teacher_id`.
* Index by `teacher_id + is_active` for teacher course list lookup.
* Index by `course_id + is_active` for admin authorization list and course permission checks.
* Do not grant content editing, publishing, archiving, deletion, or material/resource management through this authorization.

Rules:

* Course owner `Course.teacher_id` always has statistics view/detail/export permission and does not need an assignment row.
* Admin authorization candidates include only `role='teacher'` users with normal/active status.
* Exclude the course owner from candidates.
* One course can authorize multiple teachers.
* Re-authorizing the same teacher for the same course should be idempotent: reactivate an existing revoked row or keep the current active row, but never create duplicate active grants.
* Revocation immediately blocks future view/detail/export requests.
* Revocation does not invalidate CSV files already downloaded locally.
* Authorization history should be preserved through `revoked_at`; avoid hard-deleting assignment rows.

### 2. Teacher course statistics APIs

Add teacher-only course statistics endpoints.

Preferred route ownership:

* Add a focused backend router such as `project_code/backend/app/api/v1/teacher_statistics.py` with prefix `/teacher/statistics`.
* Mount it in `project_code/backend/app/api/v1/router.py`.
* Keep implementation logic in `project_code/backend/app/services/learning_statistics_service.py` if cohesive, or split into a focused `teacher_statistics_service.py` that reuses aggregate/query helpers.

Endpoints:

#### `GET /api/v1/teacher/statistics/courses`

Returns current teacher’s viewable course statistics list.

Query parameters:

* `keyword?: string`
* `permission_type?: all|owner|authorized` — default `all`.
* `status?: all|draft|published|archived` — default `all`.
* `page`, `page_size` with existing project pagination limits.

Response item fields:

* `course_id`
* `course_title`
* `course_cover`
* `course_status`
* `permission_type` — `owner` or `authorized`.
* `started_student_count`
* `active_student_count_7d`
* `avg_progress`
* `completion_rate`
* `total_duration_seconds`
* `recent_learn_at`

Rules:

* Only `teacher` role may access this endpoint.
* Include owned courses plus active authorized courses.
* Deduplicate if a teacher somehow has both owner and assignment relationship; show as `owner`.
* Only count `student` learner behavior.
* Prefer aggregate tables for historical totals and supplement current-day sessions if necessary to keep today visible.

#### `GET /api/v1/teacher/statistics/courses/{course_id}/overview?range=7d|30d`

Returns single-course overview metrics.

Response fields:

* `course_id`
* `course_title`
* `range`
* `started_student_count`
* `active_student_count`
* `avg_progress`
* `completion_rate`
* `avg_duration_seconds`
* `total_duration_seconds`
* `recent_learn_at`

Rules:

* `range` defaults to `7d`; allowed values are `7d` and `30d`.
* Course owner or active authorized teacher may access.
* Other teachers receive 403.
* Admin should use admin endpoints rather than this teacher-personal route unless implementation deliberately supports admin for debugging; MVP should keep it teacher-only for clear UX boundaries.
* Only count `student` role learner behavior.

#### `GET /api/v1/teacher/statistics/courses/{course_id}/students`

Returns paginated student learning details for a course.

Query parameters:

* `status=all|inactive|low_progress|completed` — default `all`.
* `page`, `page_size`.
* Optional `keyword` for username search if cheap and consistent with existing table search.
* Default sort: progress ascending.

Filter definitions:

* `inactive`: students who started the course but have no learning session/progress update in the last 7 days.
* `low_progress`: `learning_progress.progress < 30`.
* `completed`: `learning_progress.completed_at IS NOT NULL`.

Response item fields:

* `student_id`
* `username`
* `progress`
* `total_duration_seconds`
* `last_learn_at`
* `completed_at`
* `is_completed`

Privacy boundary:

* Do not return or render email, phone, nickname, avatar, bio, or other nonessential identity fields.
* Use `username` plus `student_id` as the stable identity display, consistent with the project memory that nickname should not be used for identity.

#### `GET /api/v1/teacher/statistics/courses/{course_id}/students/export`

Exports course student learning details as CSV.

Rules:

* Permission is identical to the student detail endpoint.
* Query filters should match the list endpoint where practical, especially `status`.
* CSV uses UTF-8 with BOM for Chinese Excel compatibility.
* CSV fields follow the same minimal identity boundary: student ID, username, progress, duration, recent learn time, completion status/completed time.
* No email, phone, nickname, or avatar in export.
* Unauthorized/revoked teachers receive 403.

### 3. Course statistics authorization admin APIs

Add admin-only endpoints for maintaining course statistics authorizations.

Preferred route ownership:

* Add routes under existing course management prefix if that matches current frontend course management flow:
  * `/api/v1/courses/{course_id}/statistics-authorizations...`
* Or add a focused admin router if implementation wants stronger separation:
  * `/api/v1/admin/courses/{course_id}/statistics-authorizations...`
* Choose one consistent prefix during implementation and keep frontend API docs aligned.
* Parent design used `/api/v1/admin/courses/...`; current code has no admin course router, so using `/courses/{course_id}/statistics-authorizations` with admin guards may reduce routing churn.

Required endpoints:

#### `GET /api/v1/courses/{course_id}/statistics-authorizations`

Returns current active/recent authorization list for the course.

Fields:

* `teacher_id`
* `username`
* `assigned_by`
* `assigned_at`
* `is_active`
* `revoked_at`

Rules:

* Admin only.
* Course must exist.
* Do not include the course owner as an assignment row unless historical data somehow exists; owner is implicit.

#### `GET /api/v1/courses/{course_id}/statistics-authorizations/candidates`

Returns candidate teachers that admin may authorize.

Rules:

* Admin only.
* Only include `role='teacher'` and normal/active status.
* Exclude course owner.
* Prefer excluding already active authorized teachers, or return them with `authorized=true`; choose whichever makes frontend simpler, but document the chosen behavior.
* Candidate identity should be `teacher_id` and `username`; nickname is not needed.

#### `POST /api/v1/courses/{course_id}/statistics-authorizations`

Request:

```json
{
  "teacher_ids": [2, 3]
}
```

Rules:

* Admin only.
* Reject empty `teacher_ids`.
* Validate all teacher IDs are eligible before mutating, or return a structured partial failure response consistent with existing batch-course action style. Recommended MVP: all-or-nothing validation for simpler correctness.
* Exclude/reject course owner.
* Idempotently create/reactivate active statistics-viewer assignments.
* Return current active authorization list or affected count.

#### `DELETE /api/v1/courses/{course_id}/statistics-authorizations/{teacher_id}`

Rules:

* Admin only.
* If active assignment exists, set `is_active=false` and `revoked_at=now`.
* If no active assignment exists, return success idempotently or 404; recommended MVP: return 404 only when the course/teacher does not exist, and success/no-op when already revoked.
* Future teacher view/detail/export must immediately return 403 after revocation.

### 4. Admin platform learning statistics APIs

Add admin-only platform learning statistics endpoints.

Preferred route ownership:

* Add a focused router such as `project_code/backend/app/api/v1/admin_learning_statistics.py` with prefix `/admin/learning-statistics`.
* Mount it in `project_code/backend/app/api/v1/router.py`.
* Keep read logic in `learning_statistics_service.py` or a focused admin statistics service that reuses aggregate helpers.

Shared filters:

* `range=7d|30d|all`, default `7d` where meaningful.
* `category_id?: number`
* `teacher_id?: number`
* `course_status?: all|draft|published|archived`

Rules:

* Admin only.
* Only count `student` learner behavior.
* Time ranges are natural days.
* Use aggregate tables for historical data and supplement current-day sessions if the range includes today and aggregate data may be stale.
* Missing trend dates must be filled with zero values.

#### `GET /api/v1/admin/learning-statistics/overview`

Returns operational overview metrics:

* `total_student_count` — distinct students who ever started learning within matching filters, or total matching learner count for `range=all`.
* `active_student_count` — distinct students active in selected range.
* `total_duration_seconds`
* `active_course_count`
* `new_started_course_count`
* `new_completed_course_count`

#### `GET /api/v1/admin/learning-statistics/trend?range=7d|30d&metric=duration|active_students|completed_courses`

Returns trend data.

Rules:

* Default range is `7d`.
* Support `30d` duration trend as required by parent PRD.
* Missing dates are returned with `value=0`.
* Metrics:
  * `duration`: daily total learning duration seconds.
  * `active_students`: daily active distinct student count.
  * `completed_courses`: daily new completed course count.

#### `GET /api/v1/admin/learning-statistics/popular-courses`

Returns popular courses for selected filters.

Default sort:

* Active student count descending.

Response fields:

* `course_id`
* `course_title`
* `category_id`
* `category_name`
* `teacher_id`
* `teacher_username`
* `active_student_count`
* `total_duration_seconds`
* `completion_rate`
* `recent_learn_at`

#### `GET /api/v1/admin/learning-statistics/low-completion-courses`

Returns low-completion courses.

Rules:

* Include only courses with at least 5 started students.
* Include only courses with completion rate below 30%.
* Default sort by completion rate ascending.
* Filters match overview/popular where practical.

Response fields:

* `course_id`
* `course_title`
* `teacher_id`
* `teacher_username`
* `started_student_count`
* `completed_student_count`
* `completion_rate`
* `avg_progress`
* `recent_learn_at`

### 5. Frontend teacher statistics UX

Add teacher-facing course statistics pages.

Entry:

* In `UI/src/components/layout/AppHeader.vue`, add teacher-only avatar dropdown item “课程统计”.
* Also add it to the mobile user menu when `userStore.canAccessTeacherCenter` is true.
* Recommended path: `/teacher/statistics`.
* Keep existing “课程管理” entry unchanged.

Routes:

* Add `/teacher/statistics` route for course statistics list.
* Add `/teacher/statistics/courses/:courseId` route for single-course statistics detail.
* Both should stay under the existing `/teacher` layout and permission guard.

Pages/components:

* Add `UI/src/views/teacher/CourseStatisticsPage.vue` for teacher course statistics list.
* Add `UI/src/views/teacher/CourseStatisticsDetailPage.vue` for overview + student detail.
* Optionally extract table/filter/export components only if duplication becomes clear; do not over-abstract before needed.

Course list page behavior:

* Shows teacher-viewable courses from `GET /teacher/statistics/courses`.
* Shows permission type badge: “负责人” for owner, “被授权” for authorized.
* Shows key metrics and recent learning time.
* Supports keyword/status/permission filters if implemented in API.
* Clicking a course opens detail page.

Detail page behavior:

* Shows overview cards for started students, active students, average progress, completion rate, average duration, total duration, recent learn time.
* Shows student detail table with filters: all, inactive, low progress, completed.
* Default sort places low-progress students first via backend default progress ascending.
* Export button downloads CSV using the export endpoint.
* Unauthorized/revoked access should show a friendly error and avoid rendering stale data.
* Mobile: overview cards wrap; wide student table uses horizontal scroll and remains usable.

### 6. Frontend admin learning statistics UX

Add admin platform learning statistics page and course authorization operation.

Admin sidebar/menu:

* Add “学习统计” entry in `UI/src/views/admin/AdminLayout.vue`.
* Add matching route in `UI/src/router/index.ts`.
* Recommended path: `/admin/learning-statistics`.
* Permission code decision:
  * Preferred if backend seeding is updated: add `admin.learning_statistics` and assign to admin role.
  * If avoiding RBAC seed changes in this task, reuse `admin` route guard only and omit per-item permission filtering for this one item only if the existing layout supports it cleanly.
  * Do not accidentally hide the page from admin due to missing permission seed.

Admin statistics page:

* Add `UI/src/views/admin/LearningStatisticsPage.vue`.
* Page sections:
  * Filter bar: range, category, teacher, course status.
  * Overview cards.
  * Trend chart/visualization with metric switching.
  * Popular courses table.
  * Low-completion courses table.
* Use lightweight CSS/Element Plus visualizations unless a chart dependency already exists and is justified.
* Mobile: filters wrap; tables use horizontal scroll.

Admin course statistics authorization operation:

* Extend admin course management surface if/where a course management page exists in current project scope.
* Statistics authorization UI belongs in the admin course management surface because it is a course-level management operation.
* Add a “统计授权” operation in admin course management. If the current frontend lacks a dedicated admin course management page, implementation should add or expose the minimal admin course management surface needed for this course-level action rather than placing authorization inside the learning statistics dashboard.
* The UI must support:
  * Viewing active authorized teachers.
  * Searching/selecting multiple eligible teachers.
  * Excluding course owner.
  * Revoking an authorized teacher.
  * Clear copy that authorization grants statistics view/detail/export only.

### 7. Data and metric rules

Global rules:

* All teacher/admin statistics count only `student` learner behavior.
* Learning duration is always effective duration from `learning_sessions` / aggregate rows; do not use `learning_progress.total_duration` as the source of truth unless explicitly proven to mirror session totals.
* Course completion is based on foundation `learning_progress.completed_at` and required-resource completion semantics.
* Course progress uses foundation `learning_progress.progress`.
* Time ranges use natural days consistently with existing aggregation service.
* Current-day data should not disappear just because daily aggregation has not run yet.
* Aggregates are optimization/read models; raw session facts remain authoritative for current-day supplement and exact export/detail queries.

Teacher metric definitions:

* `started_student_count`: distinct `student` users with `learning_progress` or valid course learning sessions for the course.
* `active_student_count`: distinct `student` users with effective learning sessions in selected range.
* `avg_progress`: average `learning_progress.progress` across started students.
* `completion_rate`: completed students / started students × 100.
* `avg_duration_seconds`: total course effective duration / started students, 0 when no started students.
* `recent_learn_at`: max student `last_learn_at` or max session `started_at` for the course.

Admin metric definitions:

* `active_student_count`: distinct `student` users with effective sessions in selected range.
* `active_course_count`: distinct courses with student sessions in selected range.
* `new_started_course_count`: count of user-course pairs whose first started time is in selected range.
* `new_completed_course_count`: count of user-course pairs whose first `completed_at` is in selected range.
* Popular courses default sort by active student count in selected range.
* Low-completion courses require started student count >= 5 and completion rate < 30%.

## Technical Approach

### Backend implementation plan

1. Add authorization model and compatibility:
   * Add `CourseTeacherAssignment` in `project_code/backend/app/models/course.py` or a new model module if preferred.
   * Export it from `project_code/backend/app/models/__init__.py`.
   * Add non-destructive compatibility/table creation in `project_code/backend/app/core/db_schema.py` if current project pattern requires it.
   * Add tests for active uniqueness/idempotency/revocation behavior.

2. Add schemas:
   * Teacher statistics response schemas in `project_code/backend/app/schemas/learning.py` or a new focused schema module.
   * Admin learning statistics schemas.
   * Course authorization request/response schemas.
   * CSV export may not need a Pydantic response schema but should have tested field order.

3. Add services:
   * Add authorization helpers:
     * `ensure_course_statistics_access(db, teacher, course_id)`.
     * `list_authorized_courses(db, teacher_id, filters...)`.
     * `list_candidates(db, course_id)`.
     * `grant_statistics_authorizations(...)`.
     * `revoke_statistics_authorization(...)`.
   * Add teacher read helpers for course list, overview, student detail, and export rows.
   * Add admin read helpers for overview, trend, popular courses, and low-completion courses.
   * Reuse `learning_statistics_service` aggregate/current-day helper patterns where possible.

4. Add routes:
   * New teacher statistics router under `/teacher/statistics`.
   * New admin learning statistics router under `/admin/learning-statistics`.
   * Course authorization routes under the chosen course/admin prefix.
   * Mount new routers in `app/api/v1/router.py`.

5. Permission and RBAC:
   * Teacher routes require `current_user.role == 'teacher'`.
   * Admin routes require `current_user.role == 'admin'` or existing `permission_service.ensure_admin` pattern.
   * If adding `admin.learning_statistics`, update permission seed and frontend menu permission mapping together.

6. CSV export:
   * Use Python CSV writer or equivalent safe formatting.
   * Include UTF-8 BOM.
   * Set `Content-Type: text/csv; charset=utf-8` and `Content-Disposition` filename.
   * Avoid email, phone, nickname, avatar, or arbitrary PII.

### Frontend implementation plan

1. Add typed API wrappers:
   * Teacher stats wrappers in `UI/src/api/teacher.ts` or `UI/src/api/teacherStatistics.ts`.
   * Admin stats/authorization wrappers in `UI/src/api/admin.ts` or focused admin statistics module.
   * Keep response types close to API functions.

2. Add routes:
   * `/teacher/statistics`
   * `/teacher/statistics/courses/:courseId`
   * `/admin/learning-statistics`
   * If a dedicated authorization management route is needed, add it only after confirming UI placement.

3. Update global header:
   * Add “课程统计” to teacher avatar dropdown and mobile menu in `AppHeader.vue`.
   * Preserve existing “课程管理” and “后台管理”.

4. Add teacher pages:
   * Course statistics list page.
   * Course detail statistics page with overview, filters, student table, and CSV export.
   * Use table horizontal scroll for mobile.

5. Add admin page:
   * Overview/filter/trend/popular/low-completion sections.
   * Admin sidebar item.
   * Keep charts lightweight unless existing dependencies justify a charting component.

6. Add authorization UI:
   * Put the “统计授权” action in the admin course management surface.
   * If no dedicated admin course management page currently exists, add/expose the minimal admin course management surface needed for this action instead of putting authorization controls in the admin learning statistics dashboard.

7. Update docs/logs:
   * `UI/docs/前端接口文档.md` when frontend API contracts are added.
   * `UI/operations-log.md` for frontend file changes.
   * `project_code/operations-log.md` for backend file changes.

## Decision (ADR-lite)

**Context**: The parent learning analytics design intentionally split implementation into a shared foundation, student self-statistics, and teacher/admin statistics. The first two subtasks are complete. The remaining work must add higher-privilege views and course-level authorization without duplicating data collection or weakening privacy boundaries.

**Decision**: Implement teacher/admin statistics as a read-model and permission layer over the completed analytics foundation. Add a dedicated course statistics authorization model for non-owner teachers; add teacher-specific course statistics/detail/export APIs; add admin platform statistics APIs; add role-correct frontend entries/pages. Keep student personal statistics and learning-record deletion out of scope.

**Consequences**: This keeps the implementation aligned with existing metric口径 and reduces the risk of contradictory statistics. It adds a new authorization surface, so tests must focus heavily on owner vs authorized vs unauthorized vs revoked access. Admin authorization UI placement may require one implementation-time check because the current frontend routes do not show a dedicated admin course management page.

## Implementation Plan (Small PR/Phase Split)

### Phase 0 — Pre-development checklist

Before coding, implementation agent must read:

* `.trellis/spec/backend/index.md` and listed backend pre-development guidelines.
* `.trellis/spec/frontend/index.md` and listed frontend pre-development guidelines.
* `.trellis/spec/guides/cross-layer-thinking-guide.md` because this touches DB, API, services, routes, frontend API wrappers, menus, and pages.
* `.trellis/spec/guides/code-reuse-thinking-guide.md` before adding helper utilities or route constants.
* `project_code/CLAUDE.md` before backend changes.
* `UI/CLAUDE.md` before frontend changes.
* PRDs for the completed foundation and student self-statistics subtasks.

### Phase 1 — Backend authorization foundation

Files likely touched:

* `project_code/backend/app/models/course.py` or a new model file.
* `project_code/backend/app/models/__init__.py`.
* `project_code/backend/app/core/db_schema.py`.
* `project_code/backend/app/schemas/course.py` or focused authorization schema module.
* `project_code/backend/app/services/course_service.py` or focused authorization service.
* `project_code/backend/app/api/v1/courses.py` or focused admin/course authorization router.
* `project_code/backend/tests/test_courses.py`.

Deliverables:

* `course_teacher_assignments` model/table.
* Admin grant/list/candidate/revoke APIs.
* Permission checks and all-or-nothing validation.
* Tests for candidates, owner exclusion, multiple grants, idempotency, and revocation.

### Phase 2 — Backend teacher statistics

Files likely touched:

* `project_code/backend/app/api/v1/teacher_statistics.py`.
* `project_code/backend/app/api/v1/router.py`.
* `project_code/backend/app/schemas/learning.py` or focused stats schemas.
* `project_code/backend/app/services/learning_statistics_service.py` or `teacher_statistics_service.py`.
* `project_code/backend/tests/test_learning.py`.

Deliverables:

* Teacher course list endpoint.
* Course overview endpoint.
* Student detail endpoint.
* CSV export endpoint.
* Owner/authorized/unauthorized/revoked permission tests.
* Student-only aggregation tests.
* Minimal identity tests proving no email/phone/nickname in detail/export.

### Phase 3 — Backend admin platform statistics

Files likely touched:

* `project_code/backend/app/api/v1/admin_learning_statistics.py`.
* `project_code/backend/app/api/v1/router.py`.
* `project_code/backend/app/services/learning_statistics_service.py` or focused admin stats service.
* `project_code/backend/app/services/permission_service.py` if adding `admin.learning_statistics`.
* `project_code/backend/tests/test_learning.py` and possibly `tests/test_system.py`.

Deliverables:

* Admin overview endpoint.
* Admin trend endpoint.
* Popular courses endpoint.
* Low-completion courses endpoint.
* Admin-only permission tests.
* Filter tests for range/category/teacher/course status where fixtures make this practical.
* Threshold/sort tests for popular and low-completion lists.

### Phase 4 — Frontend teacher statistics pages

Files likely touched:

* `UI/src/components/layout/AppHeader.vue`.
* `UI/src/router/index.ts`.
* `UI/src/api/teacher.ts` or new focused teacher statistics API file.
* `UI/src/views/teacher/CourseStatisticsPage.vue`.
* `UI/src/views/teacher/CourseStatisticsDetailPage.vue`.

Deliverables:

* Teacher-only “课程统计” avatar/mobile menu entry.
* Teacher statistics course list.
* Teacher course detail page with overview, student detail filters, and CSV export.
* Mobile horizontal scroll for wide tables.
* Friendly unauthorized/empty/loading/error states.

### Phase 5 — Frontend admin statistics and authorization UI

Files likely touched:

* `UI/src/views/admin/AdminLayout.vue`.
* `UI/src/router/index.ts`.
* `UI/src/api/admin.ts` or new focused admin statistics API file.
* `UI/src/views/admin/LearningStatisticsPage.vue`.
* Existing admin course management page if discovered, or the new admin statistics page for authorization management.

Deliverables:

* Admin “学习统计” sidebar/mobile entry.
* Admin learning statistics dashboard.
* Filters, overview, trend, popular courses, low-completion courses.
* Course statistics authorization UI for list/candidates/grant/revoke.
* Mobile horizontal scroll/wrapped filters.

### Phase 6 — Documentation, logs, and validation

Files likely touched:

* `project_code/operations-log.md`.
* `UI/operations-log.md`.
* `UI/docs/前端接口文档.md`.
* Possibly backend docs/API inventory if this project convention requires endpoint inventory updates for new APIs.

Deliverables:

* Operations logs match actual file changes.
* API docs include teacher/admin statistics and authorization endpoints used by frontend.
* Backend tests and frontend build/typecheck run.
* Browser validation covers teacher/admin paths.

## Acceptance Criteria

### Backend authorization acceptance

* [ ] `course_teacher_assignments` exists and preserves authorization history.
* [ ] Course owner implicitly has course statistics view/detail/export access.
* [ ] Admin can list current course statistics authorizations.
* [ ] Admin candidate list includes only active normal teachers and excludes the course owner.
* [ ] Admin can authorize multiple eligible teachers for one course.
* [ ] Re-authorizing the same teacher is idempotent and does not create duplicate active grants.
* [ ] Admin can revoke an authorization and the revoked teacher immediately loses future statistics/export access.
* [ ] Authorization grants only statistics view/detail/export, not edit/publish/archive/delete/content permissions.

### Backend teacher statistics acceptance

* [ ] Teacher course list includes owned and authorized courses with correct `permission_type`.
* [ ] Course owner can view/export owned course statistics.
* [ ] Authorized teacher can view/export authorized course statistics.
* [ ] Unauthorized teacher receives 403 for course overview, student detail, and export.
* [ ] Revoked teacher receives 403 after revocation.
* [ ] Teacher statistics count only `student` learner behavior.
* [ ] Overview returns started students, active students, average progress, completion rate, average duration, total duration, and recent learn time.
* [ ] Student detail supports all/inactive/low_progress/completed filters.
* [ ] Inactive means no learning in the last 7 days.
* [ ] Low progress means course progress below 30%.
* [ ] Student detail defaults to progress ascending.
* [ ] Student detail and CSV export exclude email, phone, nickname, avatar, and other nonessential identity fields.
* [ ] CSV export uses UTF-8 with BOM and Chinese-compatible filename/content.

### Backend admin statistics acceptance

* [ ] Admin overview endpoint is admin-only.
* [ ] Admin trend endpoint fills missing dates with zero values.
* [ ] Admin statistics count only `student` learner behavior.
* [ ] Default admin trend range is 7 days; 30-day duration trend is supported.
* [ ] Admin filters support time range, category, teacher, and course status where applicable.
* [ ] Popular courses default sort by active student count descending.
* [ ] Low-completion courses include only courses with at least 5 started students and completion rate below 30%.
* [ ] Current-day data can appear without waiting for the next manual aggregation run.

### Frontend teacher acceptance

* [ ] Teacher-only avatar dropdown includes “课程统计”.
* [ ] Teacher mobile user menu includes “课程统计”.
* [ ] Student users do not see the teacher “课程统计” entry.
* [ ] Teacher statistics list shows owned and authorized courses with permission type badge.
* [ ] Teacher course detail shows overview cards, student detail filters, and export action.
* [ ] Unauthorized/revoked access does not show stale protected data.
* [ ] Teacher statistics pages remain usable on mobile; wide tables scroll horizontally rather than breaking layout.

### Frontend admin acceptance

* [ ] Admin sidebar/mobile drawer includes “学习统计”.
* [ ] Admin learning statistics page shows filters, overview cards, trend, popular courses, and low-completion courses.
* [ ] Admin can manage course statistics authorizations through the chosen UI surface.
* [ ] Candidate picker excludes course owner and avoids duplicate active grants.
* [ ] Revoking an authorization updates the visible state.
* [ ] Admin pages remain usable on mobile; filters wrap and wide tables scroll horizontally.

### Validation acceptance

* [ ] Backend targeted tests pass for learning/statistics/course authorization.
* [ ] Frontend build passes in `UI`.
* [ ] Type checking passes if frontend API/page typing changes are substantial.
* [ ] Browser validation is performed as `teacher1` for teacher statistics list/detail/export and mobile table usability.
* [ ] Browser validation is performed as `admin1` for admin learning statistics and authorization management.
* [ ] Permission validation confirms unauthorized teacher cannot view/export another course and revoked authorization blocks future access.
* [ ] Backend `project_code/operations-log.md` is updated if backend files change.
* [ ] Frontend `UI/operations-log.md` and `UI/docs/前端接口文档.md` are updated if frontend files/API contracts change.

## Validation Plan

Backend, from `project_code/backend`:

* `pytest tests/test_learning.py -v`
* `pytest tests/test_courses.py -v`
* `pytest tests/test_users.py -v` if user/candidate helpers or teacher option behavior are touched.
* `pytest tests/test_system.py -v` if permission seed/RBAC behavior changes.
* `python -m compileall app scripts` if broad backend files or scripts are touched.

Frontend, from `UI`:

* `npm run build`
* `npx vue-tsc -b` if the build does not already cover the relevant type checking or if new API types/routes are substantial.

Browser validation:

* Start backend and frontend dev servers.
* Login as `teacher1` / `Test123456`.
* Verify avatar dropdown and mobile menu show “课程统计”.
* Open `/teacher/statistics`, view owned courses, open a detail page, switch student filters, export CSV.
* Login as a different unauthorized teacher and verify direct URL/API access is blocked.
* Login as `admin1` / `Admin123456`.
* Open `/admin/learning-statistics`, verify overview/trend/popular/low-completion sections.
* Grant a course statistics authorization to another teacher, verify that teacher can view/export, revoke it, then verify access is blocked.
* Check one desktop viewport and one mobile viewport for teacher/admin table usability and horizontal overflow.

## Out of Scope

* Student personal statistics APIs/page.
* Learning session collection, progress snapshot saving, visible record deletion semantics, or aggregate table infrastructure rewrites.
* Granting authorized teachers course editing, publishing, archiving, deletion, content management, or material/resource upload permissions.
* Admin viewing individual student private profile/contact data from platform statistics.
* Email/phone/nickname/avatar in teacher student detail or exports.
* Advanced resource diagnosis, per-resource heatmaps, seek/pause analytics, prediction, recommendation, or full BI dashboard.
* Adding a scheduler system for aggregation jobs; existing manual/callable aggregation remains the baseline unless a separate scheduler task is created.
* Destructive cleanup of old learning behavior data.

## Risks and Guardrails

* **Permission regression**: owner, authorized, unauthorized, revoked, teacher/admin role boundaries must be tested directly.
* **Privacy leakage**: teacher details/exports must not include email, phone, nickname, avatar, or broad profile fields.
* **Metric drift**: do not calculate learning duration from progress snapshots; use session/aggregate口径.
* **Current-day staleness**: teacher/admin dashboards should include current-day session supplement or clearly reuse the existing service behavior that does so.
* **Route/permission mismatch**: if adding `admin.learning_statistics`, update backend seed, frontend route meta, admin layout menu, and default admin role permissions together.
* **Admin authorization UI placement**: user confirmed statistics authorization belongs in admin course management because it is a course-level management operation.
* **CSV encoding**: export must include BOM; test response bytes, not just visible text.
* **Large frontend tables**: teacher/admin pages are table-heavy; mobile acceptance is horizontal-scroll usability, not perfect card redesign.

## Technical Notes

* Parent PRD source: `.trellis/tasks/05-09-student-learning-analytics/prd.md`.
* Foundation PRD source: `.trellis/tasks/05-09-learning-statistics-foundation/prd.md`.
* Student self-statistics PRD source: `.trellis/tasks/05-09-student-self-statistics/prd.md`.
* Existing backend aggregate service: `project_code/backend/app/services/learning_statistics_service.py`.
* Existing backend learning routes: `project_code/backend/app/api/v1/learning.py`.
* Existing backend route aggregator: `project_code/backend/app/api/v1/router.py`.
* Existing backend course owner model: `project_code/backend/app/models/course.py` / `Course.teacher_id`.
* Existing backend user role/status model: `project_code/backend/app/models/user.py`.
* Existing frontend avatar dropdown/mobile user menu: `UI/src/components/layout/AppHeader.vue`.
* Existing frontend teacher routes/layout: `UI/src/router/index.ts`, `UI/src/views/teacher/TeacherLayout.vue`.
* Existing frontend admin sidebar/mobile drawer: `UI/src/views/admin/AdminLayout.vue`.
* Existing frontend API modules: `UI/src/api/teacher.ts`, `UI/src/api/admin.ts`, `UI/src/api/learning.ts`.
* Do not use nickname in teacher/admin statistics UI, API responses, tables, candidate identity, or exports.
