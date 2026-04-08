# 操作记录

## 编码前检查 - 实际接口清单文档
时间：2026-03-27

- 已查阅上下文摘要文件：`.claude/context-summary-api-endpoint-inventory.md`
- 将使用以下可复用组件：
  - `backend/app/main.py:87-108`：确认 `/api/v1` 挂载链路与排除项。
  - `backend/app/api/v1/router.py:16-26`：确认 11 个已挂载模块。
  - `backend/app/core/dependencies.py:61-163`：统一认证判定口径。
  - `backend/app/schemas/common.py:15-68`：统一响应包装口径。
- 将遵循命名约定：模块名沿用路由 `tags` / 文件名；接口以“方法 + 完整路径”唯一标识。
- 将遵循代码风格：文档使用 Markdown 表格，逐模块分节，保留 `file_path:line` 代码定位。
- 确认不重复造轮子：本次新增 `docs/api-endpoint-inventory.md`，不改写现有 `docs/api-testing-guide.md` 与 `docs/architecture.md`。

## 研究结论
- 业务接口统计范围：`backend/app/api/v1/*.py` 中已由 `router.py` 实际挂载的 11 个模块。
- 认证判定：`CurrentUserId` = 需要 Bearer Token；当前未发现已挂载业务路由使用 `OptionalUserId`。
- 当前静态基线：68 个业务接口，不含 `GET /`、`/docs`、`/redoc`、`/openapi.json`。

## 课程封面上传接口补充
时间：2026-04-02

- 变更原因：前端在线学习视频页面联调时缺少课程封面上传接口，前端已固定访问 `/api/v1/upload/file`，需要后端补齐该能力。
- 涉及文件：
  - `backend/app/api/v1/uploads.py`
  - `backend/app/api/v1/router.py`
  - `backend/app/services/upload_service.py`
  - `backend/app/services/__init__.py`
  - `backend/app/schemas/course.py`
  - `backend/app/config.py`
  - `backend/app/main.py`
  - `backend/tests/test_courses.py`
- 核心改动：
  - 新增 `/api/v1/upload/file` 接口，接收 `multipart/form-data` 的 `file` 字段。
  - 新增课程封面上传服务，限制仅支持 `JPG/PNG`，单文件最大 `10MB`。
  - 增加讲师/管理员角色校验，普通学员不可调用该上传接口。
  - 将上传文件保存到本地 `backend/uploads/course-covers/`，并通过 `/uploads/...` 提供静态访问。
  - 上传响应补充 `file_name`、`file_url`、`url`、`file_size`、`content_type`，其中 `url` 与 `file_url` 保持一致，兼容前端组件读取。
  - 在课程测试中新增上传成功、非法格式、角色权限校验，并验证返回地址可直接访问文件内容。
- 验证结果：
  - 已执行：`python -m pytest tests/test_courses.py -k CourseCoverUpload -q`
  - 结果：`3 passed`
  - 备注：完整 `tests/test_courses.py` 仍受现有 `passlib/bcrypt` 测试环境问题影响，本次仅对新增上传接口做了定向验证。

## 协作约束补充
时间：2026-04-02

- 变更原因：为了避免后续文件新增或修改后缺少落盘记录，需要把“所有实际文件变更都要登记到 `operations-log.md`”固化到仓库协作约束中。
- 涉及文件：
  - `CLAUDE.md`
  - `operations-log.md`
- 核心改动：
  - 在 `CLAUDE.md` 的“文件写入规范”中新增日志登记要求。
  - 明确记录项至少包含变更时间、原因、涉及文件、核心改动、验证结果。
- 验证结果：
  - 文档约束已更新，并已用本次上传接口改动作为首个补录示例。

## 课程简介字段与章节/小节排序接口
时间：2026-04-03

- 变更原因：课程创建接口需要新增 `summary` 简介字段，同时前端联调需要支持章节排序和小节排序接口，并同步更新对应文档说明。
- 涉及文件：
  - `backend/app/models/course.py`
  - `backend/app/schemas/course.py`
  - `backend/app/services/course_service.py`
  - `backend/app/api/v1/courses.py`
  - `backend/scripts/init_db.py`
  - `backend/tests/test_courses.py`
  - `backend/app/schemas/content.py`
  - `backend/app/services/content_service.py`
  - `backend/app/api/v1/content.py`
  - `backend/tests/test_content.py`
  - `4.课程管理模块详情.md`
  - `docs/architecture.md`
  - `operations-log.md`
- 核心改动：
  - 为 `courses` 表模型新增 `summary` 字段，并接入 `POST /api/v1/courses`、课程详情响应及相关 schema。
  - 在数据库初始化脚本中补充 `courses.summary` 字段缺失时的兼容补列逻辑。
  - 更新课程管理与架构设计文档，补充 `summary` 字段的接口参数和表结构说明。
  - 新增 `POST /api/v1/courses/{course_id}/chapters/sort` 接口，请求体为 `chapter_ids`，按传入顺序重排章节 `sort_order`。
  - 新增 `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/sections/sort` 接口，请求体为 `section_ids`，按传入顺序重排小节 `sort_order`。
  - 为章节/小节排序补充成功与参数校验测试，采用直接造 token 的方式避免受现有登录测试环境影响。
- 验证结果：
  - 已执行：`python -m pytest tests/test_content.py -k "sort_chapters" -q`
  - 结果：`2 passed`
  - 已执行：`python -m pytest tests/test_content.py -k "sort_sections" -q`
  - 结果：`2 passed`
  - 已执行：`python -m compileall app/api/v1/content.py app/services/content_service.py app/schemas/content.py tests/test_content.py`
  - 结果：通过
  - 已执行：内存 SQLite 下定向验证课程 `summary` 创建与响应序列化链路
  - 备注：完整 `tests/test_courses.py` 仍受现有 `passlib/bcrypt` 测试环境问题影响，本次未做全量回归。

## 仓库改动 review 与提交流程收尾
时间：2026-04-08

- 变更原因：对当前未提交改动做集中 review，并在提交前补一处日志安全收口和开发产物忽略规则，减少把敏感 SQL 参数和运行产物带入仓库的风险。
- 涉及文件：
  - `backend/app/config.py`
  - `.gitignore`
  - `operations-log.md`
- 核心改动：
  - 将 `database_log_parameters` 默认值从开启调整为关闭，避免 SQL 绑定参数默认落入日志。
  - 在 `.gitignore` 中补充覆盖率文件、pytest 缓存、运行日志目录和上传目录的忽略规则。
  - 记录本次 review、验证与提交整理动作，方便后续追溯。
- 验证结果：
  - 已执行：`.\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_courses.py backend/tests/test_content.py backend/tests/test_system.py backend/tests/test_logging.py -q`
  - 结果：`31 passed`
