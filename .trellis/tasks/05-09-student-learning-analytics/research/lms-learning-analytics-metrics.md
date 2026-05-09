# Research: LMS learning analytics metrics for student learning records

- **Query**: Research mature LMS / online course platform learning analytics metrics for student learning records. Goal: identify common statistics, dashboards, role-specific views, and metric definitions used in online learning video platforms. Map findings to this repo's context: student/teacher/admin roles; video/audio/document/image resources; existing progress saving every 30s; existing learning records list.
- **Scope**: mixed
- **Date**: 2026-05-09

## Findings

### Files Found

| File Path | Description |
|---|---|
| `UI/src/views/learn/LearningPage.vue` | Immersive learning page; switches video/audio/document/image resources, restores per-resource progress, displays active-task progress, auto-completes document/image resources, and starts 30s periodic progress sync. |
| `UI/src/composables/useProgressSync.ts` | Frontend progress syncing hook; saves `resource_id`, `section_id`, `chapter_id`, `current_time`, `total_time`, and `is_completed` every 30s while playing, plus immediate saves on pause/switch/leave and `sendBeacon` on unload. |
| `UI/src/api/learning.ts` | Frontend learning API contract and types for course detail, resource types (`video`, `audio`, `document`, `image`), continue learning, play URL, get/save progress. |
| `UI/src/views/profile/LearningRecordsPage.vue` | Student learning-record list; filters by `recent_7`, `recent_30`, `all`, displays course, last learned section/resource title, last learn time, course status, and continue button. |
| `UI/src/api/profile.ts` | Frontend profile API contract for `LearningRecordItem` and `fetchLearningRecords('/users/me/learning-records')`. |
| `UI/src/store/learn.ts` | Learning state store; keeps active resource state and local progress cache used by the learning page task list. |
| `project_code/backend/app/api/v1/learning.py` | Backend learning API routes: start learning, save/get progress, continue learning, play URL, preview URL. |
| `project_code/backend/app/services/learning_service.py` | Backend learning progress service; persists and returns resource-level progress, position, completion, timestamps, and continue-learning information. |
| `project_code/backend/app/models/learning.py` | `resource_progress` model; stores user/course/chapter/section/resource IDs, progress percentage, playback position, completion flag, completed time, last play time. |
| `project_code/backend/app/schemas/learning.py` | Pydantic request/response models; derives progress percentage from `current_time / total_time` when missing and treats explicit completion as 100%. |
| `project_code/backend/app/api/v1/users.py` | Backend profile route exposing `/users/me/learning-records` with time range and pagination. |
| `project_code/backend/app/services/user_service.py` | Learning-record list query; joins progress with course/section/resource and returns one latest record per course. |
| `project_code/backend/app/models/learning_progress.py` | Legacy/course-level `learning_progress` model with course progress, last section, last position, total duration, completed time; current searched service code uses `ResourceProgress` instead. |
| `.trellis/spec/frontend/index.md` | Frontend guideline index. |
| `.trellis/spec/backend/index.md` | Backend guideline index. |
| `.trellis/spec/guides/cross-layer-thinking-guide.md` | Cross-layer data-flow guide relevant because analytics spans resource events, storage, aggregation, and role dashboards. |

### Code Patterns

