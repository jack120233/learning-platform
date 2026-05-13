# Research: existing docs baseline

- **Query**: Research the existing documentation baseline for the technical documentation task at `.trellis/tasks/05-11-current-architecture-technical-documentation`. Inspect root `README.md`, `CLAUDE.md`, `project_code/docs/*`, `UI/docs/*`, `UI/README.md`, and any obvious architecture/API/test docs, excluding node_modules, venv, pytest cache, and `.claude/worktrees`. Include current doc inventory, useful sources, stale/partial docs, recommended output location and structure for the new document.
- **Scope**: internal
- **Date**: 2026-05-11

## Findings

### Files Found

| File Path | Description |
|---|---|
| `README.md` | Root monorepo/dev-start README; currently focused on macOS one-click startup, service ports, and log path. |
| `CLAUDE.md` | Root coordination guide; strongest current full-stack architecture summary and directory-routing rules. |
| `UI/README.md` | Default Vue/Vite template README; not project-specific. |
| `UI/CLAUDE.md` | Frontend project guide; current source for frontend tech stack, directory layout, API base, routing, store, and auth conventions. |
| `UI/docs/login-auth-issue-review.md` | Detailed frontend auth/state-management postmortem and formal conventions. |
| `UI/docs/course-id-mismatch-review.md` | Focused postmortem for course `id` vs `course_id` mismatch. |
| `UI/docs/前端接口文档.md` | Frontend-facing API contract document; includes upload, feedback, teacher/admin statistics additions, but also older field assumptions. |
| `UI/api-frontend-quick-reference.md` | Frontend quick reference copied from backend inventory; useful structure, but older counts and endpoint set. |
| `UI/前端架构设计文档.md` | Early frontend architecture proposal; useful only as historical intent, not current implementation source. |
| `UI/前后端接口文档差异对照.md` | Historical comparison of frontend and backend API document differences; useful for knowing legacy mismatch areas, but not current truth. |
| `UI/前端接口文档.md` | Older frontend API document at UI root; overlaps with `UI/docs/前端接口文档.md` and includes stale assumptions. |
| `project_code/CLAUDE.md` | Backend project guide; source for backend stack, module structure, commands, and backend docs index. |
| `project_code/docs/architecture.md` | Backend architecture document; source for backend layering, app structure, models, response format, and deployment basics, but endpoint/module counts are older. |
| `project_code/docs/api-endpoint-inventory.md` | Most detailed backend factual endpoint inventory with file/line references, schemas, test mappings, and upload endpoints; internally inconsistent counts require care. |
| `project_code/docs/api-testing-guide.md` | Manual API testing guide with startup steps, test accounts, auth flow, upload/material/resource examples, and curl examples; contains an older duplicate test-account section. |
| `project_code/docs/test-plan.md` | Backend pytest/httpx test-plan document; useful for intended test layout and commands, but stale on endpoint count and actual test file organization. |
| `project_code/docs/worktree-guide.md` | Git worktree guide; not a source for architecture, API, or validation behavior. |
| `project_code/docs/plans/2026-04-09-backend-upload-and-resource-apis.md` | Implementation plan for upload/resource API work; useful as history for why upload docs changed, not as current-state truth. |
| `project_code/5.接口文档.md` | Older full API specification; useful as legacy requirement/source of stale assumptions, not current truth without code verification. |
| `project_code/2.用户认证模块详情文档.md` and numbered module docs | Legacy module requirement docs listed by backend CLAUDE; useful for business intent only. |
| `project_code/context-summary-api-endpoint-inventory.md` | Historical context summary for API inventory; treat as secondary. |
| `project_code/context-summary-api-frontend-quick-reference.md` | Historical context summary for frontend quick reference; treat as secondary. |
| `.trellis/spec/frontend/*.md` | Current Trellis frontend guidelines index and package-level conventions. |
| `.trellis/spec/backend/*.md` | Current Trellis backend guidelines index and package-level conventions. |
| `.trellis/spec/guides/*.md` | Cross-layer/code-reuse thinking guides; relevant for organizing future documentation and verification thinking. |
| `.trellis/tasks/05-11-current-architecture-technical-documentation/prd.md` | Task PRD defining desired new current-state technical document scope. |

