# Research: Windows installer packaging options

- **Query**: Package a Vue + FastAPI + MySQL + Redis project as a Windows end-user installer with no command-line usage.
- **Scope**: mixed
- **Date**: 2026-05-13

## Findings

### Files Found

| File Path | Description |
|---|---|
| `UI/package.json` | Frontend build entrypoint; production bundle is generated with `npm run build`. |
| `UI/vite.config.ts` | Dev proxy and Windows-specific Vite cache setting; confirms frontend is a standard browser app. |
| `project_code/backend/requirements.txt` | Backend dependency list includes FastAPI, Uvicorn, SQLAlchemy async, MySQL drivers, and Redis. |
| `project_code/backend/app/config.py` | Environment-driven runtime config for database, Redis, JWT, upload dirs, and API prefix. |
| `project_code/backend/app/main.py` | FastAPI app bootstrap, lifecycle startup, database compatibility check, router mount, and static upload serving. |
| `project_code/backend/app/core/dependencies.py` | Async engine/session setup and Bearer-token auth dependencies. |
| `project_code/backend/app/core/db_schema.py` | Startup compatibility fixer for existing databases; used during app boot and DB init. |
| `project_code/backend/scripts/init_db.py` | Database table creation + compatibility checks for first-time setup. |
| `project_code/backend/scripts/seed_data.py` | Seed script for users, categories, tags, courses, content, and announcements. |
| `project_code/backend/.env.example` | Deployment example showing MySQL + Redis + JWT environment variables. |
| `project_code/backend/run.bat` | Developer-only Windows launcher for the backend. |
| `start-e2e-local.cmd` | Local developer orchestration script that starts init/seed/backend/frontend. |
| `start-backend-mysql.cmd` | Local developer script that starts the backend against MySQL. |
| `project_code/docs/architecture.md` | Backend architecture and deployment notes; documents MySQL/Redis and startup commands. |
| `.trellis/spec/backend/directory-structure.md` | Backend structure guide confirming startup and script locations. |
| `.trellis/spec/frontend/directory-structure.md` | Frontend structure guide confirming build and routing locations. |

### Code Patterns

#### 1) The repo is already split into a browser frontend and an API backend
- Frontend build is a standard static Vite bundle: `UI/package.json:9-10`.
- Dev-time frontend proxy goes to the backend API: `UI/vite.config.ts:35-43`.
- Backend exposes a FastAPI app under `/api/v1`: `project_code/backend/app/config.py:37-38`, `project_code/backend/app/main.py:99-105`.

This means a Windows installer can package the frontend as files and launch the backend separately; the frontend does not require Node at runtime.

#### 2) The backend expects external runtime configuration, not hard-coded local paths
- Database URL, Redis URL, JWT secret, upload dir, and CORS all come from settings: `project_code/backend/app/config.py:16-160`.
- `.env.example` explicitly shows MySQL and Redis values: `project_code/backend/.env.example:13-25`.
- The backend engine is created from `settings.async_database_url`: `project_code/backend/app/core/dependencies.py:24-38`.

This is installer-friendly because setup can write an `.env` file or set environment variables, but it also means the installer must provision the database/cache side correctly.

#### 3) First-run database setup is already scripted
- `init_db.py` creates tables and runs compatibility checks: `project_code/backend/scripts/init_db.py:23-62`.
- `seed_data.py` inserts users, categories, tags, courses, content, and announcements: `project_code/backend/scripts/seed_data.py:34-317`.
- The app startup also runs compatibility checks and creates the upload directory: `project_code/backend/app/main.py:35-56`.

This is the clearest fit for installer automation: the installer or first launch can call these scripts non-interactively.

#### 4) Windows launch scripts exist, but they are developer-style orchestration, not end-user packaging
- `run.bat` directly starts Uvicorn on port 8000: `project_code/backend/run.bat:40-51`.
- `start-e2e-local.cmd` starts init/seed, then backend and frontend dev servers: `start-e2e-local.cmd:21-36`.
- `start-backend-mysql.cmd` starts only the backend service against MySQL: `start-backend-mysql.cmd:14-18`.

These scripts show the current startup order, but they still assume a developer environment and command-line visibility.

#### 5) The backend is already aware of data-shape drift in deployed databases
- `ensure_database_compatibility()` patches columns and role-permission data during startup: `project_code/backend/app/core/db_schema.py:14-183`.
- `project_code/backend/app/main.py:50-57` and `project_code/backend/scripts/init_db.py:37-40` both call it.

That makes installer-first-launch workflows more realistic because schema drift is already handled in code.

### Packaging Pattern Comparison

| Pattern | What the user installs | Fit for this repo | Main advantages | Main risks / limits |
|---|---|---|---|---|
| Native Windows installer bundling portable services | One `.exe` or MSI/NSIS/Inno Setup installer that deploys frontend assets, backend runtime, config, DB initialization, and local services | Strongest match to “double-click to install” if the installer can also provision MySQL/Redis or compatible local services | Best end-user experience; can auto-run `init_db.py` / `seed_data.py`; can create desktop/start-menu shortcuts; works with current env-driven backend | Hardest to make reliable because MySQL + Redis must be installed, configured, and started on Windows; service permissions and upgrades are tricky; backend/runtime packaging must be maintained |
| Docker Desktop based deployment | Docker Desktop + Compose stack with frontend/backend/MySQL/Redis containers | Technically compatible with the repo because the app is env-driven and service boundaries are clear | Very repeatable environment; easy to pin versions; Compose fits multi-service stack well | Not a true “no command line” experience for beginners; Docker Desktop is heavy, needs virtualization, and adds another product users must understand |
| Electron/Tauri desktop wrapper with backend service | A desktop shell app plus a local backend executable/service | Partial fit: frontend is browser-friendly, but MySQL/Redis remain external dependencies | Good desktop feel; can hide browser navigation; can auto-launch backend on app start | Does not solve MySQL/Redis by itself; adds another packaging layer; sidecar/service lifecycle is complex; updates become harder |
| Enterprise server deployment | Install on a server/VM; Windows users open the web app in a browser | Very strong architectural fit for the current Vue + FastAPI web app | Lowest complexity for end users; centralizes database/cache on the server; matches current web architecture closely | Not a local end-user installer; needs server/admin operations; not suited to offline single-PC use |