- **Resource progress is the current tracking grain.** `ResourceProgress` stores `user_id`, `course_id`, `chapter_id`, nullable `section_id`, `resource_id`, `progress`, `position`, `is_completed`, `completed_at`, and `last_play_at` (`project_code/backend/app/models/learning.py:13-87`). This maps naturally to resource-level analytics such as per-resource completion, last position, last activity, and resource progress percent.
- **Progress percentage definition already exists.** If the frontend sends only `current_time` and `total_time`, backend schema derives `progress = min((current_time / total_time) * 100, 100)`; if `is_completed` is true, progress becomes `100.0` (`project_code/backend/app/schemas/learning.py:31-59`). `LearningService.save_progress` also marks completed when `data.is_completed` or `progress_percent >= 95` (`project_code/backend/app/services/learning_service.py:125-152`).
- **Video/audio telemetry currently captures current position, not fine-grained events.** `LearningPage.vue` wires `timeupdate`, `pause`, `play`, and `ended` handlers for both video and audio (`UI/src/views/learn/LearningPage.vue:457-488`, `UI/src/views/learn/LearningPage.vue:853-887`). The hook only persists sampled state every 30s while `playState === 'playing'` and when pause/switch/leave happens (`UI/src/composables/useProgressSync.ts:93-147`). Mature event metrics like pause counts, replay/rewind counts, playback speed, and dwell time per segment would require event data that is not visible in the current persisted model.
- **Documents/images are marked completed on open.** The learning page calls `markResourceCompleted()` and immediately saves progress for `document` and `image` resources (`UI/src/views/learn/LearningPage.vue:432-436`). For those resource types, existing progress means completion/open status rather than time-on-page unless separate dwell/session events are captured.
- **Student learning records are course-level latest-resource summaries.** `/users/me/learning-records` returns the latest `ResourceProgress` per course after sorting by `updated_at` and `id`, with course title/cover/status, `progress`, total course duration, last section/resource title, timestamps, and completion time (`project_code/backend/app/services/user_service.py:149-210`). The frontend type currently displays only course ID/title/cover, last section title/time, and course status (`UI/src/api/profile.ts:49-58`; `UI/src/views/profile/LearningRecordsPage.vue:118-170`).
- **Teacher/admin analytics screens were not found by filename search.** Searches found course management and feedback management screens, but no `Analytics`, `Dashboard`, or statistics-specific learning analytics view under `UI/src/views`.

### Common LMS / Online Course Analytics Metrics

#### Student-facing learning record / dashboard metrics

| Metric | Common definition in mature LMS/video platforms | Mapping to this repo context |
|---|---|---|
| Courses in progress | Count/list of enrolled or started courses with at least one learning activity and not completed. | Can be derived from `resource_progress` grouped by `course_id` where not all resources are completed; current list already has latest record per course. |
| Completed courses | Count/list of courses where all required resources/sections are completed, or course progress meets threshold. | Current model has per-resource `is_completed`; course completion requires aggregating required resources. Existing `learning_progress.completed_at` model exists but current active service path uses resource progress. |
| Course progress percent | Completed required content divided by total required content, or weighted by duration for media resources. | Backend currently stores resource percent; course progress shown in records is the latest resource's `progress`, not necessarily aggregate course progress (`user_service.py:195-196`). Mature LMS dashboards usually distinguish resource progress from course completion percent. |
| Last activity / continue learning | Last accessed resource, timestamp, and resume position. | Directly supported by `get_continue_info` and records list: `last_resource_id`, `position/current_time`, `last_learn_at` (`learning_service.py:225-287`). |
| Learning time | Total active time spent learning in a selected period; for video/audio often watched seconds, for docs/images dwell time/session duration. | Current samples store playback position but not accumulated watched time or session duration. `learning_progress.total_duration` exists in legacy model but not in active `ResourceProgress` service flow. |
| Streak / active days | Number of consecutive days or distinct active days with learning activity. | Can be counted from `last_play_at`/`updated_at` dates, but only records latest per resource unless event/session history is retained. |
| Resource completion | Per video/audio/document/image completed state and percent. | Directly supported by `ResourceProgress.is_completed` and `progress`; document/image completion is currently immediate-on-open. |
| Recently learned items | Chronological resource/course activities with timestamp and title. | Current `/users/me/learning-records` collapses to one latest row per course; resource-level chronological history would need exposing multiple `ResourceProgress` rows or event history. |
| Time-period filters | 7 days, 30 days, all time; sometimes custom date range. | Current student record page already provides `recent_7`, `recent_30`, `all`. |

#### Teacher-facing course analytics metrics