### Current Documentation Inventory

#### Root-level docs

- `README.md` is minimal and operational. It documents `./start-dev-macos.sh`, the expected local service ports for MySQL, Redis, backend, and Vite frontend, and the `logs/dev/` location (`README.md:0-25`). It does not describe project architecture beyond dev startup.
- `CLAUDE.md` is the most useful current root-level baseline. It explicitly says the workspace contains two independently evolved subprojects, `UI` and `project_code` (`CLAUDE.md:4-11`), and summarizes the current high-level architecture: Vue 3 + TypeScript + Vite frontend, FastAPI + SQLAlchemy + Pydantic backend, frontend entry/API/store/router, backend entry/router/config/tests, and shared API/auth/role/response conventions (`CLAUDE.md:71-80`). It also contains detailed directory-routing rules for frontend, backend, and integration work (`CLAUDE.md:98-160`), plus validation expectations (`CLAUDE.md:318-355`).
- `AGENTS.md`, `handoff.md`, `前端对应接口.md`, and `优化资源上传计划.md` exist at root. The obvious technical-doc candidates among these are `前端对应接口.md` and `优化资源上传计划.md`; based on filename and scope they should be treated as task-specific or historical unless checked against code/current docs.

#### Frontend docs

- `UI/README.md` is still the default Vue 3 + TypeScript + Vite template (`UI/README.md:0-4`). It is not a good source for project-specific architecture.
- `UI/CLAUDE.md` is the best frontend baseline. It documents the frontend stack (`UI/CLAUDE.md:32-42`), current directory structure (`UI/CLAUDE.md:43-70`), API layer and Vite proxy (`UI/CLAUDE.md:74-80`), route permissions (`UI/CLAUDE.md:82-90`), Pinia state management (`UI/CLAUDE.md:92-98`), auto-import setup (`UI/CLAUDE.md:100-107`), auth-store single-source-of-truth rule (`UI/CLAUDE.md:111-148`), API base/response/pagination format (`UI/CLAUDE.md:176-181`), and frontend reference docs (`UI/CLAUDE.md:183-188`).
- `UI/docs/login-auth-issue-review.md` is highly useful for current frontend auth conventions. It documents the login/auth bugs and formalizes the rule that business code must not directly read localStorage, with `useUserStore()` as the single source for auth/role state (`UI/docs/login-auth-issue-review.md:463-679`). It also provides concrete examples of the actual login response nesting and frontend mapping (`UI/docs/login-auth-issue-review.md:181-275`).
- `UI/docs/course-id-mismatch-review.md` is useful for a narrow integration caveat: backend course primary key can be `id` while older frontend used `course_id`, causing `/courses/undefined` (`UI/docs/course-id-mismatch-review.md:8-35`).
- `UI/docs/前端接口文档.md` is useful as a frontend-facing API inventory and includes newer additions such as feedback image upload and teacher/admin learning statistics (`UI/docs/前端接口文档.md:48-57`, `UI/docs/前端接口文档.md:157-171`, `UI/docs/前端接口文档.md:220-244`). However, it also begins with older auth field assumptions such as `login_id` for login and extra registration fields (`UI/docs/前端接口文档.md:6-16`), so it is partial rather than authoritative.
- `UI/api-frontend-quick-reference.md` is useful as a compact format model, but it is stale relative to the newer backend inventory: it states 11 modules / 68 interfaces (`UI/api-frontend-quick-reference.md:8-18`), while `project_code/docs/api-endpoint-inventory.md` now attempts to cover upload and other newer endpoints. It still provides a good quick-reference structure (`UI/api-frontend-quick-reference.md:89-217`).
- `UI/前端架构设计文档.md` is an early architecture proposal. It contains a general Vue/TS/Vite/Element Plus/Axios architecture and feature-based layout (`UI/前端架构设计文档.md:2-40`), but references planned concepts such as `/api/v1/tasks/{taskId}/materials` and `/api/v1/study/progress` (`UI/前端架构设计文档.md:69-74`) that do not match the current shared `/learning/...` conventions. Use as historical intent only.
- `UI/前后端接口文档差异对照.md` is a useful map of known historical frontend/backend mismatches, including `login_id` vs `username`, homepage pagination vs limit, learning progress model, feedback type fields, and delete route differences (`UI/前后端接口文档差异对照.md:9-56`, `UI/前后端接口文档差异对照.md:61-130`). It should not be treated as current truth because some listed gaps have since been resolved by upload/resource work.
- `UI/前端接口文档.md` at the UI root is older than the `UI/docs/前端接口文档.md` copy: it still documents `login_id`, `avatar_url`, `DELETE`/`POST .../delete` discrepancies, and lacks newer statistics sections (`UI/前端接口文档.md:6-17`, `UI/前端接口文档.md:52-72`, `UI/前端接口文档.md:140-184`). Treat as stale.

