# Learning Statistics Foundation

## Goal

Implement the full shared learning analytics foundation defined by parent task `05-09-student-learning-analytics`, including backend data foundation, frontend learning-session collection, progress/record semantics, aggregation, migration boundaries, and verification. Student, teacher, and admin statistics must later consume one consistent data model and metric口径 instead of redefining learning time, course completion, records, and aggregation separately.

This subtask is still in planning only. No product code is implemented in this planning pass.

## Scope Decision

Jacob confirmed that this foundation subtask should include everything needed for the first complete foundation slice, not only a backend-only API contract.

Included in this subtask:

* Backend models/tables for session facts, course-level progress summary, visible learning-record entries, and daily aggregate tables.
* Backend session API `POST /api/v1/learning/sessions` with idempotency and effective-duration normalization.
* Backend `Resource.is_required` data model and content API/schema support.
* Backend progress-save semantics: maintain `resource_progress`, formalize `learning_progress`, preserve first course completion, and maintain visible learning-record entries.
* Backend aggregation service/command-level callable logic that can re-run safely and reprocess the 7-day offline retry window.
* Frontend learning-session collector integrated into the learning page lifecycle, separate from existing progress snapshot saving.
* Frontend persisted offline retry queue for learning sessions with a 7-day retention boundary.
* Frontend resource create payload/display support for required/optional resources where current UI creates resources.
* Backend and frontend operations logs and API documentation updates when actual implementation happens.
* Validation across backend tests, frontend build/typecheck, and browser learning-page golden paths.

Not included in this subtask:

* Student statistics dashboard page UI.
* Teacher course statistics dashboard UI.
* Admin platform statistics dashboard UI.
* Teacher/admin statistics authorization and CSV export.
* Advanced BI/heatmaps/recommendation/prediction features.
* Executing destructive cleanup of old learning behavior data without a separate explicit confirmation.

## Research References

* [`research/backend-foundation-code-map.md`](research/backend-foundation-code-map.md) — backend code map for learning progress, resources, records, content flows, publish validation, schema compatibility, and missing aggregation patterns.
* [`research/frontend-session-collector-code-map.md`](research/frontend-session-collector-code-map.md) — frontend code map for `LearningPage.vue`, `useProgressSync.ts`, learn store, learning API wrappers, offline/beacon patterns, routes, and frontend logging rules.
* [`research/validation-migration-code-map.md`](research/validation-migration-code-map.md) — validation/migration map for pytest fixtures, DB compatibility workflow, seed data, one-off migration patterns, and absence of scheduler infrastructure.

## Current Repo Findings

### Backend findings

* `project_code/backend/app/api/v1/learning.py` exposes learning progress routes under `/api/v1/learning`.
* `POST /api/v1/learning/progress` currently saves a per-resource snapshot using `learning_service.save_progress`.
* `project_code/backend/app/models/learning.py` defines `ResourceProgress`, which is the active resource-level progress snapshot model.
* `ResourceProgress.section_id` is already nullable for chapter-level resources.
* `project_code/backend/app/models/learning_progress.py` defines `LearningProgress`, but current service paths found in research do not actively write it as the authoritative course summary.
* `project_code/backend/app/services/user_service.py` currently builds `/users/me/learning-records` by joining `ResourceProgress`, `Course`, `Section`, and `Resource`, deduplicating by course in Python.
* `project_code/backend/app/models/content.py` defines `Resource` with `is_free`, but not `is_required`.
* `is_free` means free preview/access and must not be reused as required/optional learning semantics.
* Backend content creation flows are in `project_code/backend/app/schemas/content.py`, `project_code/backend/app/api/v1/content.py`, and `project_code/backend/app/services/content_service.py`.
* No backend `ResourceUpdate` route/schema/service was found; resource management currently creates and deletes resources, so `is_required` is primarily create/response/display scope unless a resource-edit path is added separately.
* `CourseService._ensure_publishable` currently checks only title/description; publish validation does not check content or required resources.
* No daily/stat aggregation implementation or scheduler infrastructure was found.
* DB compatibility convention is `project_code/backend/app/core/db_schema.py` plus scripts under `project_code/backend/scripts/`; no Alembic migration directory exists despite Alembic being listed in requirements.

