# Research: Learning Analytics Data Modeling

- **Query**: Research practical data modeling approaches for learning analytics in an online video learning platform. Compare event-log based tracking, progress snapshot tables, aggregate/stat tables, and hybrid approaches. Cover metric accuracy, privacy/permission boundaries, idempotency, offline/retry issues, course deletion/downline behavior, and performance. Map findings to this repo's existing learning_progress/resource_progress style.
- **Scope**: mixed
- **Date**: 2026-05-09

## Findings

### Files Found

| File Path | Description |
|---|---|
| `project_code/backend/app/models/learning.py` | Current `ResourceProgress` snapshot model for per-user/per-resource progress, including course/chapter/section/resource IDs, percent, position, completion, and last play time. |
| `project_code/backend/app/models/learning_progress.py` | Existing `LearningProgress` course-level snapshot model, imported by model registry but not found in active progress services during search. |
| `project_code/backend/app/services/learning_service.py` | Saves, reads, and returns `ResourceProgress`; current save path updates or creates one row per `(user_id, resource_id)`. |
| `project_code/backend/app/api/v1/learning.py` | Learning progress API endpoints: start learning, save progress, get progress, continue learning, play/preview resource. |
| `project_code/backend/app/schemas/learning.py` | Progress request/response schema; normalizes `current_time`, `position`, `total_time`, and `progress`. |
| `project_code/backend/app/services/user_service.py` | Builds learning-record list from `ResourceProgress` joined to courses/sections/resources. |
| `project_code/backend/app/api/v1/users.py` | Exposes `GET /users/me/learning-records`, scoped to `CurrentUserId`. |
| `project_code/backend/app/schemas/user.py` | `LearningRecordResponse` schema used by the profile learning-record list. |
| `project_code/backend/app/core/db_schema.py` | Compatibility behavior for nullable `resource_progress.section_id`, supporting chapter-level resources. |
| `project_code/backend/app/models/course.py` | Course status model (`draft`/`published`/`archived`) and course metadata used by learning records. |
| `project_code/backend/app/models/content.py` | Course content hierarchy: `Chapter`, `Section`, `Resource`; `Resource.section_id` is nullable for chapter-level resources. |
| `UI/src/api/learning.ts` | Frontend API contract for course detail, continue info, resource play URL, get/save progress. |
| `UI/src/composables/useProgressSync.ts` | Frontend progress sync strategy: high-frequency local updates, periodic sync, immediate sync, offline queue, and `sendBeacon`. |
| `UI/src/store/learn.ts` | Client-side current resource state and progress cache. |
| `UI/src/views/learn/LearningPage.vue` | Learning page wiring for progress sync, resource switching, completion, offline/online events, and archived-course guard. |
| `UI/src/api/profile.ts` | Frontend learning-record list contract. |
| `UI/src/views/profile/LearningRecordsPage.vue` | Profile learning records UI; shows archived course as disabled. |
| `.trellis/spec/backend/database-guidelines.md` | Backend DB conventions: SQLAlchemy async ORM, model style, service-owned queries, pagination, compatibility checks. |
| `.trellis/spec/guides/cross-layer-thinking-guide.md` | Cross-layer data-flow checklist relevant to analytics event ingestion and metric display contracts. |
| `.trellis/tasks/05-09-student-learning-analytics/prd.md` | Current task PRD for student learning analytics; notes existing progress rules and missing analytics design. |

### Code Patterns

#### Current repository shape: snapshot-based progress, not event-log analytics

The active backend progress model is a per-resource snapshot table:

- `project_code/backend/app/models/learning.py:13-31` defines `ResourceProgress` and table name `resource_progress`.
- `project_code/backend/app/models/learning.py:33-84` stores `user_id`, `course_id`, `chapter_id`, nullable `section_id`, `resource_id`, `progress`, `position`, `is_completed`, `completed_at`, and `last_play_at`.
- `project_code/backend/app/services/learning_service.py:111-155` queries by `user_id` + `resource_id`, then updates or creates the row.
- Completion currently becomes true when `data.is_completed` is true or progress percent is at least 95 (`project_code/backend/app/services/learning_service.py:132-136`, `149-151`).
- `project_code/backend/app/api/v1/learning.py:39-56` exposes save progress at `POST /learning/progress` and wraps it in `{ code, message, data }`.

A separate course-level `LearningProgress` snapshot model exists:

- `project_code/backend/app/models/learning_progress.py:13-29` defines `LearningProgress` and table `learning_progress`.
- `project_code/backend/app/models/learning_progress.py:30-66` stores course-level percent, last section, last position, total duration, and completion time.
- Search found no active service path writing this model; current learning-record aggregation uses `ResourceProgress` instead (`project_code/backend/app/services/user_service.py:149-210`).