### Pattern Notes Mapped to This Repo

#### Native installer with bundled local services
- The frontend can be packaged as static build output using `npm run build` (`UI/package.json:9-10`).
- The backend can be launched with Uvicorn and configured via `.env` / environment variables (`project_code/backend/app/config.py:16-160`).
- `init_db.py` and `seed_data.py` already provide the first-run initialization path (`project_code/backend/scripts/init_db.py:23-62`, `project_code/backend/scripts/seed_data.py:269-317`).

This pattern would let an installer write config, create directories, start services, and open the browser without user shell interaction.

#### Docker Desktop based deployment
- The repo already separates concerns cleanly enough for Compose: frontend build, FastAPI backend, MySQL, Redis.
- The main mismatch is user experience: the app is web-based, but the user must first install and understand Docker Desktop.
- The Vite proxy in development (`UI/vite.config.ts:35-43`) is a dev-only concern; a containerized release would need explicit runtime env wiring.

#### Electron/Tauri wrapper + backend service
- The frontend is suitable for a wrapper because it is already a standard SPA.
- The backend can be packaged as a local process because it is already launched as a single Uvicorn app (`project_code/backend/app/main.py:65-105`).
- However, the current repo still depends on MySQL and Redis (`project_code/backend/requirements.txt:4-26`), so the wrapper alone does not eliminate infra setup.

#### Enterprise server deployment
- The repository is already aligned with server deployment: browser frontend, `/api/v1` backend, external DB/cache, and seed/init scripts.
- The backend docs explicitly describe production Uvicorn startup and environment variables (`project_code/docs/architecture.md:418-456`).
- This is the least disruptive operational model, but it is no longer an end-user desktop installer.

### Recommended MVP Route

**Recommended MVP**: native Windows installer for a single-machine local installation, with the installer doing all setup silently for the user.

Why this route fits the repo best:
- The frontend is already a buildable static asset bundle.
- The backend already has explicit init/seed scripts.
- Runtime configuration is already environment-driven.
- The startup path already includes compatibility checks and upload directory creation.

Practical MVP shape for this repo:
1. Installer copies frontend build output and backend runtime files.
2. Installer writes `.env` or service config for `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `UPLOAD_DIR`, and API prefix.
3. Installer starts or registers the database/cache layer.
4. Installer runs `python scripts/init_db.py` and `python scripts/seed_data.py` once.
5. Installer registers a Windows shortcut or service entry that starts the backend and opens the browser.

### Risks / Caveats

- **MySQL on Windows** is the biggest operational dependency for a beginner-friendly installer.
- **Redis on Windows** is also a risk; this environment often needs containerized, packaged, or server-hosted handling rather than a simple “click install” story.
- **Packaging Python runtime** for FastAPI/Uvicorn is non-trivial; the installer needs a stable executable/runtime strategy.
- **Upgrades and uninstall** need a plan for preserving user data and avoiding broken DB/cache state.
- **Developer scripts are not installer scripts**; `run.bat`, `start-e2e-local.cmd`, and `start-backend-mysql.cmd` are useful references, but they are not sufficient for end users.

### External References

- [Inno Setup Help](https://jrsoftware.org/ishelp/) — Windows installer authoring option for `.exe` installers.
- [NSIS Users Manual](https://nsis.sourceforge.io/Docs/) — Another common Windows installer system.
- [PyInstaller Manual](https://pyinstaller.org/en/stable/) — Packaging Python apps into Windows executables.
- [Deployment - FastAPI](https://fastapi.tiangolo.com/deployment/) — Backend deployment reference.
- [Docker Desktop on Windows](https://docs.docker.com/desktop/setup/install/windows-install/) — Required if choosing the Docker Desktop pattern.
- [Docker Compose](https://docs.docker.com/compose/) — Multi-service orchestration reference for backend + DB + cache.
- [electron-builder](https://www.electron.build/) — Desktop app packaging reference for Electron-based wrappers.
- [Distribute | Tauri](https://v2.tauri.app/distribute/) — Desktop packaging reference for Tauri-based wrappers.
- [Install Redis on Windows](https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-windows/) — Relevant because Redis-on-Windows support is limited/archived.
- [Services (Services) - Win32 apps](https://learn.microsoft.com/en-us/windows/win32/services/services) — Windows service model reference.
- [Windows Installer - Win32 apps](https://learn.microsoft.com/en-us/windows/win32/msi/windows-installer-portal) — MSI packaging reference.

### Related Specs

- `.trellis/spec/backend/directory-structure.md` — Confirms backend startup, script, and service layering.
- `.trellis/spec/frontend/directory-structure.md` — Confirms frontend build, API proxy, and route-page structure.

## Caveats / Not Found

- No existing installer, Docker Compose file, Electron app, Tauri app, or packaging pipeline was found in this repo snapshot.
- MySQL official documentation pages were not reliably fetchable from this environment, so MySQL-specific packaging details should be verified separately before implementation.
- The current codebase contains development launch scripts, not a user-facing installer workflow.