### Frontend findings

* `UI/src/views/learn/LearningPage.vue` owns learning-page lifecycle: course/resource loading, resource switching, media/document/image behavior, route leave, unmount, beforeunload, online/offline events.
* `UI/src/composables/useProgressSync.ts` currently handles progress snapshot sync only: local timeupdate, periodic 30s save, immediate save, `sendBeacon`, and in-memory offline retry queue.
* Existing `beforeunload` beacon targets `/api/v1/learning/progress`, not session collection.
* Existing offline queue is memory-only and does not survive page reload, so it does not satisfy the 7-day retry requirement.
* `UI/src/api/learning.ts` has progress and resource API wrappers but no `/learning/sessions` API wrapper.
* `UI/src/store/learn.ts` stores active resource, playback state, progress percent, total time, and current course context; it can provide session context but does not currently track session lifecycle.
* `UI/src/views/teacher/components/ResourceManager.vue` creates resource payloads with `resource_type`, `title`, `file_name`, `file_url`, `file_size`, `sort_order`, and `is_free`; it should be updated to include `is_required` defaulting to true and a UI control/label if resource requirement is editable.
* `UI/src/api/teacher.ts` owns teacher resource API types/wrappers; resource types need `is_required` support.

### Validation and migration findings

* Backend tests use in-memory SQLite and `Base.metadata.create_all`, so new models must be imported/exported through `app/models/__init__.py`.
* Existing tests for learning, users, and content are the right places to extend coverage.
* Compatibility changes should go through `ensure_database_compatibility` and/or explicit scripts because no Alembic workflow is active.
* No scheduler exists. Aggregation should be implemented as a callable backend service and optional manual script first; recurring scheduling can be added later when the project has an agreed scheduler mechanism.

## Requirements

### 1. Learning session fact model

Add `learning_sessions` as the source-of-truth fact table for analytics sessions.

Required fields:

* `id`
* `session_id` — globally unique frontend-generated idempotency key.
* `user_id`
* `course_id`
* `chapter_id`
* `section_id` — nullable for chapter-level resources.
* `resource_id`
* `resource_type` — denormalized from `Resource.type` at submission time.
* `started_at`
* `ended_at`
* `effective_duration_seconds`
* `start_position_seconds` — media only, nullable.
* `end_position_seconds` — media only, nullable.
* `progress_percent_at_end` — nullable.
* `is_completed_at_end`
* `end_reason` — `switch_resource | leave_page | completed | timeout | beacon | offline_retry | manual_stop | error`.
* `created_at`, `updated_at` inherited from base model if available.

Indexes/constraints:

* Unique `session_id`.
* Index `user_id + started_at`.
* Index `course_id + started_at`.
* Index `resource_id`.
* Index `started_at`.

Behavior:

* Backend derives `course_id`, `chapter_id`, `section_id`, and `resource_type` from `resource_id`.
* Backend does not trust frontend-provided hierarchy fields for session facts.
* `POST /learning/sessions` writes analytics facts only and must not update `resource_progress`.
* Teacher/admin sessions may be stored in `learning_sessions` if they use the learning page, but aggregate metrics must filter to `student` role only.

### 2. Learning session API

Add `POST /api/v1/learning/sessions`.

Request fields:

* `session_id: string`
* `resource_id: number`
* `started_at: datetime`
* `ended_at: datetime`
* `effective_duration_seconds: number`
* `start_position_seconds?: number`
* `end_position_seconds?: number`
* `progress_percent_at_end?: number`
* `is_completed_at_end?: boolean`
* `end_reason: switch_resource | leave_page | completed | timeout | beacon | offline_retry | manual_stop | error`

Response fields:

* `session_id`
* `accepted: boolean`
* `effective_duration_seconds`
* `duplicate: boolean` or equivalent idempotency indicator.

Rules:

* Missing/unknown resource returns the project’s existing not-found/error pattern.
* Current user must have learning access to the resource/course.
* `ended_at < started_at` is rejected.
* Negative durations are rejected.
* Valid duplicate `session_id` does not insert another row.
* Duplicate submissions may improve/update terminal fields, but must not reduce start time, move media end position backward, regress completion state, or double count duration.
* Duration is normalized on both insert and duplicate update.

### 3. Effective duration normalization

Final accepted duration is:

`min(frontend_effective_duration_seconds, ended_at - started_at, resource_type_cap_seconds, media_resource_duration_if_applicable)`

Resource-type rules:

* Video/audio:
  * Frontend sends actual playback seconds accumulated only while media is playing.
  * Backend caps by wall-clock duration.
  * Backend also caps by resource duration if `Resource.duration > 0`.
* Document:
  * Frontend counts foreground active viewing/reading time.
  * Frontend stops counting after 5 minutes without activity.
  * Backend caps a single document session at 20 minutes.
* Image:
  * Frontend counts foreground viewing time.
  * Backend caps a single image session at 5 minutes.
* Unknown/unsupported resource type should be rejected or treated as 0 duration for analytics; MVP should reject unsupported types rather than silently pollute metrics.

### 4. Required / optional resource model

Add `Resource.is_required: bool NOT NULL DEFAULT true`.

Implementation requirements:

* Add field to backend `Resource` model.
* Add field to `ResourceCreate` with default `true`.
* Add field to `ResourceResponse`.
* Set `is_required=data.is_required` in both section-level and chapter-level resource creation.
* Ensure existing resources get `true` through model default and DB compatibility update.
* Expose `is_required` through teacher frontend resource types and create payload.
* Update teacher `ResourceManager.vue` so newly uploaded resources send `is_required: true` by default and can be marked required/optional if UI scope chooses to expose it immediately.
* Do not overload `is_free`.

Publish validation:

* When publishing a course, require at least one required resource in the course.
* Apply the same rule to single publish and batch publish.
* If a published course has no required resources, return a clear validation error.

### 5. Formalized course-level `learning_progress`

Use `learning_progress` as the user-course current summary.

Required fields/semantics:

* Unique `user_id + course_id`.
* `progress` — course-level percent based on required resources.
* `last_section_id` — nullable.
* `last_resource_id` — add if absent.
* `last_position`.
* `last_learn_at` — add if absent or use `updated_at` deliberately; implementation should prefer explicit `last_learn_at` for clarity.
* `total_duration` may remain if existing, but analytics duration should come from sessions/aggregates, not this field.
* `completed_at` — first course completion time.

Progress-save integration:

* `POST /learning/progress` remains the resource progress snapshot API.
* After saving/upserting `ResourceProgress`, update/create `LearningProgress` for that user/course.
* Course progress uses required resources only.
* Equal weighting: `completed_required_resource_count / required_resource_count * 100`.
* If `required_resource_count == 0`, progress is 0 and publish should prevent this state for published courses.
* When progress first reaches 100, set `completed_at` if it is currently null.
* Never clear or move `completed_at` backward after first completion.
* Continue-learning behavior must continue to work from latest `ResourceProgress` unless deliberately moved to `LearningProgress` in a tested way.

### 6. Append-style learning-record display entries

Add `learning_record_entries` for student-visible learning record rows.

Required fields:

* `id`
* `user_id`
* `course_id`
* `last_section_id` — nullable.
* `last_resource_id`
* `last_learn_at`
* `course_progress_snapshot`
* `course_completed_snapshot`
* `visible`
* `hidden_at`
* `created_at`, `updated_at`

Rules:

* Same user/course may have at most one visible row.
* If a visible row exists, later learning updates that row.
* If only hidden rows exist, later learning creates a new visible row.
* Hidden rows are not reactivated.
* Query `/users/me/learning-records` returns only `visible = true` rows.
* The row can store snapshots, but API display should return current progress/completion from `learning_progress` so the list reflects current state.
* Deleting/hiding records does not affect progress, sessions, or statistics.

Deletion endpoint foundation requirement:

* Add or prepare `POST /api/v1/users/me/learning-records/delete` with `{ record_ids: number[] }` if learning-record deletion is included in foundation implementation.
* Validate all record IDs exist, belong to current student, and are visible.
* Any invalid ID fails the whole request; no partial deletion.
* On success, set `visible=false`, `hidden_at=now`.

### 7. Daily aggregate tables

Add aggregate models/tables:

#### `student_daily_learning_stats`

Dimension: `user_id + stat_date`.

Fields:

* `effective_duration_seconds`
* `video_duration_seconds`
* `audio_duration_seconds`
* `document_duration_seconds`
* `image_duration_seconds`
* `session_count`
* `learned_course_count`
* `completed_resource_count`

#### `student_course_daily_stats`

Dimension: `user_id + course_id + stat_date`.

Fields:

* `effective_duration_seconds`
* `session_count`
* `completed_resource_count`
* `course_progress_at_day_end`
* `is_course_completed_at_day_end`

#### `course_daily_learning_stats`

Dimension: `course_id + stat_date`.

Fields:

* `active_student_count`
* `new_started_student_count`
* `new_completed_student_count`
* `cumulative_started_student_count`
* `cumulative_completed_student_count`
* `total_effective_duration_seconds`
* `avg_progress`
* `completion_rate`

#### `platform_daily_learning_stats`

Dimension: `stat_date`.

Fields:

* `active_student_count`
* `new_started_course_count`
* `new_completed_course_count`
* `total_effective_duration_seconds`
* `active_course_count`

Rules:

* Aggregates derive from `learning_sessions` plus `learning_progress`/`resource_progress` where needed.
* Aggregates include only `student` role users.
* Aggregation uses natural dates consistently.
* Aggregate tables are query optimization/trend sources; `learning_sessions` remains the fact source.

### 8. Re-runnable aggregation service and manual script

Because the project has no scheduler infrastructure, this subtask should implement callable aggregation logic and a manual script, not invent a scheduler system.

Required implementation:

* Add backend service, conceptually `learning_statistics_service` or `learning_aggregation_service`.
* Implement `aggregate_date(stat_date)` or equivalent.
* Implement `aggregate_range(start_date, end_date)`.
* Re-aggregation must delete/replace or upsert by dimension/date; never additive-accumulate over existing aggregate rows.
* Add a manual script under `project_code/backend/scripts/`, conceptually `aggregate_learning_stats.py`, that can aggregate one date or the last N days.
* Default operational behavior should support re-aggregating the last 7 days to include offline retry sessions.
* Do not wire recurring scheduling in this task unless an existing scheduler pattern is introduced elsewhere first.

### 9. Frontend learning-session collector

Implement session collection in frontend learning flow, separate from progress snapshot sync.

Preferred structure:

* Keep `useProgressSync.ts` focused on progress snapshots if possible.
* Add a new composable, conceptually `UI/src/composables/useLearningSession.ts`, or extend carefully if keeping one composable is simpler.
* Add `saveLearningSession` API wrapper and request/response types in `UI/src/api/learning.ts`.
* Generate a UUID `session_id` on each resource activation.
* Track `started_at`, active resource id/type, start position, effective duration, last activity time, and end reason.
* On resource switch, route leave, unmount, media completion, document/image close/timeout, and beforeunload, finalize and submit the current session.
* Continue to call `/learning/progress` separately for current progress snapshots.
* Do not make session submission failure block learning, playback, navigation, or progress saving.

Media behavior:

* Count effective duration only while video/audio is playing.
* Paused/background time must not count.
* Track `start_position_seconds` and `end_position_seconds`.
* On `ended`, finalize session with `end_reason=completed` after progress completion sync.

Document/image behavior:

* Document/image opening still marks resource completed for progress.
* Start a session when the resource becomes active.
* Count foreground active viewing time.
* For documents, stop accumulating after 5 minutes idle and finalize or cap at 20 minutes.
* For images, cap at 5 minutes.
* Track user activity events such as mouse/keyboard/scroll/touch on the learning page for document idle detection.

Offline retry:

* Persist session retry queue in localStorage, not only memory.
* Queue payloads when session submission fails due to network/offline conditions.
* Keep queued sessions at most 7 days.
* Flush queued sessions on app/page online event and learning-page mount.
* Preserve the same `session_id` on retry.
* For retries, submit `end_reason=offline_retry` only if that is the intended terminal reason; otherwise retain original reason and include retry behavior only through same session id. Implementation should choose one convention and test backend idempotency.

Beacon behavior:

* `beforeunload` should attempt a session beacon to `/api/v1/learning/sessions` in addition to existing progress beacon.
* The beacon payload must include the same `session_id`, resource id, times, duration, progress, completion, and end reason.
* If beacon cannot be trusted to include auth headers, keep current progress beacon behavior and rely on persisted retry on next load for authenticated session submission. Do not introduce insecure token-in-body behavior.

### 10. Frontend required-resource support

Update teacher content/resource creation flow to preserve required/optional semantics.

Likely files:

* `UI/src/api/teacher.ts`
* `UI/src/views/teacher/components/ResourceManager.vue`
* Possibly course/chapter/resource types consumed by `UI/src/views/teacher/CourseFormPage.vue` and `UI/src/views/teacher/components/ChapterManager.vue`.

Requirements:

* Add `is_required?: boolean` to resource request/type definitions.
* Default uploaded resources to `is_required: true`.
* Display whether a resource is required/optional in teacher course content UI if the backend response includes it.
* If adding an edit control is too large, defaulting and displaying is still required; toggling can be a follow-up only if no existing resource update endpoint exists.

## Concrete Implementation Plan

### Phase 0 — Pre-implementation checklist

Before coding, implementation agent must read:

* `.trellis/spec/backend/index.md` and listed backend pre-development guidelines.
* `.trellis/spec/frontend/index.md` and listed frontend pre-development guidelines.
* `.trellis/spec/guides/cross-layer-thinking-guide.md` because this touches API, services, database, frontend composables, and UI.
* `.trellis/spec/guides/code-reuse-thinking-guide.md` before adding helper utilities or changing constants.
* `project_code/CLAUDE.md` before backend changes.
* `UI/CLAUDE.md` before frontend changes.
* The three research files listed above.

### Phase 1 — Backend models and schema compatibility

Files likely touched:

* `project_code/backend/app/models/content.py`
* `project_code/backend/app/models/learning.py`
* `project_code/backend/app/models/learning_progress.py`
* `project_code/backend/app/models/__init__.py`
* `project_code/backend/app/core/db_schema.py`
* `project_code/backend/scripts/init_db.py` only if needed by existing pattern.
* New explicit cleanup/migration scripts under `project_code/backend/scripts/` if needed.

Tasks:

1. Add `Resource.is_required` with default `true`.
2. Add or extend `LearningProgress` with `last_resource_id`, `last_learn_at`, and unique `user_id + course_id` support.
3. Add models for `LearningSession`, `LearningRecordEntry`, and four aggregate tables.
4. Export new models from `app/models/__init__.py` so tests and init see them.
5. Add `ensure_database_compatibility` logic for existing DBs:
   * add `resources.is_required` default true,
   * add missing `learning_progress` columns if needed,
   * create new tables through metadata/init path, or explicit compatibility table creation if existing startup does not create new tables after first deploy.
6. Add compatibility tests if `db_schema.py` changes are non-trivial.

Pitfalls:

* SQLite compatibility may require separate behavior from MySQL.
* Do not execute destructive cleanup automatically.
* Ensure model defaults and DB defaults agree enough for existing rows.

### Phase 2 — Backend content/resource required flag

Files likely touched:

* `project_code/backend/app/schemas/content.py`
* `project_code/backend/app/services/content_service.py`
* `project_code/backend/app/services/course_service.py`
* `project_code/backend/tests/test_content.py`
* `project_code/backend/tests/test_courses.py`

Tasks:

1. Add `is_required` to `ResourceCreate`, default `true`.
2. Add `is_required` to `ResourceResponse`.
3. Persist `data.is_required` in `create_for_section` and `create_for_chapter`.
4. Ensure course detail/resource tree response includes `is_required` through existing `ResourceResponse` serialization.
5. Add publish validation requiring at least one required resource.
6. Ensure batch publish uses same validation.
7. Add/extend tests for:
   * default required resource creation,
   * explicit optional resource creation,
   * course detail returns required flag,
   * publish fails with no required resources,
   * publish succeeds with at least one required resource.

### Phase 3 — Backend session API and duration normalization

Files likely touched:

* `project_code/backend/app/schemas/learning.py`
* `project_code/backend/app/api/v1/learning.py`
* `project_code/backend/app/services/learning_service.py` or new `project_code/backend/app/services/learning_session_service.py`
* `project_code/backend/tests/test_learning.py`

Tasks:

1. Add Pydantic request/response schemas for learning sessions.
2. Implement duration normalization helper:
   * validate non-negative duration,
   * validate `ended_at >= started_at`,
   * compute wall-clock seconds,
   * apply media/document/image caps.
3. Implement idempotent service logic:
   * lookup by `session_id`,
   * insert on first submit,
   * update allowed terminal fields on duplicate,
   * never create duplicate duration.
4. Add `POST /learning/sessions` route returning `ApiResponse`.
5. Add tests for:
   * valid media session,
   * valid document/image caps,
   * duplicate session idempotency,
   * duplicate update does not regress,
   * invalid resource,
   * invalid time range,
   * teacher/admin session storage vs student-only aggregate boundary later.

### Phase 4 — Backend progress summary and learning-record entries

Files likely touched:

* `project_code/backend/app/services/learning_service.py`
* `project_code/backend/app/services/user_service.py`
* `project_code/backend/app/schemas/user.py`
* `project_code/backend/app/api/v1/users.py`
* `project_code/backend/tests/test_learning.py`
* `project_code/backend/tests/test_users.py`

Tasks:

1. After `ResourceProgress` upsert, compute course-level required-resource progress.
2. Upsert `LearningProgress` by `user_id + course_id`.
3. Set `last_section_id`, `last_resource_id`, `last_position`, `last_learn_at`.
4. Set `completed_at` only if null and course first reaches completion.
5. Preserve `completed_at` even if required resources later change.
6. Maintain `LearningRecordEntry` visible row:
   * update existing visible row,
   * create new visible row if none exists,
   * do not reactivate hidden rows.
7. Change `/users/me/learning-records` to query visible `LearningRecordEntry` rows and join to current course/progress context.
8. Add `POST /users/me/learning-records/delete` if implementing deletion foundation now.
9. Add tests for:
   * required-resource-only course progress,
   * optional resource does not block course completion,
   * first completion persists,
   * visible record updates on repeat learning,
   * hidden record remains hidden and new row appears after later learning,
   * deletion all-or-nothing validation,
   * deletion does not delete progress/session data.

### Phase 5 — Backend aggregation service and manual script

Files likely touched:

* New or existing `project_code/backend/app/services/learning_statistics_service.py`
* New `project_code/backend/scripts/aggregate_learning_stats.py`
* `project_code/backend/tests/test_learning.py` or new focused test module if existing file becomes too large.

Tasks:

1. Implement aggregation for one natural date.
2. Implement aggregation for a date range.
3. Use only `student` role users in aggregate queries.
4. Rebuild aggregates for the target date by delete+insert or upsert-overwrite.
5. Compute student daily, student-course daily, course daily, and platform daily aggregates.
6. Add manual script that defaults to recent 7 days and accepts explicit start/end/date arguments if consistent with project scripts.
7. Add tests for:
   * aggregate creation from sessions,
   * teacher/admin sessions excluded,
   * rerun does not duplicate totals,
   * late session in previous 7 days appears after rerun,
   * platform/course/student counts match expected distinct semantics.

### Phase 6 — Frontend learning-session API and collector

Files likely touched:

* `UI/src/api/learning.ts`
* New `UI/src/composables/useLearningSession.ts` or careful extension to `UI/src/composables/useProgressSync.ts`
* `UI/src/views/learn/LearningPage.vue`
* `UI/src/store/learn.ts` only if collector needs shared state beyond composable-local state.