#### Backend docs

- `project_code/CLAUDE.md` is the best backend guidance baseline. It documents backend tech stack (`project_code/CLAUDE.md:14-23`), architecture conventions for `/api/v1/`, unified response, Bearer Token, roles, and Course → Chapter → Section → Resource (`project_code/CLAUDE.md:25-38`), backend tree and test files (`project_code/CLAUDE.md:39-60`), and the docs index (`project_code/CLAUDE.md:62-71`). It also lists legacy requirement docs (`project_code/CLAUDE.md:73-83`).
- `project_code/docs/architecture.md` is useful for backend-only architecture: tech stack (`project_code/docs/architecture.md:7-23`), project structure (`project_code/docs/architecture.md:24-99`), layered architecture (`project_code/docs/architecture.md:101-139`), core components (`project_code/docs/architecture.md:141-184`), data model overview (`project_code/docs/architecture.md:185-244`), response formats (`project_code/docs/architecture.md:245-289`), and basic module list (`project_code/docs/architecture.md:291-307`). It appears stale for current API scope because it lists 11 modules and omits the upload module from its module table (`project_code/docs/architecture.md:291-307`).
- `project_code/docs/api-endpoint-inventory.md` is the most valuable API source because it claims to derive from actual mounted FastAPI routes and includes code locations and test files (`project_code/docs/api-endpoint-inventory.md:8-15`, `project_code/docs/api-endpoint-inventory.md:131-140`). It includes upload endpoints and newer user/feedback/resource fields (`project_code/docs/api-endpoint-inventory.md:239-248`, `project_code/docs/api-endpoint-inventory.md:282-358`). Caveat: the totals conflict internally: it says 81 business interfaces in the overview (`project_code/docs/api-endpoint-inventory.md:50-58`), but its statistical check sums to 85 and notes old totals are not synchronized (`project_code/docs/api-endpoint-inventory.md:76-82`), while the conclusion again says 81 (`project_code/docs/api-endpoint-inventory.md:360-365`).
- `project_code/docs/api-testing-guide.md` is useful for manual validation flows: current seed accounts are documented near the top (`project_code/docs/api-testing-guide.md:30-45`), auth flow and token usage are covered (`project_code/docs/api-testing-guide.md:76-183`), and upload/material/resource examples are included (`project_code/docs/api-testing-guide.md:258-412`). Caveat: it contains an older duplicate test account table later (`project_code/docs/api-testing-guide.md:608-617`), so use the top account table and root `CLAUDE.md` as the current account baseline.
- `project_code/docs/test-plan.md` is useful for validation-command patterns, fixtures intent, and test module scope (`project_code/docs/test-plan.md:19-24`, `project_code/docs/test-plan.md:25-49`, `project_code/docs/test-plan.md:439-456`). It appears stale because it states 68 endpoints (`project_code/docs/test-plan.md:7-18`) and lists planned files like separate `test_messages.py`, `test_categories.py`, `test_tags.py`, and `test_announcements.py`, while current docs map those to `test_feedbacks.py` / `test_system.py` in places (`project_code/docs/api-endpoint-inventory.md:61-74`).
- `project_code/docs/worktree-guide.md` is not a source for the new architecture doc. It documents Git worktree usage and older directory examples (`project_code/docs/worktree-guide.md:15-30`) rather than current product architecture.
- `project_code/docs/plans/2026-04-09-backend-upload-and-resource-apis.md` is useful historical context for why upload/resource endpoints and compatibility routes exist. It describes the planned upload/resource lifecycle and files changed (`project_code/docs/plans/2026-04-09-backend-upload-and-resource-apis.md:4-9`, `project_code/docs/plans/2026-04-09-backend-upload-and-resource-apis.md:356-409`). Treat as implementation history, not current-state reference.
- `project_code/5.接口文档.md` and numbered module docs are legacy API/requirement docs. They include old fields such as `login_id`, `captcha_id`, `avatar_url`, `course_id`, and older assumptions (`project_code/5.接口文档.md:182-289`, `project_code/5.接口文档.md:464-535`, `project_code/5.接口文档.md:869-1340`). They are useful for business-intent background only.

