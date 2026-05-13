# current architecture technical documentation

## Goal

梳理当前项目实际开发逻辑和功能，参考原有技术/架构文档，整理一份反映当前代码现状的技术文档，降低后续开发、联调和验收时对过期资料的依赖。

## What I already know

* 用户希望参考原有文档，而不是从零另起一套。
* 当前项目已经改动较多，旧文档与当前实现存在差异，需要以现有代码为准。
* 文档应覆盖前端、后端、联调/API、权限/角色、核心业务功能与开发验证方式。
* 项目是 Vue 3 + TypeScript + Vite 前端，以及 FastAPI + SQLAlchemy + Pydantic 后端。
* 联调统一口径包括 `/api/v1`、Bearer Token、角色 `student`/`teacher`/`admin`、响应结构 `{ code, message, data }`。
* 现有文档中，`CLAUDE.md`、`UI/CLAUDE.md`、`project_code/CLAUDE.md`、`project_code/docs/api-endpoint-inventory.md`、`project_code/docs/api-testing-guide.md`、`UI/docs/login-auth-issue-review.md`、`UI/docs/course-id-mismatch-review.md` 最适合作为参考源。
* `project_code/docs/architecture.md`、`project_code/docs/test-plan.md`、`UI/docs/前端接口文档.md` 等文档有参考价值，但部分模块/API/字段描述已经过期，需要在新文档中明确以当前代码为准。

## Requirements

* 新文档应是全栈当前状态技术文档，而不是仅前端或仅后端文档。
* 文档应覆盖：目的与资料可信度、工作区总览、跨层联调约定、前端架构、后端架构、核心业务模块、角色权限、API/集成资料索引、开发验证命令、文档维护规则。
* 文档应总结核心业务功能，但不重复维护完整逐接口清单；详细 API 以 `project_code/docs/api-endpoint-inventory.md` 为主要引用，且说明其计数存在需复核的问题。
* 文档应指出常见历史差异风险：`username` vs 旧 `login_id`、`id` vs `course_id`、旧接口数量/模块清单、认证状态应以 `useUserStore()` 为前端单一来源。
* 本任务只改文档，不改业务代码。

## Acceptance Criteria

* [ ] 文档反映当前仓库实际代码结构和主要功能模块。
* [ ] 文档覆盖前端、后端、联调/API、权限/角色、核心业务功能和验证方式。
* [ ] 文档参考并整合现有文档，而不是重复制造冲突入口。
* [ ] 文档写入明确位置，方便后续维护。
* [ ] 文档明确哪些旧资料只能作为历史参考，哪些当前资料更可信。

## Definition of Done

* 文档更新完成并与当前代码结构核对。
* 如仅修改文档，说明无需运行构建/测试的原因。
* 若发现现有文档明显过期，记录在新文档中或在任务说明中指出。

## Technical Approach

建议新增根级全栈文档 `docs/current-architecture.md`。理由：本任务覆盖 `UI` 和 `project_code/backend` 两个子项目，放在 `UI/docs` 会偏前端，放在 `project_code/docs` 会偏后端；根级 `docs/` 更适合作为当前联合项目的架构入口。

文档结构建议：

1. 目的与资料可信度
2. 工作区与运行时总览
3. 前后端共享联调契约
4. 前端架构
5. 后端架构
6. 核心业务模块
7. 角色、权限与认证流
8. API 与集成资料索引
9. 开发、测试与验证命令
10. 文档维护规则

## Decision (ADR-lite)

**Context**: 现有文档分散在根目录、`UI/`、`project_code/`，且部分旧接口/架构文档已经落后于当前实现。

**Decision**: 以当前代码和当前 CLAUDE/Trellis 规则为准，新增一份全栈当前架构技术文档；旧文档只作为来源和差异提示，不直接复制过期内容。

**Consequences**: 新文档将成为当前开发总览入口，但详细 API 清单仍引用现有 endpoint inventory，避免维护多个逐接口清单造成新的分歧。

## Out of Scope

* 不改业务代码。
* 不重写完整逐接口 API 文档。
* 不修复代码与文档发现的不一致问题，仅记录当前状态和维护建议。
* 不整理 node_modules、venv、`.claude/worktrees` 中的历史/依赖文档。

## Research References

* [`research/frontend-current-architecture.md`](research/frontend-current-architecture.md) — 当前前端入口、路由、状态、API、页面模块、权限流与旧文档差异。
* [`research/backend-current-architecture.md`](research/backend-current-architecture.md) — 当前后端入口、路由、配置、数据库会话、分层、权限、模块与旧文档差异。
* [`research/existing-docs-baseline.md`](research/existing-docs-baseline.md) — 现有文档盘点、可信来源、过期文档说明和推荐输出结构。

## Technical Notes

* Task directory: `.trellis/tasks/05-11-current-architecture-technical-documentation`
* Preferred output: `docs/current-architecture.md`
