# Logging Guidelines

> Structured logging, log levels, and logging conventions for the backend.

---

## Overview

Backend logging is configured centrally in `project_code/backend/app/core/logging.py` and initialized in `app/main.py`. Request logging is handled by `RequestLoggingMiddleware` in `app/middleware/logging_middleware.py`.

Use Python's standard `logging` module through the project helper:

```py
from app.core.logging import get_logger

logger = get_logger(__name__)
```

---

## Logging Setup

`app/main.py` initializes logging at import/startup time:

```py
setup_logging(
    level=settings.log_level,
    log_dir=settings.log_dir,
    log_to_console=settings.log_to_console,
    log_to_file=settings.log_to_file,
    log_file_prefix=settings.log_file_prefix,
    backup_count=settings.log_backup_count,
)

logger = get_logger(__name__)
```

`setup_logging(...)` configures root logger level, colored console logs, daily rotating main log file, daily rotating error log file, and reduced noise from common third-party libraries.

---

## Log Levels

Use `INFO` for lifecycle and high-level operational events:

```py
logger.info(f"🚀 {settings.app_name} v{settings.app_version} 启动中...")
logger.info(f"📝 环境: {settings.environment}")
logger.info(f"📁 日志目录: {settings.log_dir}")
```

Use `WARNING` for recoverable or operator-actionable situations:

```py
if "请手动检查" in message:
    logger.warning(message)
else:
    logger.info(message)
```

Use `ERROR` for unexpected exceptions or failed operations that need investigation:

```py
logger.error(
    f"未处理的异常: {exc.__class__.__name__}: {exc}",
    exc_info=True,
)
```

Use `DEBUG` only for development diagnostics and low-level details. Current request middleware only logs JSON content type at debug level, not the body.

---

## Structured Logging

Console format:

```text
%(asctime)s | %(levelname)-8s | %(name)s | %(message)s
```

File format:

```text
%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s
```

Request logs include request id, method/path, client, auth presence, status code, duration, database label, SQL count, and SQL duration.

---

## Request Logging

`RequestLoggingMiddleware` logs every HTTP request and adds these response headers:

- `X-Request-ID`
- `X-Response-Time`

Completion level depends on status code:

```py
log_level = logging.INFO if response.status_code < 400 else logging.WARNING
if response.status_code >= 500:
    log_level = logging.ERROR
```

The middleware logs authentication presence only:

```py
authorization = request.headers.get("authorization", "")
if authorization.startswith("Bearer "):
    user_id = "authenticated"
```

Do not change this to log token values.

---

## What to Log

- application startup/shutdown
- environment, docs URL, log directory, upload directory
- schema compatibility messages
- HTTP request start/completion/exception through middleware
- unexpected exceptions with `exc_info=True`
- external integration failures with enough context to diagnose safely

---

## What NOT to Log

Do not log secrets or sensitive payloads:

- passwords
- access tokens
- refresh tokens
- full `Authorization` header
- verification codes/captcha text in production logs
- raw uploaded file contents
- full request bodies by default

---

## SQL Logging

Request logs include SQL query count and duration through request context helpers:

```py
db_stats = get_request_db_stats()
f"数据库: {db_stats.query_count}条SQL/{db_stats.total_duration_ms:.2f}ms"
```

SQL logging integration is installed in tests through `install_sql_logging(engine)` in `tests/conftest.py`.

Do not enable verbose SQL statement logging globally unless it is needed for a focused debug session.

---

## Forbidden Patterns

- Do not log access tokens, refresh tokens, passwords, or verification codes.
- Do not log full request bodies by default.
- Do not use `print()` for backend diagnostics in app code.
- Do not configure logging independently inside feature modules.
- Do not lower third-party library log levels globally without checking noise and sensitive data impact.
- Do not swallow exceptions after logging them unless the failure is explicitly recoverable.
- Do not log expected 4xx business errors as `ERROR` unless they indicate a server-side issue.

---

## Common Mistakes

- Adding route-local try/except logging that duplicates global exception logs.
- Logging the `Authorization` header while debugging authentication.
- Logging uploaded file contents or large request bodies.
- Creating a new logger format that makes request id correlation harder.
- Forgetting to include `exc_info=True` when logging unexpected exceptions.