#### Current record listing is derived from resource snapshots

- `project_code/backend/app/services/user_service.py:149-162` joins `ResourceProgress` with `Course`, `Section`, and `Resource`.
- `project_code/backend/app/services/user_service.py:173-210` orders by latest progress update, keeps the first row per course, then paginates in memory.
- `project_code/backend/app/api/v1/users.py:96-124` exposes this as `GET /users/me/learning-records`, using `CurrentUserId`, not arbitrary user ID.
- `UI/src/views/profile/LearningRecordsPage.vue:143-169` renders the last learned item and disables continue action when `course_status` is archived.

#### Current frontend capture behavior resembles a snapshot sync client

- `UI/src/composables/useProgressSync.ts:13-19` documents three layers: high-frequency player callback updates memory, 30-second reporting, immediate saves on key events.
- `UI/src/composables/useProgressSync.ts:47-90` builds a `SaveProgressRequest` with IDs, `current_time`, `total_time`, and `is_completed`, then calls `saveProgress`.
- `UI/src/composables/useProgressSync.ts:76-87` queues failed saves when offline.
- `UI/src/composables/useProgressSync.ts:128-147` uses `navigator.sendBeacon` on `beforeunload`.
- `UI/src/views/learn/LearningPage.vue:457-475` wires video/audio time update, pause, play, and ended events to progress sync and completion.
- `UI/src/views/learn/LearningPage.vue:432-436` marks documents/images completed when opened.
- `UI/src/views/learn/LearningPage.vue:260-265` prevents entering the learning page for non-published courses.

#### Existing deletion/downline behavior visible in code

- Course status supports `draft`, `published`, and `archived` (`project_code/backend/app/models/course.py:29`, `100-106`).
- Learning records include archived course status from the join (`project_code/backend/app/services/user_service.py:154-156`, `199-200`).
- The profile page displays archived records but disables continue (`UI/src/views/profile/LearningRecordsPage.vue:143-169`).
- The learning page redirects away from non-published courses (`UI/src/views/learn/LearningPage.vue:260-265`).
- `Resource.section_id` is nullable (`project_code/backend/app/models/content.py:170-174`), and `resource_progress.section_id` compatibility logic exists for chapter-level resources (`project_code/backend/app/core/db_schema.py:73-131`).

### Practical Data Modeling Approaches

#### 1. Event-log based tracking

**Shape**: append-only table or stream of learner actions. Typical event columns:

| Field group | Practical fields |
|---|---|
| Identity | `event_id`/idempotency key, `user_id`, `course_id`, `chapter_id`, `section_id`, `resource_id` |
| Event | `event_type` such as `resource_opened`, `play_started`, `play_paused`, `heartbeat`, `seeked`, `completed` |
| Time | server receipt time, client event time, optional client sequence number |
| Progress | `position_seconds`, `duration_seconds`, `progress_percent`, `playback_rate` |
| Context | device/session ID, app version, source (`web`, `beacon`, `offline_retry`) |
| Privacy-minimized metadata | coarse user agent/device class if needed; avoid raw IP/user agent unless required and governed |

**Metric accuracy**:

- Strongest option for reconstructing time-on-task, session counts, streaks, playback behavior, abandonment points, and repeated attempts.
- Accuracy depends on heartbeat interval, duplicate handling, client clock trust, and how seeking/background playback is interpreted.
- Event logs can explain why a metric changed because raw facts remain available.

**Privacy / permission boundaries**:

- Raw events are the most sensitive layer because they expose fine-grained behavior.
- Student self-view can use own raw-derived metrics; teacher view should normally be scoped to courses owned by that teacher and presented as per-student or aggregate according to product policy; admin view can access platform-level aggregates and limited drill-down.
- Event payloads should avoid collecting content unrelated to analytics, and should avoid storing unnecessary personal/device details.

**Idempotency**:

- Needs stable `event_id` or `(user_id, resource_id, session_id, client_seq)` uniqueness so retrying a failed POST does not double-count.
- Server-generated IDs alone do not deduplicate offline retries unless the client also sends a stable key.

**Offline / retry issues**:

- Works well with offline queues if each event has a client timestamp, sequence, and idempotency key.
- Late-arriving events require deterministic merge rules, e.g. aggregate by event time but ingest by server time.
- A `sendBeacon` final event can reduce loss on page close, but authentication and payload support must be validated in the actual browser/API setup.

**Course deletion / downline behavior**:

- If courses/resources are hard-deleted, event rows that only store foreign IDs lose context unless they also store immutable labels/snapshots or reference tombstone records.
- If courses are archived/downlined, event history can remain queryable while learning entry points are disabled, matching this repo's archived-record pattern.

**Performance**:

- Highest write volume; heartbeat events can be large for video learning.
- Requires indexes/partitioning by time, user, course, and possibly resource; raw-event queries should not power high-traffic dashboards directly.
- Best paired with asynchronous rollups for analytics pages.

#### 2. Progress snapshot tables

**Shape**: one current-state row per learner/resource or learner/course. This repo's `ResourceProgress` is the active example; `LearningProgress` is a course-level snapshot model.

**Metric accuracy**:

- Good for resume position, percent complete, latest activity, and simple completion state.
- Weak for true learning duration, session count, streaks, rewatches, seek behavior, and historical trend because intermediate states are overwritten.
- A snapshot can overstate or understate engagement if a retry overwrites a newer state with an older position.

**Privacy / permission boundaries**:

- Less sensitive than raw events because it stores only current/last state.
- Current repo's student learning-record endpoint is self-scoped through `CurrentUserId` (`project_code/backend/app/api/v1/users.py:102-115`).
- Teacher/admin analytics would need explicit scope rules because `ResourceProgress` contains direct `user_id` and course/resource IDs.

**Idempotency**:

- Simpler than event logs: repeated saves can update the same row.
- The active save path uses `(user_id, resource_id)` lookup (`project_code/backend/app/services/learning_service.py:111-119`), which naturally avoids duplicate rows for the same user/resource in normal operation.
- Snapshot idempotency still needs conflict rules for out-of-order retry, e.g. whether older `current_time` can overwrite newer progress.

**Offline / retry issues**:

- Offline retry can be handled by re-sending the latest known snapshot, but queues with multiple entries need ordering/merge rules.
- If only the last queued snapshot is needed for resume UX, intermediate offline events are not necessary; if time-on-task analytics matter, snapshots alone are insufficient.

**Course deletion / downline behavior**:

- Snapshot rows joined to live course/resource tables inherit the current course state.
- This repo already shows archived courses in profile records but disables continuing (`UI/src/views/profile/LearningRecordsPage.vue:143-169`).
- Hard deletion of courses/resources would break joins or remove display context unless cleanup, tombstones, or denormalized display fields exist.

**Performance**:

- Low write/read volume compared with events.
- Current indexed IDs on `ResourceProgress` support direct user/course/resource lookups (`project_code/backend/app/models/learning.py:33-56`).
- Course-level record listing currently derives latest course record from all matching resource rows and paginates after de-duplication in Python (`project_code/backend/app/services/user_service.py:178-210`), which is acceptable for small volumes but is a different scaling profile from precomputed analytics tables.

#### 3. Aggregate/stat tables

**Shape**: precomputed rows such as daily learner stats, course-resource stats, course-student stats, or platform daily stats. Typical keys and measures:

| Aggregate | Example key | Example measures |
|---|---|---|
| Student daily | `(user_id, date)` | active seconds, resources touched, completed resources, active courses |
| Student-course daily | `(user_id, course_id, date)` | learned seconds, resource completions, last position, sessions |
| Course daily | `(course_id, date)` | active learners, completions, average progress, total watch seconds |
| Resource daily | `(resource_id, date)` | starts, completions, median watched percent, drop-off buckets |
| Teacher course summary | `(teacher_id, course_id)` | learners, completion rate, recent active learners, average progress |

**Metric accuracy**:

- Accuracy depends on source data and rollup rules.
- If sourced only from snapshots, aggregates can count current state but not true time/session history.
- If sourced from events, aggregates can provide accurate dashboards while preserving raw-event auditability.

**Privacy / permission boundaries**:

- Aggregates are easier to expose to teachers/admins without revealing individual behavior.
- Small-group aggregates can still re-identify users; thresholds or suppression are common for course cohorts with very few learners.
- Student-facing aggregates can be keyed by own `user_id`; teacher-facing aggregates can be keyed by `teacher_id` or course ownership.

**Idempotency**:

- Rollups need deterministic inputs and windows.
- Event-sourced aggregates can track processed event offsets or recompute day windows idempotently.
- Snapshot-sourced aggregates need clear refresh semantics: full recompute, incremental update, or materialized snapshot.

**Offline / retry issues**:

- Aggregates should tolerate late arrivals by recomputing affected windows or applying idempotent event updates.
- If stats are updated directly from client calls, duplicate/offline retries can inflate counts unless guarded by event IDs or snapshot merge rules.

