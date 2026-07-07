# Error Handling

> How errors are handled in this project.

---

## Overview

The backend uses custom application exceptions from `app/core/exceptions.py`, FastAPI exception handlers in `app/main.py`, and Pydantic validation in `app/schemas/`.

All normal API responses should keep the project response shape:

```json
{ "code": 200, "message": "操作成功", "data": {} }
```

Business errors should be raised as typed `AppException` subclasses where possible. Unexpected errors are handled by the global exception handler and logged.

---

## Error Types

Custom application exceptions live in `project_code/backend/app/core/exceptions.py`.

Current hierarchy:

```py
class AppException(Exception):
    def __init__(
        self,
        code: int = BusinessCode.BAD_REQUEST,
        message: str = "操作失败",
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(self.message)
```

Use existing subclasses for common cases:

| Exception | When to use |
|-----------|-------------|
| `UnauthorizedException` | Missing/invalid login or token |
| `ForbiddenException` | Logged-in user lacks permission |
| `NotFoundException` | Requested resource does not exist |
| `ValidationException` | Business-level validation failure |
| `ConflictException` | Duplicate/conflicting resource |
| `AuthenticationException` | Login credential failure |
| `AccountLockedException` | Locked account |

Example from `app/api/v1/feedbacks.py`:

```py
feedback = await feedback_service.get_by_id(db, feedback_id)
if not feedback:
    raise NotFoundException("反馈不存在")

can_view_all = await has_feedback_admin_permission(db, current_user.role)
if not can_view_all and feedback["user_id"] != current_user.id:
    raise ForbiddenException("无权查看该反馈")
```

---

## Business Status Codes

Business codes are defined in `app/schemas/common.py` as `BusinessCode` constants.

Examples:

```py
class BusinessCode:
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    VALIDATION_ERROR = 422
    INTERNAL_ERROR = 500
```

Use these codes through `AppException` subclasses or `ApiResponse` helpers instead of scattering magic numbers.

---

## Error Propagation Pattern

### Routes

Routes should validate route-level permissions and resource ownership, then delegate business work to services.

Correct pattern:

```py
@router.post("/{feedback_id}/process", response_model=ApiResponse[FeedbackResponse])
async def process_feedback(
    feedback_id: int,
    db: DBSession,
    current_user: CurrentUser,
    data: FeedbackProcess | None = None,
) -> ApiResponse[FeedbackResponse]:
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.feedback",
        "无权处理反馈",
    )
    feedback = await feedback_service.process(db, feedback_id, data, current_user.id)
    detail = await feedback_service.get_by_id(db, feedback.id)
    return ApiResponse.success(
        data=FeedbackResponse.model_validate(detail),
        message="处理成功",
    )
```

### Services

Services should raise business exceptions when the requested operation cannot proceed.

Example from `app/services/feedback_service.py`:

```py
feedback = await db.get(Feedback, feedback_id)
if not feedback:
    raise NotFoundException("反馈不存在")
```

Do not catch an `AppException` only to rethrow the same error. Let FastAPI's registered exception handler convert it.

---

## API Error Responses

`app/main.py` registers the `AppException` handler:

```py
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    http_exc = app_exception_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail,
    )
```

`app_exception_to_http_exception()` maps business codes to HTTP status codes and returns this structure:

```json
{
  "code": 404,
  "message": "资源不存在",
  "details": null
}
```

Note: success responses use `{ code, message, data }`; current `AppException` errors use `{ code, message, details }`. When changing error handling, keep frontend expectations in sync.

---

## Pydantic Validation

Use Pydantic schemas for request shape, field constraints, literals, aliases, and cross-field validation.

Example from `app/schemas/feedback.py`:

```py
class FeedbackCreate(BaseModel):
    feedback_type: Literal["system", "course"] = Field(
        default="system",
        validation_alias=AliasChoices("feedback_type", "type"),
        description="反馈类型：system/course",
    )
    course_id: int | None = Field(default=None, ge=1)
    content: str = Field(..., min_length=1, max_length=2000)

    @model_validator(mode="after")
    def _finalize(self):
        if self.feedback_type == "course" and self.course_id is None:
            raise ValueError("课程反馈必须提供 course_id")
        return self
```

Use schema validation for input contract rules; use services for database-dependent business validation.

---

## Global Exception Handling

Unexpected exceptions are caught in `app/main.py`:

```py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"未处理的异常: {exc.__class__.__name__}: {exc}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误" if not settings.debug else str(exc),
            "data": None,
        },
    )
```

Do not expose raw exception messages in production. The current handler only exposes `str(exc)` when `settings.debug` is enabled.

---

## Permission Errors

Use `permission_service.ensure_permission(...)` for permission-code checks.

Example:

```py
await permission_service.ensure_permission(
    db,
    current_user.role,
    "admin.feedback",
    "无权处理反馈",
)
```

Use `ForbiddenException` directly when the check is resource ownership or a local rule that is not just a permission-code lookup.

---

## Logging Errors

Only unexpected exceptions are logged by the global handler. Expected business errors such as not found, forbidden, and validation failures generally should not be logged as server errors.

If a service catches an external integration failure in the future, log the operational context and raise an appropriate `AppException` so the client still receives a stable response.

---

## Forbidden Patterns

- Do not return raw error dictionaries from routes when an exception should be raised.
- Do not raise bare `Exception` for business failures.
- Do not catch and suppress errors silently in backend services.
- Do not expose internal stack traces or raw database errors to clients.
- Do not duplicate exception classes inside feature modules.
- Do not mix HTTP status codes and business codes ad hoc; use `BusinessCode` and existing exceptions.
- Do not perform database-dependent validation in Pydantic schemas.

---

## Common Mistakes

- Returning `{ "success": false }` instead of raising a typed exception or using `ApiResponse.error` where appropriate.
- Adding route-level `try/except Exception` blocks that hide the global exception handler and logging behavior.
- Forgetting to check resource ownership after fetching an object.
- Treating permission-code checks and ownership checks as the same thing.
- Adding new Pydantic validators for rules that require database access.
- Changing error response shape without checking frontend Axios error handling in `UI/src/api/index.ts`.
