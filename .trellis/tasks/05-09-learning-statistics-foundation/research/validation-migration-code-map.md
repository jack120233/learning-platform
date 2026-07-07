# Research: validation migration code map

- **Query**: Research existing validation, tests, database initialization/migration patterns, and scheduler/background job patterns relevant to the learning statistics foundation. Focus on pytest fixtures, current learning/user/content tests, scripts/init_db.py, seed data, any migration conventions, and whether cron/scheduler infrastructure exists.
- **Scope**: internal
- **Date**: 2026-05-09

## Findings

### Files Found

| File Path | Description |
|---|---|
| `project_code/backend/tests/conftest.py` | Shared async pytest infrastructure, in-memory SQLite engine, DB dependency override, auth/header/user/course fixtures. |
| `project_code/backend/tests/test_learning.py` | Learning progress API tests for start/progress/save/continue and chapter-level resource progress. |
| `project_code/backend/tests/test_users.py` | User profile and learning-record API tests; verifies `/users/me/learning-records` aggregates from `ResourceProgress`. |
| `project_code/backend/tests/test_content.py` | Content hierarchy and resource tests; creates Course → Chapter → Section → Resource records and checks counts/sort/resource routes. |
| `project_code/backend/tests/test_permissions.py` | Contains compatibility test for role permission cleanup via `ensure_database_compatibility`. |
| `project_code/backend/tests/test_feedbacks.py` | Contains compatibility test for adding missing `feedbacks` columns via `ensure_database_compatibility`. |
| `project_code/backend/scripts/init_db.py` | First-deploy DB init script: creates all metadata tables and runs schema compatibility checks. |
| `project_code/backend/scripts/seed_data.py` | Seed script for users, categories, tags, courses, chapters, sections, resources, and announcements. |
| `project_code/backend/scripts/migrate_author.py` | One-off async migration script adding `courses.author` if missing. |
| `project_code/backend/app/core/db_schema.py` | Startup/init compatibility checks: adds missing columns, adjusts nullable fields, rebuilds SQLite `resource_progress`, and normalizes role permissions. |
| `project_code/backend/app/main.py` | FastAPI lifespan runs `ensure_database_compatibility` on startup; no scheduler startup code found. |
| `project_code/backend/app/core/dependencies.py` | Async SQLAlchemy engine/session factory and `get_db` dependency with commit/rollback lifecycle. |
| `project_code/backend/app/models/base.py` | Shared declarative base, ID/timestamp/soft-delete mixins, `BaseModel` with eager defaults. |
| `project_code/backend/app/models/learning.py` | Active `ResourceProgress` table model used for resource-level learning progress and records. |
| `project_code/backend/app/models/learning_progress.py` | Older/course-level `LearningProgress` model; exported, but current searched learning/user services use `ResourceProgress`. |
| `project_code/backend/app/services/learning_service.py` | Business logic for start/save/get progress and continue learning, based on `ResourceProgress`. |
| `project_code/backend/app/services/user_service.py` | Learning-record query joins `ResourceProgress`, `Course`, `Section`, and `Resource` and deduplicates latest record per course in Python. |
| `project_code/backend/app/api/v1/learning.py` | Learning API routes under `/api/v1/learning`. |
| `project_code/backend/app/api/v1/users.py` | `/api/v1/users/me/learning-records` route wrapping `user_service.get_learning_records` in paginated response. |
| `project_code/backend/app/schemas/learning.py` | Pydantic validation for learning progress requests/responses, including progress/current_time normalization. |
| `project_code/backend/app/schemas/user.py` | `LearningRecordResponse` schema for profile learning records. |
| `project_code/backend/app/api/v1/router.py` | v1 router aggregation includes learning/users/content modules. |
| `project_code/backend/requirements.txt` | Dependencies include pytest/pytest-asyncio/httpx and Alembic package, but no scheduler package found. |
| `.trellis/spec/backend/database-guidelines.md` | Backend database conventions; states migrations are not the primary workflow and compatibility checks live in `app/core/db_schema.py`. |
| `.trellis/spec/backend/quality-guidelines.md` | Backend test/layering/response conventions and relevant pytest commands. |

### Code Patterns

#### Pytest fixtures and validation harness

