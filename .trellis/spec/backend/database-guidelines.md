# Database Guidelines

> ORM patterns, queries, and database conventions for the backend.

---

## Overview

The backend uses SQLAlchemy 2.x async ORM. Database access should be performed through `AsyncSession` injected by dependencies or tests. Models live in `project_code/backend/app/models/`, business queries live in `project_code/backend/app/services/`, and Pydantic schemas live in `project_code/backend/app/schemas/`.

The project currently does not use a migration framework as the primary workflow. Compatibility adjustments are handled by startup schema checks such as `app/core/db_schema.py`, and database initialization scripts live under `project_code/backend/scripts/`.

---

## Model Base and Mixins

All ORM models inherit from shared base classes in `app/models/base.py`.

Use `BaseModel` for most tables:

```py
class BaseModel(Base, IDMixin, TimestampMixin):
    __abstract__ = True
    __mapper_args__ = {"eager_defaults": True}
```

Shared mixins:

| Mixin | Purpose |
|-------|---------|
| `IDMixin` | integer primary key `id` |
| `TimestampMixin` | `created_at` and `updated_at` with server defaults |
| `SoftDeleteMixin` | optional `is_deleted` and `deleted_at` |

`__mapper_args__ = {"eager_defaults": True}` is used to avoid async ORM lazy-loading problems for server-generated default values.

---

## Model Field Style

Use SQLAlchemy 2 typed ORM declarations with `Mapped[...]` and `mapped_column(...)`.

Example from `app/models/feedback.py`:

```py
class Feedback(BaseModel):
    __tablename__ = "feedbacks"

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="用户ID",
    )
    type: Mapped[str] = mapped_column(
        String(20),
        default="system",
        nullable=False,
        comment="反馈类型",
    )
    course_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="关联课程ID",
    )
```

Model field conventions:

- use explicit SQL types for strings, text, date/time, integers, floats, and booleans
- set `nullable=False` for required fields
- use Python union syntax for nullable values, e.g. `Mapped[int | None]`
- add `index=True` to fields commonly used in filters or joins
- add Chinese `comment` text for database readability
- keep table names plural where existing modules do so, e.g. `feedbacks`, `courses`, `course_materials`

---

## Where Queries Belong

Place SQLAlchemy query logic in service classes, not route modules or schemas.

Example from `app/services/feedback_service.py`:

```py
base_query = (
    select(
        Feedback,
        User.username.label("username"),
        User.email.label("user_email"),
        User.phone.label("user_phone"),
        Course.title.label("course_title"),
    )
    .join(User, User.id == Feedback.user_id)
    .outerjoin(Course, Course.id == Feedback.course_id)
)
```

Routes should call services:

```py
feedbacks, total = await feedback_service.get_list(
    db,
    user_id=None if can_view_all else current_user.id,
    feedback_type=feedback_type,
    status=status,
    page=page,
    page_size=page_size,
)
```

---

## Async Session Pattern

Use `AsyncSession` and await database operations:

```py
db.add(feedback)
await db.flush()
return feedback
```

Common operations:

```py
result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
feedback = result.scalar_one_or_none()

feedback = await db.get(Feedback, feedback_id)

await db.flush()
await db.refresh(model)
```

Do not use synchronous SQLAlchemy sessions in app code.

---

## Filtering and Pagination

Build filters as a list of conditions and apply them when present.

Example:

```py
conditions = []

if user_id:
    conditions.append(Feedback.user_id == user_id)

if feedback_type == "course":
    conditions.append(or_(Feedback.course_id.is_not(None), Feedback.type == "course"))
elif feedback_type == "system":
    conditions.append(and_(Feedback.course_id.is_(None), Feedback.type != "course"))

if conditions:
    base_query = base_query.where(*conditions)
```

Use subquery counts for paginated joined queries:

```py
count_query = select(func.count()).select_from(base_query.subquery())
total_result = await db.execute(count_query)
total = total_result.scalar() or 0

query = base_query.order_by(Feedback.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
```

Return `(items, total)` from service list methods, and let routes wrap the result in `PageData.create(...)`.

---

## Serialization

Prefer Pydantic schemas for simple ORM-to-response conversion. When a response combines multiple joined models or compatibility fields, keep serialization in the service.

Use service-level serialization when the API needs joined fields, normalized status/type fields, compatibility aliases, or parsed JSON stored in text columns.

---

## JSON-Like Fields

Some existing fields store JSON arrays as text, such as `Feedback.images`.

Current pattern:

```py
images=json.dumps(data.images) if data.images else None
images = json.loads(feedback.images) if feedback.images else []
```

If adding new JSON-like fields, prefer a real JSON column if the target database supports it consistently. If using text for compatibility, centralize serialization/deserialization in the service.

---

## Schema Compatibility

Database compatibility checks live in `app/core/db_schema.py` and run during application startup from `app/main.py` through `ensure_database_compatibility(...)`.

There are tests for compatibility behavior, for example `tests/test_feedbacks.py::test_ensure_database_compatibility_adds_feedback_course_id` verifies old `feedbacks` tables are updated with `course_id`.

When changing table shape:

1. Update the ORM model.
2. Update schemas/services/routes that expose the field.
3. Update seed/init scripts if needed.
4. Add or update compatibility logic if existing databases may lack the field.
5. Add or update tests proving both new behavior and compatibility behavior.

---

## Tests

Tests use an in-memory SQLite database configured in `tests/conftest.py`:

```py
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

The test engine creates all tables from `Base.metadata`, and each test receives an isolated `AsyncSession` fixture that rolls back after completion.

When changing database logic, run the module-specific test first:

```bash
pytest tests/test_feedbacks.py -v
pytest tests/test_courses.py -v
```

---

## Forbidden Patterns

- Do not put database query logic in Pydantic schemas.
- Do not create synchronous SQLAlchemy sessions in app code.
- Do not call blocking database operations from async routes/services.
- Do not build raw SQL strings from user input.
- Do not add model fields without updating schemas/services/tests that expose or use them.
- Do not rely on async lazy loading after `flush`; use eager defaults, explicit joins, or explicit refreshes.
- Do not scatter JSON text parsing across routes/pages; keep it in services.
- Do not skip compatibility checks/tests when changing tables that may already exist in local/prod databases.

---

## Common Mistakes

- Adding a model column but forgetting `app/core/db_schema.py` compatibility behavior for existing SQLite databases.
- Returning ORM models from joined service queries when the route expects flattened frontend fields.
- Forgetting `await db.flush()` before using a newly-created model id.
- Counting paginated joined queries incorrectly by counting rows after `limit`/`offset`.
- Filtering course/system feedback only by `type` and forgetting that `course_id` also defines course feedback in current compatibility logic.