| Metric | Common definition | Mapping to this repo context |
|---|---|---|
| Enrollment / learners | Number of learners enrolled/started in a course. | Course model/API expose `student_count` in several places; active learning starts can also be counted from distinct users in `resource_progress` per course. |
| Active learners | Distinct learners with activity in selected period. | Derivable from `ResourceProgress.last_play_at`/`updated_at` grouped by course and time window, noting lack of session/event history. |
| Completion rate | Completed learners / started or enrolled learners. | Requires course-level completion rule from resource completions. Current resource completion threshold is 95% or explicit completion. |
| Average progress | Mean course progress across learners. | Requires aggregate course progress per learner; existing records contain resource progress, not full course progress. |
| Average learning time | Mean/sum active learning duration per learner/resource/course. | Not directly available from current active model; playback position is not equivalent to time spent because seek/replay can distort it. |
| Resource engagement | Views/starts/completions/drop-off per resource; video watch percent; document/image opens. | Starts/completions can be approximated from `ResourceProgress` rows; fine-grained video drop-off and replay require event or segment data. Resource model has `view_count` field for content but current learning progress flow is the richer learner-specific source. |
| At-risk learners | Learners with low/no recent activity, low progress, poor grades, or missed deadlines. | No assessment/deadline data surfaced in searched learning code; low/no recent activity could be derived from stale `last_play_at`. |
| Heatmap / timeline | Distribution of views, pauses, rewinds, drop-offs by video time segment or by calendar date. | Current 30s state save does not persist enough event/segment detail for heatmaps. Calendar activity counts can be approximated only from latest resource timestamps. |

#### Admin-facing platform analytics metrics

| Metric | Common definition | Mapping to this repo context |
|---|---|---|
| Total learners / teachers / courses | Platform-level user/course inventory by role/status. | Admin user/course modules exist; not specific to learning analytics. |
| DAU/WAU/MAU learners | Distinct active learners in day/week/month. | Can be based on distinct `user_id` in `resource_progress` updated in period; exact activity frequency requires event/session history. |
| Course popularity | Views, starts, active learners, completions, enrollments. | `student_count` and course sorting by popularity exist; starts/completions can be grouped from progress records. |
| Content utilization | Resource opens/plays/completions by type and course/category. | Resource type is available through `Resource`; progress records identify resources. Counts are limited to latest per user-resource state, not every access. |
| Completion funnel | Started -> in progress -> completed by course/category/teacher. | Start/in-progress/completion can be estimated from progress rows and resource completion aggregation. |
| Platform learning time | Total active media play time / session time by period. | Not directly available without accumulated duration/session/event data. |

### Metric Definitions Suited to This Repo's Existing Data

These definitions describe what mature platforms usually show and whether this repo's currently visible data can support them:

| Proposed metric definition | Data inputs visible now | Support level |
|---|---|---|
| `resource_progress_percent = min(current_time / total_time * 100, 100)` for media resources, or `100` when marked complete. | `SaveProgressRequest.current_time`, `total_time`, `progress`, `is_completed`; schema validator. | Directly supported. |
| `resource_completed = is_completed OR progress >= 95`. | Backend save logic. | Directly supported. |
| `last_learning_at = ResourceProgress.last_play_at or updated_at`. | `ResourceProgress.last_play_at`, `updated_at`; user service records query. | Directly supported. |
| `continue_position_seconds = ResourceProgress.position`. | `ResourceProgress.position`; continue-learning response. | Directly supported. |
| `started_courses = distinct course_id with any ResourceProgress row for user`. | `resource_progress` rows. | Directly supported. |
| `active_days = distinct date(last_play_at or updated_at)` in period. | Current state table timestamps. | Partially supported; only latest per user-resource state remains, so repeated sessions on same resource are not retained. |
| `course_completion_percent = completed required resources / total required resources`. | `ResourceProgress.is_completed` plus course content resources. | Supported if required-resource denominator is defined; not shown in searched code. |
| `media_watch_time_seconds = sum active playback seconds`. | Need session/event duration; current `position` is resume location. | Not directly supported. |
| `video_engagement_heatmap = count/seconds watched per timeline segment`. | Need media event/segment tracking. | Not supported by current persisted model. |
| `document/image dwell_time_seconds`. | Need open/close/session duration. | Not supported; current code marks complete on open. |
| `pause_count`, `seek_count`, `rewatch_count`, `playback_speed_usage`. | Need event tracking. | Not supported by current persisted model. |

