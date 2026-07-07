# Research: Backend Foundation Code Map

- **Query**: Research the backend codebase for the learning statistics foundation implementation plan. Focus on current models, routes, services, schemas, migrations/init scripts, and operations-log requirements for: ResourceProgress, LearningProgress, Resource, learning records, content resource create/update, course publish validation, and daily/stat aggregation patterns if any.
- **Scope**: internal
- **Date**: 2026-05-09

## Findings

### Files Found

| File Path | Description |
|---|---|
| `project_code/backend/app/models/learning.py` | Defines `ResourceProgress` table `resource_progress` for per-resource progress. |
| `project_code/backend/app/models/learning_progress.py` | Defines `LearningProgress` table `learning_progress` for course-level progress, exported but not used by current services found. |
| `project_code/backend/app/models/content.py` | Defines `Chapter`, `Section`, and `Resource`; `Resource.section_id` is nullable for chapter-level resources. |
| `project_code/backend/app/models/course.py` | Defines `Course`, `CourseMaterial`, `CourseTag`; course has status/duration/section/student/rating counters. |
| `project_code/backend/app/models/__init__.py` | Exports `LearningProgress`, `ResourceProgress`, `Resource`, `Course`, and related models for metadata initialization. |
| `project_code/backend/app/schemas/learning.py` | Defines save/get progress request/response schemas and frontend field normalization. |
| `project_code/backend/app/schemas/content.py` | Defines chapter/section/resource schemas; `ResourceCreate` supports `resource_type` and `file_name` aliases. |
| `project_code/backend/app/schemas/course.py` | Defines course schemas, management/batch schemas, and list response `view_count` compatibility field. |
| `project_code/backend/app/schemas/user.py` | Defines `LearningRecordResponse` for `/users/me/learning-records`. |
| `project_code/backend/app/api/v1/learning.py` | Learning routes: start, save/get progress, continue, play URL, preview URL. |
| `project_code/backend/app/api/v1/content.py` | Content routes for chapters, sections, and resource creation/deletion. |
| `project_code/backend/app/api/v1/courses.py` | Course CRUD/list/detail/publish/archive/batch/material routes. |
| `project_code/backend/app/api/v1/users.py` | User routes including `/users/me/learning-records`. |
| `project_code/backend/app/api/v1/router.py` | Mounts `courses`, `content`, `learning`, `users`, and other route modules under v1. |
| `project_code/backend/app/services/learning_service.py` | Core `ResourceProgress` business logic for saving/querying progress and continue info. |
| `project_code/backend/app/services/content_service.py` | Chapter/section/resource service logic, including duration/count maintenance. |
| `project_code/backend/app/services/course_service.py` | Course service logic, publish/archive/delete validation, chapter tree serialization. |
| `project_code/backend/app/services/user_service.py` | Builds learning records from latest `ResourceProgress` rows joined to course/section/resource. |
| `project_code/backend/app/core/db_schema.py` | Startup/init compatibility checks; adjusts `resources.section_id` and `resource_progress.section_id` nullable behavior. |
| `project_code/backend/scripts/init_db.py` | Creates tables from `Base.metadata` and runs `ensure_database_compatibility`. |
| `project_code/backend/scripts/seed_data.py` | Seeds users/courses/chapters/sections/resources; does not seed progress/stat rows. |
| `project_code/backend/tests/test_learning.py` | Tests progress APIs, including chapter-level resource progress where `section_id is None`. |
| `project_code/backend/tests/test_content.py` | Tests chapter/section/resource APIs, aliases, chapter-level resources, and duration/count effects. |
| `project_code/backend/tests/test_courses.py` | Tests course detail/resources, publish/archive/batch action behavior. |
| `project_code/CLAUDE.md` | Backend rule requiring `operations-log.md` update when backend files change. |
| `.trellis/spec/backend/database-guidelines.md` | Backend database conventions and current non-migration workflow note. |
| `.trellis/spec/backend/quality-guidelines.md` | Backend validation and operations-log checklist. |
| `.trellis/spec/backend/directory-structure.md` | Backend file placement and required checks. |

### Code Patterns

#### ResourceProgress model and usage