- `tests/conftest.py` defines test DB as `sqlite+aiosqlite:///:memory:`.
- `tests/conftest.py` creates a session-scoped async engine, runs `Base.metadata.create_all`, then drops all tables and disposes the engine at session end.
- Per-test `AsyncSession` rolls back after each test.
- `get_db` is overridden via `app.dependency_overrides[get_db]`; `httpx.AsyncClient` uses `ASGITransport(app=app)`.
- Reusable fixtures include `test_user`, `test_teacher`, `test_admin`, role tokens/headers, `test_category`, and `test_course`.
- Response assertion helpers check the project response contract (`code`, optional `message`).

#### Existing learning/content/user test construction patterns

- `tests/test_learning.py` exercises start/get/save progress by creating `Category`, `Course`, `Chapter`, `Section`, captcha records, login token, then calling `/api/v1/learning/...` endpoints.
- The stricter chapter-level resource progress test creates a `Resource` with `section_id=None`, saves progress with `chapter_id` and `resource_id`, asserts response payload fields, fetches progress by `resource_id`, and verifies continue-learning fields.
- `tests/test_users.py` verifies learning-record aggregation from `ResourceProgress` for section resources and chapter-level resources.
- `tests/test_content.py` uses direct ORM creation plus route assertions for sorting/deletion/resource creation/count fields.

#### Current learning-progress data flow

- `ResourceProgress` stores resource-level progress with nullable `section_id`, `progress`, `position`, `is_completed`, `completed_at`, and `last_play_at`.
- `LearningProgress` stores course-level fields, but current learning-record and progress services/tests are based on `ResourceProgress`.
- `learning_service.save_progress` loads `Resource`, derives hierarchy, upserts `ResourceProgress`, and marks complete when `data.is_completed` or progress reaches 95%.
- `learning_service.get_progress` returns default zero progress if no resource progress exists.
- `learning_service.get_continue_learning` selects latest `ResourceProgress` by `updated_at desc`.
- `user_service.get_learning_records` builds records from `ResourceProgress` joined to course/section/resource, filters by `recent_7` / `recent_30` / `all`, deduplicates by course in Python, then paginates.

#### Database initialization and compatibility/migration patterns

- `scripts/init_db.py` runs `Base.metadata.create_all`, then `ensure_database_compatibility(conn)`, then prints table names.
- `app/main.py` runs `ensure_database_compatibility(conn)` on startup inside FastAPI lifespan.
- `app/core/db_schema.py` is the main compatibility convention: inspect existing tables/columns, issue raw `ALTER TABLE` for missing columns, handle dialect-specific nullable changes, and return human-readable messages.
- Compatibility tests exist for permissions and feedback schema changes.
- `scripts/migrate_author.py` is a one-off async migration-script pattern.
- `requirements.txt` includes Alembic, but no Alembic config/version directory was found.
- `.trellis/spec/backend/database-guidelines.md` says compatibility checks and scripts are the current workflow, not Alembic migrations.

#### Seed data patterns

- `scripts/seed_data.py` seeds users, categories, tags, courses, chapters, sections, resources, and announcements.
- It skips import if any `User` exists.
- It does not create `ResourceProgress`, `LearningProgress`, or statistics rows.

#### Scheduler/background job search results

- No scheduler, cron, APScheduler, Celery, FastAPI `BackgroundTasks`, `asyncio.create_task`, or recurring job infrastructure was found.
- `app/main.py` startup compatibility checks are the only lifecycle work found.
- `requirements.txt` has no scheduler/background package.

### Related Specs

- `.trellis/spec/backend/database-guidelines.md` — SQLAlchemy async patterns, tests, and compatibility convention.
- `.trellis/spec/backend/quality-guidelines.md` — backend layering, pytest fixture expectations, and validation commands.

## Caveats / Not Found

- No Alembic configuration or migration versions directory was found, even though `alembic` is listed in `requirements.txt`.
- No scheduler, cron, APScheduler, Celery, FastAPI `BackgroundTasks`, or recurring background job infrastructure was found.
- Current seed data does not create learning progress/statistics rows.
- `LearningProgress` exists as a model, but current learning-record and progress services/tests found in this search are based on `ResourceProgress`.