Tasks:

1. Add `LearningSessionRequest`, `LearningSessionResponse`, and `saveLearningSession` to `UI/src/api/learning.ts`.
2. Add a session collector composable with:
   * `startSession(resourceContext)`
   * `recordMediaPlayingDelta(...)` or equivalent duration accumulation
   * `recordActivity()` for document idle detection
   * `finishSession(endReason)`
   * `flushSessionQueue()`
   * `onBeforeUnloadSession()`
3. Generate stable UUID per resource session using browser crypto API if available.
4. Integrate collector in `LearningPage.vue`:
   * start session after active resource is set,
   * finish session before resource switch after progress immediate sync,
   * finish session on route leave/unmount,
   * finish session on media ended,
   * count only playing time for media,
   * count document/image foreground activity with caps/idle rules.
5. Persist failed session payloads in localStorage with `queued_at`.
6. Drop queued payloads older than 7 days.
7. Flush queue on online and learning-page mount.
8. Keep existing progress sync behavior intact.
9. Add unit-level tests only if existing frontend test harness exists; otherwise rely on build/typecheck and browser validation.

Important frontend boundary:

* Do not put access token in beacon payload.
* If `sendBeacon` cannot include auth, use it only when existing cookies/headers make it work; otherwise persisted retry on next authenticated page load is the reliable path.

### Phase 7 — Frontend required-resource support

Files likely touched:

* `UI/src/api/teacher.ts`
* `UI/src/views/teacher/components/ResourceManager.vue`
* Possibly `UI/src/views/teacher/components/ChapterManager.vue` and `UI/src/views/teacher/CourseFormPage.vue` if their local types need the new field.

Tasks:

1. Add `is_required` to resource item/request types.
2. Include `is_required: true` in upload resource payloads by default.
3. Display required/optional label in resource list.
4. If adding edit UI is feasible without inventing a missing backend update route, add a simple required/optional selector before upload.
5. Do not add a fake update flow if backend has no resource update endpoint; mark editing existing resource requirement as follow-up if needed.

### Phase 8 — Documentation, operations logs, and validation

Backend files likely touched:

* `project_code/operations-log.md`
* Possibly backend docs if API behavior changes are documented there.

Frontend files likely touched:

* `UI/operations-log.md`
* `UI/docs/前端接口文档.md`

Validation commands:

Backend, from `project_code/backend`:

* `pytest tests/test_learning.py -v`
* `pytest tests/test_users.py -v`
* `pytest tests/test_content.py -v`
* `pytest tests/test_courses.py -v`
* If compatibility logic changes substantially, also run focused compatibility tests in `tests/test_permissions.py` / `tests/test_feedbacks.py` or new compatibility tests.

Frontend, from `UI`:

* `npm run build`
* `npx vue-tsc -b` if type changes are substantial or build does not already run full type checking.

Browser validation:

* Start backend and frontend dev servers.
* Login as `student1` / `Test123456`.
* Open a published course learning page.
* Verify video/audio progress still saves every 30 seconds and on pause/switch/leave.
* Verify session submission is created once per resource learning session.
* Verify duplicate/retry does not double count.
* Verify document/image still marks complete and submits a capped session.
* Verify offline then online queues and flushes session payloads.
* Verify navigation away does not lose progress or break route leave.
* Login as `teacher1` and verify resource upload sends/defaults `is_required` and page/build does not break.

## Acceptance Criteria

### Backend acceptance

* [ ] `Resource.is_required` exists, defaults to true, and appears in create/response schemas.
* [ ] Existing resources are treated as required after compatibility/init.
* [ ] Course publish rejects courses with zero required resources.
* [ ] `learning_sessions` exists with unique `session_id` and derived hierarchy fields.
* [ ] `POST /api/v1/learning/sessions` records a valid session once.
* [ ] Re-submitting the same `session_id` does not insert a second row or double count duration.
* [ ] Effective duration uses the minimum of frontend duration, wall-clock duration, resource-type cap, and media duration where applicable.
* [ ] Invalid time ranges are rejected.
* [ ] `POST /api/v1/learning/progress` still maintains `resource_progress` correctly.
* [ ] `learning_progress` is maintained as user-course summary after progress save.
* [ ] Course completion uses required resources only.
* [ ] First `completed_at` is preserved and does not regress.
* [ ] `learning_record_entries` supports visible-row update and new-row-after-hide semantics.
* [ ] Learning-record deletion is all-or-nothing and only hides visible display rows.
* [ ] Daily aggregation can be rerun without duplicate accumulation.
* [ ] Aggregates include only `student` role users.