- `project_code/backend/app/models/learning.py:13` defines `class ResourceProgress(BaseModel)` with table name `resource_progress` at `project_code/backend/app/models/learning.py:31`.
- Columns are per user/course/chapter/resource, with nullable `section_id` for chapter-level resources: `user_id`, `course_id`, `chapter_id`, `section_id`, `resource_id`, `progress`, `position`, `is_completed`, `completed_at`, `last_play_at` at `project_code/backend/app/models/learning.py:33` through `project_code/backend/app/models/learning.py:84`.
- `project_code/backend/app/services/learning_service.py:13` imports `ResourceProgress` from `app.models.learning`.
- `save_progress` loads `Resource` first, derives missing `course_id/chapter_id/section_id` from the resource, then upserts by `(user_id, resource_id)` at `project_code/backend/app/services/learning_service.py:101` through `project_code/backend/app/services/learning_service.py:155`.
- Completion threshold is service-level: existing or new progress becomes completed when `data.is_completed` is true or `progress_percent >= 95` at `project_code/backend/app/services/learning_service.py:132` and `project_code/backend/app/services/learning_service.py:149`.
- Progress response serialization maps `position` to both `position` and `current_time`, and `last_play_at` to both `last_play_at` and `last_learn_at` at `project_code/backend/app/services/learning_service.py:23` through `project_code/backend/app/services/learning_service.py:36`.

#### LearningProgress model status

- `project_code/backend/app/models/learning_progress.py:13` defines `LearningProgress` table `learning_progress` with course-level fields: `user_id`, `course_id`, `progress`, `last_section_id`, `last_position`, `total_duration`, and `completed_at` at `project_code/backend/app/models/learning_progress.py:30` through `project_code/backend/app/models/learning_progress.py:66`.
- `project_code/backend/app/models/__init__.py:16` exports `LearningProgress`, but searches found no service/route imports or writes to this model outside model exports.
- Current learning APIs and user learning-records use `ResourceProgress`, not `LearningProgress` (`project_code/backend/app/services/learning_service.py:13`; `project_code/backend/app/services/user_service.py:22`).

#### Resource model and content resource create/delete

- `project_code/backend/app/models/content.py:139` defines `Resource` table `resources`; `section_id` is `Mapped[int | None]` and nullable at `project_code/backend/app/models/content.py:170` through `project_code/backend/app/models/content.py:174`.
- `Resource` stores `course_id`, `chapter_id`, `section_id`, `title`, `type`, `file_url`, `file_size`, `duration`, `sort_order`, `is_free`, and `view_count` at `project_code/backend/app/models/content.py:160` through `project_code/backend/app/models/content.py:219`.
- `ResourceCreate` accepts `type` plus frontend aliases `resource_type` and `file_name`; `normalize_frontend_payload` copies `resource_type -> type` and `file_name -> title` when canonical fields are absent at `project_code/backend/app/schemas/content.py:175` through `project_code/backend/app/schemas/content.py:233`.
- `ResourceResponse` emits both canonical and frontend-compatible fields (`id/resource_id`, `title/file_name`, `type/resource_type`) at `project_code/backend/app/schemas/content.py:236` through `project_code/backend/app/schemas/content.py:256`.
- Chapter-level resource route: `POST /courses/{course_id}/chapters/{chapter_id}/resources` in `project_code/backend/app/api/v1/content.py:265` through `project_code/backend/app/api/v1/content.py:288`; service creates `section_id=None` at `project_code/backend/app/services/content_service.py:490` through `project_code/backend/app/services/content_service.py:529`.
- Section-level resource route: `POST /courses/{course_id}/sections/{section_id}/resources` in `project_code/backend/app/api/v1/content.py:291` through `project_code/backend/app/api/v1/content.py:318`; service increments `section.resource_count`, section/chapter/course video duration counters at `project_code/backend/app/services/content_service.py:425` through `project_code/backend/app/services/content_service.py:488`.
- Resource delete route exists for section resources at `project_code/backend/app/api/v1/content.py:320` through `project_code/backend/app/api/v1/content.py:335`, plus legacy POST delete routes for chapter and section resources at `project_code/backend/app/api/v1/content.py:338` through `project_code/backend/app/api/v1/content.py:373`.
- Resource deletion decrements section resource count and video durations for section/chapter/course as applicable at `project_code/backend/app/services/content_service.py:531` through `project_code/backend/app/services/content_service.py:565`.
- No `ResourceUpdate` schema, resource update service method, or resource update route was found; searches for `ResourceUpdate`, `update_resource`, and resource update routes returned only delete/create matches.

#### Learning routes and schemas

- Learning router prefix is `/learning` at `project_code/backend/app/api/v1/learning.py:20`; v1 router includes it at `project_code/backend/app/api/v1/router.py:26`.
- Routes found:
  - `POST /learning/courses/{course_id}/start` at `project_code/backend/app/api/v1/learning.py:23` through `project_code/backend/app/api/v1/learning.py:36`.
  - `POST /learning/progress` at `project_code/backend/app/api/v1/learning.py:39` through `project_code/backend/app/api/v1/learning.py:56`.
  - `GET /learning/progress` at `project_code/backend/app/api/v1/learning.py:59` through `project_code/backend/app/api/v1/learning.py:85`.
  - `GET /learning/courses/{course_id}/continue` at `project_code/backend/app/api/v1/learning.py:88` through `project_code/backend/app/api/v1/learning.py:101`.
  - `GET /learning/resources/{resource_id}/play` at `project_code/backend/app/api/v1/learning.py:104` through `project_code/backend/app/api/v1/learning.py:117`.
  - `GET /learning/resources/{resource_id}/preview` at `project_code/backend/app/api/v1/learning.py:120` through `project_code/backend/app/api/v1/learning.py:133`.
