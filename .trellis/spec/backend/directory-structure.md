# Directory Structure

> How backend code is organized in this project.

---

## Overview

The backend project lives under `project_code/backend/`. The workspace root is not a backend package, so backend commands and file lookups must be performed inside `project_code/backend/` unless the task explicitly concerns root-level collaboration files.

The backend is a FastAPI + SQLAlchemy + Pydantic application. Business modules usually follow this layered pattern:

```text
API route → schema → service → model → database
```

Cross-cutting concerns such as configuration, security, dependencies, logging, and exceptions live under `app/core/` and `app/middleware/`.

---

## Project Root

```text
project_code/
├── backend/
│   ├── app/                 # FastAPI application package
│   ├── tests/               # pytest test suite
│   ├── scripts/             # Database initialization and seed scripts
│   └── requirements.txt     # Backend dependencies
├── docs/                    # Backend architecture, API inventory, test docs
├── CLAUDE.md                # Backend-specific AI development rules
└── operations-log.md        # Required log for actual backend file changes
```

Run backend commands from `project_code/backend/`:

```bash
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
pytest tests/test_auth.py -v
python scripts/init_db.py
python scripts/seed_data.py
```

---

## Application Layout

```text
project_code/backend/app/
├── api/v1/              # FastAPI route modules and v1 router aggregation
├── core/                # Dependencies, security, exceptions, logging, constants
├── middleware/          # Request middleware
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic and database queries
├── config.py            # pydantic-settings configuration
└── main.py              # FastAPI app, middleware, exception handlers, router mount
```

---

## Layer Responsibilities

### `app/main.py`

`app/main.py` creates and configures the FastAPI application. It owns:

- logging setup via `setup_logging(...)`
- upload directory initialization
- lifespan startup/shutdown behavior
- CORS middleware registration
- request logging middleware registration
- `AppException` and global exception handlers
- mounting the v1 API router under `settings.api_v1_prefix`
- static upload file serving

Example:

```py
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
```

Do not define business endpoints directly in `main.py` except simple root/health-style entry points.

### `app/api/v1/`

Route modules define HTTP endpoints, request parameters, dependency injection, permission checks, and response wrapping. They should delegate business logic to services.

Examples:

- `app/api/v1/auth.py` for auth endpoints.
- `app/api/v1/courses.py` for course endpoints.
- `app/api/v1/feedbacks.py` for feedback endpoints.
- `app/api/v1/router.py` aggregates v1 route modules.

Typical route pattern:

```py
@router.post("", response_model=ApiResponse[FeedbackResponse])
async def create_feedback(
    data: FeedbackCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[FeedbackResponse]:
    feedback = await feedback_service.create(db, current_user.id, data)
    detail = await feedback_service.get_by_id(db, feedback.id)
    return ApiResponse.success(
        data=FeedbackResponse.model_validate(detail),
        message="提交成功",
    )
```

### `app/services/`

Services contain business rules, SQLAlchemy query composition, persistence operations, serialization that is too business-specific for schemas, and cross-model coordination.

Examples:

- `app/services/feedback_service.py` creates feedback, lists feedback with joins, normalizes feedback status/type, and processes replies.
- `app/services/course_service.py` owns course query/write logic.
- `app/services/learning_service.py` owns learning-progress logic.

Services should not import frontend concepts or return raw FastAPI responses.

### `app/schemas/`

Schemas define Pydantic request and response models. Shared response wrappers live in `app/schemas/common.py`.

Examples:

- `ApiResponse[T]` wraps all API responses as `{ code, message, data }`.
- `PageData[T]` wraps paginated results.
- Feature schemas such as `FeedbackCreate`, `FeedbackResponse`, `CourseResponse`, and auth schemas live in feature-specific files.

### `app/models/`

Models define SQLAlchemy ORM tables. Shared model base/mixins live in `app/models/base.py`.

Examples:

```py
class BaseModel(Base, IDMixin, TimestampMixin):
    __abstract__ = True
    __mapper_args__ = {"eager_defaults": True}
```

