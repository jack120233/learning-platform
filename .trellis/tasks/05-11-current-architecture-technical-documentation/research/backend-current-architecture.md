# Research: Backend Current Architecture

- **Query**: Research the current backend architecture and functionality for this FastAPI project. Goal: support a new technical documentation task at `.trellis/tasks/05-11-current-architecture-technical-documentation`. Inspect current code under `project_code/backend/` and relevant docs under `project_code/docs`, especially architecture and API docs. Persist findings to `.trellis/tasks/05-11-current-architecture-technical-documentation/research/backend-current-architecture.md`. Include: app entry/router structure/config/database/session patterns, service/model/schema layering, auth/roles/permissions, major API modules and core business functions, test/dev commands, notable differences or stale spots in existing docs if obvious. Do not modify code outside the research file.
- **Scope**: internal
- **Date**: 2026-05-11

## Findings

### Files Found

| File Path | Description |
|---|---|
| `project_code/backend/app/main.py` | FastAPI app entry; logging setup, lifespan startup, CORS, request logging middleware, exception handlers, v1 router mount, static upload mount, root endpoint. |
| `project_code/backend/app/config.py` | `pydantic-settings` configuration; app/API/server/database/JWT/CORS/log/upload settings and validators. |
| `project_code/backend/app/api/v1/router.py` | v1 route aggregator mounted under `settings.api_v1_prefix`; includes health, auth, system, permissions, users, courses, uploads, content, learning, feedbacks, messages. |
| `project_code/backend/app/core/dependencies.py` | Async SQLAlchemy engine/session factory, `get_db()` transaction dependency, bearer-token current-user dependencies. |
| `project_code/backend/app/core/security.py` | Password hashing/verification and JWT access/refresh token helpers. |
| `project_code/backend/app/core/exceptions.py` | `AppException` hierarchy and business-code to HTTP-status mapping. |
| `project_code/backend/app/core/db_schema.py` | Startup/init compatibility checks for historical schema changes and permission-role cleanup/fill. |
| `project_code/backend/app/schemas/common.py` | Shared `ApiResponse[T]`, `PageData[T]`, `ErrorResponse`, and `BusinessCode` constants. |
| `project_code/backend/app/models/base.py` | SQLAlchemy `DeclarativeBase` plus `IDMixin`, `TimestampMixin`, `SoftDeleteMixin`, `BaseModel`. |
| `project_code/backend/app/models/*.py` | ORM models for users, auth artifacts, system data, permissions, courses/content, learning, feedback, messages. |
| `project_code/backend/app/schemas/*.py` | Pydantic request/response models organized by feature/domain. |
| `project_code/backend/app/services/*.py` | Business logic/query services organized by feature/domain. |
| `project_code/backend/app/api/v1/*.py` | FastAPI route modules. Current decorator count found by scan: 96 endpoints across route files plus health. |
| `project_code/backend/tests/conftest.py` | pytest-asyncio/httpx ASGI test setup; in-memory SQLite, dependency override for `get_db`, user/token fixtures. |
| `project_code/backend/tests/test_*.py` | Module tests for auth, courses, content, learning, feedbacks, health, logging, ORM safety/defaults, permissions, system, uploads, users. |
| `project_code/backend/scripts/init_db.py` | Creates all tables through `Base.metadata.create_all` and runs compatibility checks. |
| `project_code/backend/scripts/seed_data.py` | Seeds sample users, categories, tags, courses, course content, announcements. |
| `project_code/backend/requirements.txt` | Backend dependency list. |
| `project_code/docs/architecture.md` | Existing architecture document; broadly describes layered FastAPI app but appears older than current route surface. |
| `project_code/docs/api-endpoint-inventory.md` | Existing API inventory; more current than architecture docs but contains count inconsistencies/stale endpoint totals. |
| `project_code/docs/test-plan.md` | Existing pytest/httpx test plan; contains planned test layout and commands, but endpoint counts and some file names are stale against current tests. |

## Current Architecture Summary

- Backend entry is `project_code/backend/app/main.py`. It sets up logging, creates upload directories, runs startup compatibility checks, configures CORS/request logging/exception handlers, mounts `/api/v1`, and serves uploaded files from the configured upload prefix.
- Configuration lives in `project_code/backend/app/config.py` via `pydantic-settings`; key defaults include `/api/v1`, SQLite-compatible defaults, JWT expiry, CORS, logging, and upload limits.
- Database access is centralized in `project_code/backend/app/core/dependencies.py`; `get_db()` yields an `AsyncSession`, commits on success, rolls back on exception, and closes the session.
- Main layering is `api/v1/*.py -> schemas/*.py -> services/*.py -> models/*.py -> database`.
- Shared response contracts are `ApiResponse[T]` and `PageData[T]` in `project_code/backend/app/schemas/common.py`.
- Auth uses bearer JWT access/refresh tokens; current-user dependencies decode tokens and load `User` rows.
- Permissions use `Permission` / `RolePermission` plus `PermissionService`; current routes mix login-only checks, owner/service checks, explicit permission checks, and admin role checks.
- Current route modules: health, auth, categories, tags, announcements, permissions, users, courses, uploads, content, learning, feedbacks, messages.

## Major Modules

- **Auth**: register, login, logout, refresh, captcha, email code, reset password.
- **Users/profile/admin workflows**: profile read/update, password change, learning records, teacher options, feedback history, admin user list/status/delete, teacher audits, admin applications.
- **System data**: categories, tags, announcements.
- **Permissions/RBAC**: permission tree, current user permission codes, role permission read/update.
- **Courses**: public list/search/homepage/detail, teacher/admin my/manage courses, create/update, publish/archive/delete, batch actions, materials.
- **Content**: chapters, sections, resources, sorting, chapter-level resources, legacy delete compatibility routes.
- **Uploads**: unified file upload, avatar upload, feedback-image upload, chunk upload init/chunk/complete.
- **Learning**: start course, save/get progress, continue learning, resource play and preview URLs.
- **Feedback**: create/list/detail/process/batch-process with role/permission-aware visibility.
- **Messages**: list/detail/read/mark-all/delete/unread-count/send.

## Validation Commands

Run from `project_code/backend/`:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
pytest tests/test_auth.py -v
pytest tests/test_auth.py::test_register -v
pytest tests/ --cov=app --cov-report=html
python scripts/init_db.py
python scripts/seed_data.py
```

## Stale/Difference Notes

- `project_code/docs/architecture.md` broadly matches the layered shape but has older module/API counts and omits current first-class `permissions.py` and `uploads.py` route modules in parts of the module inventory.
- `project_code/docs/api-endpoint-inventory.md` is the strongest endpoint source but has inconsistent endpoint totals and should be updated before quoting exact totals.
- `project_code/docs/test-plan.md` mentions 68 endpoints and planned test files that differ from the current test layout; current tests include `test_permissions.py`, `test_uploads.py`, ORM/logging tests, and grouped system/message tests.
- Seed usernames/passwords align with root guidance, but seed email domains in `seed_data.py` differ from some docs (`@test.com` vs `@example.com`). Use usernames/passwords as the stable login reference.

## Caveats

- Endpoint counts are based on a source scan and include compatibility/legacy routes; product docs may group them differently.
- This research did not run tests or the application.