**Course deletion / downline behavior**:

- Aggregates can store denormalized course title/status/teacher at time of rollup, or join to course tombstones.
- Archived courses can remain in historical stats while disabled in learning flows.

**Performance**:

- Best for dashboards and trend pages.
- Adds write complexity and refresh jobs, but avoids scanning raw event logs or many progress rows for every request.
- Common pattern is raw facts -> rollup job -> small dashboard queries.

#### 4. Hybrid approach

**Shape**: combine layers with distinct jobs:

| Layer | Role |
|---|---|
| Event log | Durable analytic facts and replay/audit source. |
| `resource_progress` snapshot | Hot UX state for resume, current completion, and current task progress. |
| `learning_progress` course snapshot | Optional course-level current state for profile lists and course completion summaries. |
| Aggregate/stat tables | Fast student/teacher/admin analytics and trends. |

**Metric accuracy**:

- Event log gives historical fidelity; snapshots give current state; aggregate tables give performant trend queries.
- Hybrid keeps resume UX independent from expensive analytics calculations.

**Privacy / permission boundaries**:

- Raw event access can stay internal/admin-limited.
- Student APIs can read own snapshots and own aggregate rows.
- Teacher APIs can read course-owned aggregates and, if product requires, scoped learner rows for their own courses.
- Admin APIs can read platform-wide aggregates and limited raw/audit data according to policy.

**Idempotency**:

- Client events use `event_id`; snapshot updates use deterministic upserts; rollup processors track processed event IDs/windows.
- A single event may update both raw log and snapshot state, but each layer has its own dedupe semantics.

**Offline / retry issues**:

- Offline clients can queue events with stable IDs and also maintain the latest local snapshot for UX.
- On reconnect, the server can accept late events for analytics and merge the latest valid snapshot for resume.

**Course deletion / downline behavior**:

- Current repo behavior already distinguishes archived courses from deleted/unavailable courses in UI flows.
- Hybrid models can preserve historical facts even when a course is archived, while current snapshots/learning entry points obey `Course.status`.
- For hard deletion, raw/aggregate layers need retained minimal identifiers or tombstones if historical analytics must remain explainable.

**Performance**:

- More moving parts, but each query uses the right storage shape: one-row snapshot for resume, compact aggregates for dashboards, raw event log for audits/recompute.
- This is the most common shape when both real-time resume UX and explainable analytics are needed.

### Comparison Matrix

| Approach | Best for | Metric accuracy | Privacy boundary | Idempotency | Offline/retry behavior | Course archived/deleted behavior | Performance profile |
|---|---|---|---|---|---|---|---|
| Event log | Sessions, duration, behavior history, audit/replay | Highest if events are deduped and sequenced | Most sensitive; restrict raw access | Requires event IDs/sequence keys | Strong with queued events and stable IDs; late events need merge rules | Needs tombstones or denormalized labels for hard delete; archive can remain historical | High writes; raw scans expensive; best with rollups |
| Progress snapshot | Resume, latest progress, completion state | Good current-state accuracy; weak historical accuracy | Lower sensitivity than raw events | Upsert by user/resource or user/course | Can resend latest state; out-of-order retries can regress without merge rules | Joins to current course/resource state; archive display works, hard delete loses context | Simple and fast for UX; large course lists may need query optimization |
| Aggregate/stat tables | Dashboards and trends | Depends on source and refresh rules | Easier to expose with thresholds/scope | Deterministic recompute or processed-offset tracking | Recompute affected windows or apply idempotent updates | Can preserve historical stats with denormalized labels/tombstones | Fast reads; added background processing |
| Hybrid | Full analytics plus reliable resume UX | Strongest overall because each metric uses appropriate source | Raw internal; scoped snapshots/aggregates outward | Event dedupe + snapshot upsert + rollup checkpoints | Handles offline events and latest snapshot separately | Supports archived history and current access rules; hard delete still needs history policy | More complexity; best scalability for mixed UX/reporting |

### Mapping to This Repo's Existing `learning_progress` / `resource_progress` Style