Use existing mixins such as `IDMixin`, `TimestampMixin`, and `SoftDeleteMixin` when a model needs those standard fields.

### `app/core/`

Use `app/core/` for shared backend infrastructure:

- `dependencies.py` for database/session/current-user dependencies.
- `exceptions.py` for `AppException` and typed application exceptions.
- `security.py` for password/JWT/security helpers.
- `logging.py`, `sql_logging.py`, and `request_context.py` for logging infrastructure.
- constants such as `resource_types.py`.

### `tests/`

Tests are organized by backend module:

```text
tests/
├── conftest.py
├── test_auth.py
├── test_courses.py
├── test_content.py
├── test_feedbacks.py
├── test_learning.py
├── test_system.py
├── test_uploads.py
└── test_users.py
```

Use the module-specific test file when changing a route/service/schema in that module.

---

## Module Organization

When adding or changing a backend feature, update the existing vertical slice instead of creating an isolated parallel structure:

| Responsibility | Location |
|----------------|----------|
| HTTP endpoint | `app/api/v1/<module>.py` |
| Router registration | `app/api/v1/router.py` |
| Request/response schema | `app/schemas/<module>.py` |
| Business logic/query | `app/services/<module>_service.py` |
| Database table | `app/models/<module>.py` |
| Tests | `tests/test_<module>.py` |
| Scripts/data setup | `scripts/` |
| Architecture/API docs | `project_code/docs/` |

For example, feedback-related behavior is split across:

- `app/api/v1/feedbacks.py`
- `app/schemas/feedback.py`
- `app/services/feedback_service.py`
- `app/models/feedback.py`
- `tests/test_feedbacks.py`

---

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Route modules | plural or domain noun | `courses.py`, `feedbacks.py`, `learning.py` |
| Service files | `<domain>_service.py` | `feedback_service.py` |
| Service instances | `<domain>_service` | `feedback_service` |
| Schema files | domain noun | `feedback.py`, `course.py` |
| Model classes | PascalCase singular | `Feedback`, `Course`, `User` |
| Schema classes | PascalCase with action/role suffix | `FeedbackCreate`, `FeedbackResponse` |
| Tests | `test_<module>.py` | `test_feedbacks.py` |
| API prefix | `/api/v1` | configured by `settings.api_v1_prefix` |

---

## Required Checks Before Adding Files

Before creating a new backend file:

1. Check whether the task belongs to `project_code/backend/` using the root `CLAUDE.md` routing rules.
2. Search for an existing module with the same business responsibility.
3. Add to the existing route/schema/service/model/test slice when possible.
4. If adding a route module, register it in `app/api/v1/router.py`.
5. Keep API responses wrapped in `ApiResponse` and paginated results in `PageData`.
6. If an actual backend file is changed, update `project_code/operations-log.md`.

---

## Forbidden Patterns

- Do not put backend source code in the workspace root.
- Do not define feature endpoints directly in `app/main.py`.
- Do not place SQLAlchemy query/business logic in schemas.
- Do not return raw dictionaries from routes when an `ApiResponse[...]` model applies.
- Do not create a new route module without registering it in `app/api/v1/router.py`.
- Do not bypass `app/core/dependencies.py` for database/current-user dependencies in normal routes.
- Do not duplicate shared exception, response, logging, or security helpers inside feature modules.
- Do not mix frontend field naming assumptions into models; adapt API contracts through schemas/services.

---

## Good Examples

- `app/api/v1/feedbacks.py` keeps HTTP concerns in the route and delegates creation/listing/processing to `feedback_service`.
- `app/services/feedback_service.py` owns feedback query joins, filtering, status normalization, and serialization for frontend-facing data.
- `app/schemas/common.py` defines the shared `ApiResponse[T]` and `PageData[T]` response contracts.
- `app/models/base.py` centralizes common ORM base behavior and timestamp/id mixins.
- `app/main.py` centralizes app setup, middleware, exception handlers, and router mounting.