### Frontend acceptance

* [ ] `UI/src/api/learning.ts` exposes a typed session submission API.
* [ ] Learning page starts a session per active resource.
* [ ] Resource switch/leave/unmount/completion finalizes the current session.
* [ ] Video/audio effective duration counts playing time only.
* [ ] Document/image sessions respect idle/cap behavior.
* [ ] Session retry queue persists across reloads and drops entries older than 7 days.
* [ ] Existing progress sync to `/learning/progress` continues to work.
* [ ] Teacher resource upload defaults new resources to required and preserves the `is_required` field in frontend types/payloads.

### Validation acceptance

* [ ] Backend targeted tests pass.
* [ ] Frontend build/typecheck passes.
* [ ] Browser golden-path validation is performed for student learning page.
* [ ] Backend operations log is updated if backend files change.
* [ ] Frontend operations log and API docs are updated if frontend files/API contract change.
* [ ] No destructive learning-data cleanup is executed without explicit confirmation.

## Risks and Guardrails

* **Large blast radius**: this touches learning, content, records, and frontend lifecycle. Implement in phases and test after each backend service boundary.
* **Progress/session confusion**: `/learning/progress` remains current snapshot; `/learning/sessions` is analytics fact. Do not merge responsibilities.
* **Duplicate duration**: all aggregation must derive from unique sessions and be re-runnable.
* **Completion regression**: never clear `completed_at` after first completion.
* **Hidden record semantics**: hidden/deleted visible rows stay hidden; later activity creates a new visible row.
* **Auth and beacon**: do not put tokens into beacon body. Prefer persisted retry for authenticated session submission.
* **No scheduler**: implement callable/manual aggregation first; do not add a scheduler dependency casually.
* **Migration safety**: compatibility may add fields/tables, but destructive cleanup must be separate and explicitly confirmed.

## Definition of Done

* Full foundation backend and frontend collector are implemented according to this plan.
* Student/teacher/admin future tasks can consume session facts, course progress summaries, record entries, and daily aggregates without redefining metric口径.
* Existing continue-learning and progress-saving behavior remains intact.
* Required/optional resource semantics are available in backend and resource creation UI path.
* Tests and manual validation prove idempotency, duration caps, student-only aggregation, first-completion persistence, hidden-record semantics, and frontend collector behavior.
* Operations logs and API docs are updated for actual changed areas.

## Migration / Cleanup Boundary

The parent design says旧学习行为数据上线新方案时可以清零，但 this implementation must not perform cleanup automatically.

Allowed in this subtask:

* Add non-destructive schema compatibility.
* Add an explicit cleanup script only if needed and clearly named.
* Make the script print affected tables and row counts before action.
* Require explicit manual confirmation before destructive cleanup.

Not allowed without another explicit Jacob confirmation:

* Clearing `resource_progress`.
* Clearing `learning_progress`.
* Clearing existing learning-record data.
* Clearing session/aggregate tables in a non-test database.
* Deleting users/courses/chapters/sections/resources.
* Clearing `student_count`, `view_count`, or other general counters.

## Technical Notes

* Parent PRD source: `.trellis/tasks/05-09-student-learning-analytics/prd.md`.
* This plan intentionally goes beyond the earlier simple foundation PRD because Jacob confirmed the foundation task should include the full end-to-end foundation, including frontend collection.
* Backend actual changes must update `project_code/operations-log.md`.
* Frontend actual changes must update `UI/operations-log.md`; API contract changes should update `UI/docs/前端接口文档.md`.