#### Trellis specs and task docs

- `.trellis/spec/frontend/index.md` and `.trellis/spec/backend/index.md` are current indexes for package-specific conventions and both say guideline files are filled (`.trellis/spec/frontend/index.md:12-22`, `.trellis/spec/backend/index.md:12-21`). They are process/convention sources, not architecture inventory docs.
- `.trellis/spec/guides/index.md` is useful for the new document's cross-layer checklist because it calls out data-format changes, multiple consumers, and layer-boundary risks (`.trellis/spec/guides/index.md:30-37`).
- `.trellis/tasks/05-11-current-architecture-technical-documentation/prd.md` states the desired goal: produce a current technical document based on original docs, with current code as truth, covering frontend, backend, integration/API, permissions/roles, core business functions, and validation (`.trellis/tasks/05-11-current-architecture-technical-documentation/prd.md:2-13`, `.trellis/tasks/05-11-current-architecture-technical-documentation/prd.md:24-35`).

### Code Patterns

No application code was modified or analyzed deeply for this baseline task. The documentation pattern that emerges is:

1. **Root `CLAUDE.md` is the current cross-project coordination layer.** It defines the two-subproject workspace and shared conventions (`/api/v1`, Bearer Token, `student`/`teacher`/`admin`, `{ code, message, data }`) (`CLAUDE.md:71-80`, `CLAUDE.md:286-294`).
2. **Frontend docs are split between current rules and historical API assumptions.** `UI/CLAUDE.md` and `UI/docs/login-auth-issue-review.md` are strong current sources for frontend architecture and auth state; API docs in `UI/docs/前端接口文档.md` are useful but need verification against backend inventory and frontend API wrappers.
3. **Backend docs have one strong factual endpoint inventory plus older architecture/test docs.** `project_code/docs/api-endpoint-inventory.md` is the best API source, but its own total counts conflict. `architecture.md` is useful for layering and structure but has older module totals.
4. **Historical mismatch docs are valuable warnings.** `UI/前后端接口文档差异对照.md`, `UI/docs/course-id-mismatch-review.md`, and `UI/docs/login-auth-issue-review.md` identify recurring integration risks: field names, ID aliases, nested response structure, and auth state sources.
5. **Several docs duplicate API lists.** Current technical documentation should not become another full endpoint inventory. It should reference `project_code/docs/api-endpoint-inventory.md` for detailed endpoint rows and summarize only the stable cross-layer contract and major business modules.

### External References

- None. The request was an internal documentation-baseline research task.

### Related Specs