1. **`resource_progress` already matches the progress snapshot layer.** It stores the latest known state per user/resource and is used by resume, current progress display, and profile learning records.
2. **`learning_progress` matches a course-level snapshot concept, but search found no active writer.** It can be understood as a potential course-current-state layer: progress percent, last section, last position, total duration, and completed time.
3. **The repo does not currently show an event-log layer for analytics.** Current frontend capture sends snapshots through `saveProgress`, not immutable analytic events.
4. **The repo does not currently show aggregate/stat tables for student/teacher/admin analytics.** Existing `Course.student_count`, `Course.rating`, `Resource.view_count`, and profile learning records are not a full learning analytics model.
5. **The frontend already has offline/retry capture hooks, but they are snapshot-oriented.** `offlineQueue` stores `SaveProgressRequest` items (`UI/src/composables/useProgressSync.ts:11-12`, `34-35`, `76-87`) rather than immutable events.
6. **Current archived-course behavior is compatible with historical learning records.** Archived courses are listed but cannot be continued from the profile page, and non-published courses are blocked in the learning page.
7. **The cross-layer contract is already important.** Frontend `SaveProgressRequest` currently omits `course_id` but sends section/resource/current/total/completion (`UI/src/api/learning.ts:111-118`), while backend schema accepts optional course/chapter/section plus resource/current/total/progress/completion (`project_code/backend/app/schemas/learning.py:18-29`) and derives course/chapter/section from `Resource` when omitted (`project_code/backend/app/services/learning_service.py:101-108`).

### Metric Suitability by Model

| Metric | Event log | Resource/course snapshot | Aggregate/stat table | Notes for this repo |
|---|---|---|---|---|
| Continue learning position | Possible but overkill | Strong | Not needed | Current `ResourceProgress.position` directly supports it. |
| Resource completion | Strong audit trail | Strong current state | Strong summary | Current backend uses `is_completed` or `progress >= 95`. |
| Course completion percent | Derivable | Possible via course-level snapshot or resource snapshots | Strong for reporting | Existing `LearningProgress.progress` model can represent course-level current state, but active code derives records from resource snapshots. |
| True active learning time | Strong with heartbeat/session events | Weak; overwritten snapshots cannot prove duration | Strong if event-sourced | Current `LearningProgress.total_duration` field exists, but active code does not write it. |
| Daily active streak | Strong | Weak unless snapshots are sampled daily | Strong | Requires event dates or daily stats. |
| Teacher course engagement | Strong but expensive raw | Limited latest-state view | Strong | Teacher boundary should be course ownership-based. |
| Drop-off point in video | Strong with heartbeat/position events | Weak latest position only | Strong if event-sourced | Current snapshots keep only the latest position. |
| Rewatch behavior | Strong | Not represented | Strong if event-sourced | Snapshot overwrites previous watches. |

### External References

- [ADL xAPI Specification](https://github.com/adlnet/xAPI-Spec) — Standardized learning activity statements using actor/verb/object style; relevant to event-log modeling for learning platforms.
- [1EdTech Caliper Analytics Specification](https://www.imsglobal.org/spec/caliper/v1p2) — Learning analytics event and metric profile specification; relevant for event vocabulary and role/resource modeling.
- [Snowplow: What is Snowplow?](https://docs.snowplow.io/docs/understanding-your-pipeline/what-is-snowplow/) — Event pipeline concepts relevant to append-only events, enrichment, and downstream modeling.
- [MDN Navigator.sendBeacon](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon) — Browser API used by the current frontend beforeunload progress fallback.
- [MDN Window online event](https://developer.mozilla.org/en-US/docs/Web/API/Window/online_event) — Browser online/offline events used by the current frontend progress sync flow.
- [GDPR.eu Data Minimization](https://gdpr.eu/data-minimization/) — Privacy principle relevant to collecting only analytics fields needed for defined metrics.

Note: URL reachability checks from this environment failed due local SSL certificate verification errors, so the references above were identified but not content-fetched during this session.

### Related Specs

- `.trellis/spec/backend/database-guidelines.md` — Confirms SQLAlchemy async ORM model conventions, service-owned queries, pagination shape, and compatibility-check expectations for table changes.
- `.trellis/spec/guides/cross-layer-thinking-guide.md` — Relevant for defining data flow from player events to backend storage to analytics UI, including boundary contracts and validation ownership.
- `.trellis/tasks/05-09-student-learning-analytics/prd.md` — Current task context: analytics design discussion only, with existing progress rules and missing analytics/reporting design called out.

## Caveats / Not Found

- `python3 ./.trellis/scripts/task.py current --source` is not supported by the script in this checkout; the research output path was taken from the user-provided task path.
- No active event-log learning analytics table was found in the searched backend/frontend code.
- No active aggregate/stat table for student/teacher/admin learning analytics was found in the searched backend/frontend code.
- `LearningProgress` exists as a model, but grep/read searches found current learning progress and profile records using `ResourceProgress` instead.
- External references were not fetched successfully because HTTPS certificate verification failed in the environment; they should be treated as identified reference targets rather than session-verified excerpts.
- This research did not modify code outside `.trellis/tasks/05-09-student-learning-analytics/research/`.