- `SaveProgressRequest` accepts optional `course_id`, `chapter_id`, nullable `section_id`, required `resource_id`, and either `position/current_time` plus `progress/total_time/is_completed`; it derives missing `position/current_time` and progress at `project_code/backend/app/schemas/learning.py:18` through `project_code/backend/app/schemas/learning.py:59`.
- `get_progress` requires at least `course_id` or `resource_id` and returns either a list or a single resource progress payload when only `resource_id` is supplied at `project_code/backend/app/services/learning_service.py:177` through `project_code/backend/app/services/learning_service.py:223`.
- Continue learning selects the most recently updated `ResourceProgress` row for a course and returns section/resource info, including `last_section_id=None` for chapter-level resources at `project_code/backend/app/services/learning_service.py:241` through `project_code/backend/app/services/learning_service.py:287`.

#### Learning records

- Route `GET /users/me/learning-records` is defined at `project_code/backend/app/api/v1/users.py:96` through `project_code/backend/app/api/v1/users.py:124` and returns `PageData[LearningRecordResponse]`.
- `LearningRecordResponse` fields are `id`, `course_id`, `course_title`, `course_name`, `course_cover`, `progress`, `total_duration`, `last_section_id`, `last_section_title`, `last_learn_at`, `course_status`, `completed_at`, `created_at`, and `updated_at` at `project_code/backend/app/schemas/user.py:116` through `project_code/backend/app/schemas/user.py:134`.
- `UserService.get_learning_records` queries `ResourceProgress` joined to `Course`, optional `Section`, and optional `Resource` at `project_code/backend/app/services/user_service.py:149` through `project_code/backend/app/services/user_service.py:162`.
- Time filters are `recent_7`, `recent_30`, and `all`; filters apply to `ResourceProgress.updated_at` at `project_code/backend/app/services/user_service.py:164` through `project_code/backend/app/services/user_service.py:172`.
- Records are ordered by latest progress update, deduplicated in Python by course ID, then paginated in memory at `project_code/backend/app/services/user_service.py:173` through `project_code/backend/app/services/user_service.py:210`.
- `total_duration` in this response currently uses `Course.total_duration`, not accumulated watch time, at `project_code/backend/app/services/user_service.py:154` and `project_code/backend/app/services/user_service.py:196`.

#### Course publish validation

- `Course` stores `status`, `total_duration`, `total_sections`, `student_count`, `rating`, `rating_count`, and `published_at` at `project_code/backend/app/models/course.py:100` through `project_code/backend/app/models/course.py:145`.
- `CourseService._ensure_publishable` checks only that the course is not already published and that both `title` and `description` are present at `project_code/backend/app/services/course_service.py:50` through `project_code/backend/app/services/course_service.py:55`.
- `CourseService.publish` enforces teacher ownership via `_can_publish_course`, calls `_ensure_publishable`, sets `status="published"`, and sets `published_at` to current UTC time at `project_code/backend/app/services/course_service.py:271` through `project_code/backend/app/services/course_service.py:280`.
- Batch publish uses the same ownership and `_ensure_publishable` logic inside `batch_action` at `project_code/backend/app/services/course_service.py:317` through `project_code/backend/app/services/course_service.py:323`.
- The course publish route is `POST /courses/{course_id}/publish` at `project_code/backend/app/api/v1/courses.py:302` through `project_code/backend/app/api/v1/courses.py:315`.

#### Course detail and resource tree serialization

- `CourseService.get_chapters_with_sections` loads all chapters, sections, and resources for a course, separates chapter-level resources (`section_id is None`) from section resources, and emits nested `ChapterWithSections`/`SectionResponse`/`ResourceResponse` at `project_code/backend/app/services/course_service.py:133` through `project_code/backend/app/services/course_service.py:220`.
- It computes chapter duration as section durations plus chapter-level video resource durations, then uses `max(chapter.total_duration, computed_duration)` at `project_code/backend/app/services/course_service.py:201` through `project_code/backend/app/services/course_service.py:213`.
- Course detail route includes `materials`, `chapters`, and computed `total_sections/total_duration` at `project_code/backend/app/api/v1/courses.py:199` through `project_code/backend/app/api/v1/courses.py:249`.

#### Init scripts and migration/compatibility pattern