- `.trellis/spec/frontend/index.md` — Index for frontend convention docs.
- `.trellis/spec/backend/index.md` — Index for backend convention docs.
- `.trellis/spec/guides/cross-layer-thinking-guide.md` — Relevant for documenting frontend/backend contract and verification boundaries.
- `.trellis/tasks/05-11-current-architecture-technical-documentation/prd.md` — Task source for desired document scope and acceptance criteria.

## Recommended Sources for the New Technical Document

Use these as primary sources:

1. `CLAUDE.md` — current cross-project architecture, directory routing, shared conventions, validation rules.
2. `UI/CLAUDE.md` — current frontend architecture, stack, structure, auth/store/router/API conventions.
3. `project_code/CLAUDE.md` — current backend architecture conventions, stack, commands, docs index.
4. `project_code/docs/api-endpoint-inventory.md` — detailed endpoint inventory, response fields, code/test mappings, with count caveat.
5. `project_code/docs/api-testing-guide.md` — manual auth/API/upload validation flows and current seed accounts near the top.
6. `UI/docs/login-auth-issue-review.md` — frontend auth single-source-of-truth rule and login response shape.
7. `UI/docs/course-id-mismatch-review.md` — current integration caveat for `id`/`course_id` handling.
8. `UI/docs/前端接口文档.md` — frontend-facing API surface, especially newer upload/feedback/statistics sections; verify field assumptions.
9. `.trellis/spec/*` — current implementation conventions and cross-layer thinking checklists.

Use these only as secondary/historical sources:

1. `project_code/docs/architecture.md` — backend architecture structure/layering, but update module/API counts against current code or endpoint inventory.
2. `project_code/docs/test-plan.md` — validation strategy and command patterns, but update endpoint/test-file assumptions.
3. `project_code/docs/plans/2026-04-09-backend-upload-and-resource-apis.md` — background on upload/resource API decisions.
4. `UI/前后端接口文档差异对照.md` — historical mismatch checklist.
5. `UI/前端架构设计文档.md` — early frontend architecture intent, not current implementation truth.
6. `project_code/5.接口文档.md` and numbered module docs — old business/API requirements, not current route/source truth.

## Stale or Partial Documentation Notes

- `UI/README.md` is not project-specific; do not use as architecture source.
- `README.md` is useful only for dev startup, not architecture.
- `project_code/docs/api-endpoint-inventory.md` is the strongest API source but has inconsistent endpoint totals (81 vs arithmetic 85). The new document should avoid restating a precise endpoint total unless code is re-counted.
- `project_code/docs/architecture.md` appears older because it omits the upload module in its module table and lists lower endpoint/module counts.
- `project_code/docs/test-plan.md` appears older because it states 68 endpoints and planned test files that do not match later endpoint inventory mappings.
- `project_code/docs/api-testing-guide.md` has two test-account sections; prefer the top section and root/project CLAUDE test-account tables.
- `UI/docs/前端接口文档.md` contains newer teacher/admin statistics content but older auth/request fields; use as frontend-consumer reference only.
- `UI/api-frontend-quick-reference.md` says 11 modules / 68 interfaces and is stale relative to newer upload/statistics work.
- `UI/前端接口文档.md` and `project_code/5.接口文档.md` are older API docs with stale fields such as `login_id`, `avatar_url`, and older `course_id` assumptions.
- `.spec-workflow` template docs exist in root, UI, and project_code, but root `CLAUDE.md` says root `.spec-workflow` is only plugin-created and not the current unified workflow entry (`CLAUDE.md:296-300`). Do not use these templates as current project docs.

## Recommended Output Location and Structure

### Recommended location

Because the new document is explicitly cross-project and should cover frontend, backend, integration/API, permissions/roles, core business functions, and validation, the best long-term location is a root-level full-stack documentation entry:

- Preferred: `docs/current-architecture.md`

Rationale:

- `project_code/docs/` is backend-scoped and would make a full-stack architecture doc look backend-owned.
- `UI/docs/` is frontend-scoped and would make backend/API validation content harder to discover.
- Root `README.md` is already the root operational entry; a root `docs/current-architecture.md` would become the canonical current-state technical document and can be linked from root `README.md`, `UI/CLAUDE.md`, and `project_code/CLAUDE.md` later if desired.