### Role-Specific View Patterns Seen in Mature LMS / Video Platforms

| Role | Common dashboard/list patterns | Repo-specific mapping notes |
|---|---|---|
| Student | Learning record timeline; continue learning; course progress cards; completed/in-progress course tabs; total learning time; active days/streak; per-course resource checklist. | Current student page already has latest course records, time filters, and continue learning. It does not display aggregate course completion, active days, or total learning time from visible code. |
| Teacher | Course analytics dashboard; learner roster with progress/completion/last activity; resource engagement table; at-risk list; exports. | Teacher course list exists, but no learning analytics/dashboard view was found by search. Existing `ResourceProgress` supports roster-style last activity/progress and resource completion counts with aggregation. |
| Admin | Platform overview; course popularity; active users; completion funnel; role/course/category breakdown; content type usage; trend charts. | Admin management pages exist, but no platform learning analytics dashboard was found. `student`/`teacher`/`admin` roles and course/resource metadata allow grouping if aggregation endpoints exist. |

### External References

- [Moodle Analytics API](https://moodledev.io/docs/5.1/apis/subsystems/analytics) — Moodle documents analytics models with indicators and targets; examples include courses without teaching activity, students not accessing courses, low participation, poor grades, and course completion prediction.
- [Canvas LMS analytics guides](https://community.canvaslms.com/t5/Instructor-Guide/tkb-p/Instructor#analytics) — Canvas instructor analytics commonly center on course activity, submissions, grades, and student-level course analytics. Direct fetched guide URLs were unstable/redirected during research, so use the Canvas Instructor Guide analytics index/search as the stable entry point.
- [Open edX Insights documentation](https://docs.openedx.org/en/latest/site_ops/install_configure_run_guide/insights/index.html) — Open edX historically provided Insights as a learning analytics application; the current docs mark it deprecated, but it remains useful as an example of platform-level learner/activity reporting.
- [1EdTech Caliper Analytics 1.2 Specification](https://www.imsglobal.org/spec/caliper/v1p2) — Defines learning event model and metric profiles including Assessment, Media, Reading, Session, Tool Use, etc. Media examples include knowing which videos are played most, how long students spend on each video, pauses, and replays.
- [ADL Experience API (xAPI)](https://adlnet.gov/projects/xapi/) — xAPI frames learning activity data as more than completions, scores, and page views; relevant when considering event-level activity records across videos/documents and other resources.
- [SCORM Run-Time Reference](https://scorm.com/scorm-explained/technical-scorm/run-time/run-time-reference/) — SCORM's runtime data model is a useful historical reference for LMS fields like lesson status/completion, score, session time, total time, and suspend/resume data. The site returned HTTP 403 to the fetch script, but the reference is widely used for LMS metric definitions.

### Related Specs

- `.trellis/spec/frontend/index.md` — Frontend guideline index; lists frontend directory, component, hook, state, quality, and type-safety docs.
- `.trellis/spec/backend/index.md` — Backend guideline index; lists backend directory, database, error-handling, quality, and logging docs.
- `.trellis/spec/guides/cross-layer-thinking-guide.md` — Relevant guide for analytics because metrics require explicit Source → Transform → Store → Retrieve → Transform → Display contracts across frontend events, backend schemas, database rows, aggregation services, and role-specific UI.

## Caveats / Not Found

- The Trellis helper command `python3 ./.trellis/scripts/task.py current --source` is not available in this worktree; it returned an invalid-command error. The user-provided output path was used, and the research directory was created as allowed.
- No code changes were made outside the requested task research directory.
- No dedicated teacher/admin learning analytics dashboard files were found by filename or term search under `UI/src/views`; existing teacher/admin files appear to be management/feedback/course screens.
- Existing visible code stores latest state per user-resource, not append-only event/session history. Metrics requiring true learning time, repeated visits, heatmaps, pause/seek/replay counts, or document dwell time cannot be derived accurately from the current persisted model alone.
- External web fetching was limited by SSL/403/redirect issues for some sites; references above include stable public documentation entry points and notes where direct fetch was blocked or unstable.