- There is no migration framework found under `project_code/backend`; `.trellis/spec/backend/database-guidelines.md:10` states the project currently does not use a migration framework as the primary workflow and uses startup schema checks such as `app/core/db_schema.py`.
- `scripts/init_db.py` runs `Base.metadata.create_all` and then `ensure_database_compatibility(conn)` at `project_code/backend/scripts/init_db.py:35` through `project_code/backend/scripts/init_db.py:40`.
- `ensure_database_compatibility` checks/updates historical columns with raw `ALTER TABLE`/rebuild operations at `project_code/backend/app/core/db_schema.py:14` through `project_code/backend/app/core/db_schema.py:183`.
- For `resources.section_id`, MySQL compatibility changes the column to nullable; non-MySQL emits a manual-check message at `project_code/backend/app/core/db_schema.py:53` through `project_code/backend/app/core/db_schema.py:71`.
- For `resource_progress.section_id`, MySQL compatibility changes the column to nullable; SQLite compatibility rebuilds the table, copies rows, recreates indexes, and drops the old table at `project_code/backend/app/core/db_schema.py:73` through `project_code/backend/app/core/db_schema.py:131`.
- `scripts/seed_data.py` creates users, categories, tags, courses, chapters, sections, resources, and announcements at `project_code/backend/scripts/seed_data.py:34` through `project_code/backend/scripts/seed_data.py:317`; no `ResourceProgress`, `LearningProgress`, or statistics rows are seeded.

#### Daily/stat aggregation patterns

- No dedicated daily/statistics models, route modules, services, or schemas were found in `project_code/backend/app` by searches for `daily`, `statistics`, `aggregate`, `aggregation`, and `group_by`.
- Existing `func.count()` patterns are primarily pagination totals, for example `CourseService.get_list` count query at `project_code/backend/app/services/course_service.py:78` through `project_code/backend/app/services/course_service.py:80`, `get_manage_courses` at `project_code/backend/app/services/course_service.py:120` through `project_code/backend/app/services/course_service.py:122`, and `UserService.get_user_list` at `project_code/backend/app/services/user_service.py:249` through `project_code/backend/app/services/user_service.py:252`.
- Learning records deduplicate latest course records in Python rather than by SQL aggregation at `project_code/backend/app/services/user_service.py:179` through `project_code/backend/app/services/user_service.py:210`.

#### Operations-log requirements

- `project_code/CLAUDE.md:164` through `project_code/CLAUDE.md:169` requires checking whether `operations-log.md` must be updated before adding/modifying files; any file addition/change under the backend project requires appending `project_code/operations-log.md` with change time, reason, files, core changes, and verification result.
- Root `CLAUDE.md` repeats that backend file changes must update `project_code/operations-log.md` at `CLAUDE.md:296` through `CLAUDE.md:325`.
- `.trellis/spec/backend/quality-guidelines.md:92` through `.trellis/spec/backend/quality-guidelines.md:104` repeats the same operations-log requirement and says API/architecture behavior changes should update relevant docs when applicable.
- `.trellis/spec/backend/quality-guidelines.md:108` through `.trellis/spec/backend/quality-guidelines.md:120` includes `project_code/operations-log.md` update in the backend completion checklist.
- `.trellis/spec/backend/directory-structure.md:221` through `.trellis/spec/backend/directory-structure.md:230` says new backend files should be placed in existing slices when possible, route modules must be registered, responses wrapped, and operations-log updated for backend file changes.

### External References

- None. This was an internal codebase research task.

### Related Specs

- `.trellis/spec/backend/database-guidelines.md` — async SQLAlchemy model/query conventions; notes no primary migration framework and compatibility adjustments via `app/core/db_schema.py`.
- `.trellis/spec/backend/quality-guidelines.md` — backend testing, response contracts, and operations-log requirements.
- `.trellis/spec/backend/directory-structure.md` — backend route/service/schema/model/test placement and required checks.
- `.trellis/spec/guides/cross-layer-thinking-guide.md` — relevant if statistics API fields are later exposed to frontend, though not read in detail for this backend-only code map.

## Caveats / Not Found

- `python3 ./.trellis/scripts/task.py current --source` is not supported by this repository's `task.py`; the user supplied explicit target path `.trellis/tasks/05-09-learning-statistics-foundation/research/backend-foundation-code-map.md`, so this research was persisted there.
- No current `LearningProgress` service/route usage was found; current progress and learning-record flows use `ResourceProgress`.
- No resource update endpoint/schema/service method was found, only resource creation and deletion.
- No daily/stat aggregation implementation was found; existing count patterns are pagination/list support rather than learning-stat aggregation.
- Research file only was modified; backend code and `project_code/operations-log.md` were not modified.
