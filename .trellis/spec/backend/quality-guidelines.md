# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

Backend changes must preserve the FastAPI + SQLAlchemy + Pydantic layering, the `/api/v1` API prefix, Bearer Token authentication, and the response contract `{ code, message, data }` for normal API responses.

Follow the root `CLAUDE.md` directory routing rules first. Backend implementation belongs under `project_code/backend/`, while backend architecture/API docs belong under `project_code/docs/`.

---

## Required Patterns

Use this responsibility split:

| Layer | Responsibility |
|-------|----------------|
| `api/v1/*.py` | HTTP routes, dependencies, permission checks, response wrapping |
| `schemas/*.py` | Pydantic request/response contracts and field validation |
| `services/*.py` | business logic, database queries, cross-model operations |
| `models/*.py` | SQLAlchemy table definitions |
| `core/*.py` | shared dependencies, exceptions, security, logging, config |
| `tests/*.py` | module-level API/service behavior tests |

Normal successful responses should use `ApiResponse.success(...)` or return an `ApiResponse[...]` model. Paginated responses should use `PageData.create(...)`.

Keep these project-wide constants aligned with frontend expectations:

- API prefix: `/api/v1`
- roles: `student`, `teacher`, `admin`
- auth: Bearer Token
- response shape: `{ code, message, data }`

---

## Permission and Ownership Rules

Use permission services for permission-code checks:

```py
await permission_service.ensure_permission(
    db,
    current_user.role,
    "admin.feedback",
    "无权处理反馈",
)
```

Use explicit ownership checks for user-owned resources:

```py
can_view_all = await has_feedback_admin_permission(db, current_user.role)
if not can_view_all and feedback["user_id"] != current_user.id:
    raise ForbiddenException("无权查看该反馈")
```

Do not assume role name alone is enough when the project uses permission codes.

---

## Testing Requirements

Tests use pytest, pytest-asyncio, httpx `AsyncClient`, and in-memory SQLite.

For cross-layer API contracts, mocked frontend responses are not completion evidence. If a frontend/browser check used mocked payloads or injected session state, treat the task result as unknown until the real FastAPI route and response payload are checked. Record the mock as a limitation/problem, create a current-task follow-up subtask for real integration validation, then resolve the API/schema/mapper mismatch before returning to the original task.

Minimum real-contract checks for frontend-facing backend changes:

- confirm the route appears in `/openapi.json` under the expected `/api/v1/...` path
- call the real endpoint with the same auth and query/body shape the UI uses
- compare response field names to the frontend API mapper/type, especially legacy `id` vs UI-facing `*_id` fields
- only mark the task complete after the real endpoint and frontend mapper agree

Use existing fixtures from `tests/conftest.py`:

- `client`
- `db_session`
- `test_user`
- `test_teacher`
- `test_admin`
- `auth_headers`
- `teacher_headers`
- `admin_headers`
- `test_course`

For backend changes, run the relevant tests from `project_code/backend/`:

```bash
pytest tests/test_feedbacks.py -v
pytest tests/test_courses.py -v
pytest tests/test_learning.py -v
```

Run `pytest tests/ -v` for broad changes touching shared dependencies, auth, response contracts, database compatibility, or permissions.

---

## Documentation and Operations Log

If any backend file under `project_code/` changes, update `project_code/operations-log.md`.

The log entry should include:

- change time
- reason
- files touched
- core changes
- verification result, or a clear statement that verification was not run

If API contracts or architecture behavior changes, update the relevant docs under `project_code/docs/` when applicable.

---

## Code Review Checklist

Before considering backend work complete, check:

- route is mounted under `/api/v1` through `app/api/v1/router.py` when needed
- response shape matches `{ code, message, data }`
- request/response schema is typed and validated with Pydantic
- service owns business logic and database queries
- model changes are reflected in schemas/services/tests
- permission and ownership checks are both correct
- module-specific pytest has been run or skipped with a clear reason
- `project_code/operations-log.md` has been updated for backend file changes
- frontend API modules were checked for cross-layer contract changes

---

## Forbidden Patterns

- Do not put backend source code in the root workspace or `UI/`.
- Do not define feature APIs in `app/main.py`.
- Do not return unwrapped success payloads from normal API routes.
- Do not bypass `DBSession` / `CurrentUser` dependency aliases in normal routes.
- Do not create sync database sessions in async code.
- Do not use raw SQL with interpolated user input.
- Do not skip tests for changed routes/services/schemas.
- Do not change cross-layer response fields without checking frontend API modules.
- Do not modify backend files without updating `project_code/operations-log.md`.

---

## Common Mistakes

- Updating `app/models/*.py` but forgetting schemas, services, tests, and compatibility checks.
- Adding a route module but forgetting to include it in `app/api/v1/router.py`.
- Checking only `role == "admin"` when permissions are actually controlled through permission codes.
- Returning backend legacy fields without normalizing to frontend-used fields.
- Catching exceptions in routes and returning inconsistent error shapes.
- Running only frontend validation for a backend contract change.