If the project does not want a new root `docs/` directory, fallback location:

- `project_code/docs/current-architecture.md`, with an explicit title/subtitle that it is a workspace-level document covering both `UI` and `project_code`, not backend-only.

### Recommended structure

Suggested outline for the new current-state technical document:

1. **Purpose and Source-of-Truth Policy**
   - State that the document summarizes current architecture, not a complete endpoint reference.
   - State that current code and `project_code/docs/api-endpoint-inventory.md` override older API docs.
   - Include a “known stale source docs” subsection.
2. **Workspace Overview**
   - Two subprojects: `UI` frontend and `project_code/backend` backend.
   - Runtime ports and startup commands from root `README.md` and `CLAUDE.md`.
3. **Shared Cross-Layer Contract**
   - `/api/v1`, Bearer Token, roles `student`/`teacher`/`admin`, `{ code, message, data }`, pagination shape.
   - ID/field compatibility caveats such as `id` vs `course_id`, `avatar` vs older `avatar_url`, `username` vs older `login_id`.
4. **Frontend Architecture**
   - Stack: Vue 3, TypeScript, Vite, Element Plus, Pinia, Vue Router, Axios, SCSS.
   - Entry points: `UI/src/main.ts`, `UI/src/App.vue`, `UI/src/router/index.ts`, `UI/src/store/user.ts`, `UI/src/api/index.ts`.
   - Directory layout by `api`, `views`, `components`, `layouts`, `store`, `router`, `composables`, `assets/styles`.
   - Auth state single-source-of-truth through `useUserStore()`.
   - Frontend API wrapper conventions and Vite proxy.
5. **Backend Architecture**
   - Stack: FastAPI, SQLAlchemy async, Pydantic, pydantic-settings, JWT, Redis, pytest/httpx.
   - Entry points: `project_code/backend/app/main.py`, `app/api/v1/router.py`, `app/config.py`.
   - Layers: API routes, schemas, services, models, core dependencies/security/exceptions/logging, middleware.
   - Static uploads and configuration notes.
6. **Core Business Modules**
   - Auth/users, courses/content/resources/uploads, learning/progress/statistics, feedback/messages, system/category/tag/announcement, admin/teacher/student flows.
   - Keep each module at summary level and link to endpoint inventory for details.
7. **Permissions and Roles**
   - Frontend route meta/store permission checks.
   - Backend login requirement vs role/RBAC caveat from endpoint inventory.
   - Current test accounts.
8. **API and Integration Reference Map**
   - Link to `project_code/docs/api-endpoint-inventory.md` as detailed endpoint table.
   - Link to `UI/docs/前端接口文档.md` as frontend-facing consumer expectations.
   - Note documents requiring verification before use.
9. **Validation and Development Commands**
   - Frontend build/type-check commands.
   - Backend pytest commands.
   - Integration validation expectations.
10. **Documentation Maintenance Rules**
   - When routes change: update endpoint inventory first.
   - When frontend contract changes: update frontend API docs.
   - When auth/role conventions change: update root and subproject CLAUDE docs or the new current-architecture doc.

## Caveats / Not Found

- `python3 ./.trellis/scripts/task.py current --source` failed because this checkout's `task.py` does not expose a `current` command. The requested task directory was provided explicitly, so the research file was written there.
- This research did not verify current code implementation line-by-line; it inventories and classifies the documentation baseline only.
- The search intentionally excluded `node_modules`, virtualenv directories, `.pytest_cache`, and `.claude/worktrees`. Other `.claude` files outside worktrees appeared in broad inventory output but are not recommended as project documentation sources unless explicitly needed.
- Several API docs conflict with each other. For the new current-state document, avoid precise endpoint totals unless the implementer re-counts current mounted routes from code or resolves the `api-endpoint-inventory.md` total mismatch.
