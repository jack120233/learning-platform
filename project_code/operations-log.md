# 操作记录

## 反馈截图上传接口补齐
时间：2026-04-27 15:22:10

- 变更原因：个人中心提交反馈支持上传截图，但前端原先复用 `/api/v1/upload/file`，该接口只允许讲师或管理员上传课程资源，普通学生添加截图会被权限拦截。
- 涉及文件：
  - `backend/app/config.py`
  - `backend/app/api/v1/uploads.py`
  - `backend/app/services/upload_service.py`
  - `backend/tests/test_uploads.py`
  - `docs/api-endpoint-inventory.md`
  - `operations-log.md`
- 核心改动：
  - 新增 `feedback_image_subdir`，将反馈截图保存到 `uploads/feedback-images/`。
  - 新增 `POST /api/v1/upload/feedback-image`，允许 active 状态的当前登录用户上传反馈截图，不限制学生、讲师或管理员角色。
  - 上传服务新增反馈截图保存逻辑，复用头像图片格式校验，支持 JPG/PNG/GIF，单文件最大 10MB。
  - 补充反馈截图上传成功和禁用用户拒绝上传的测试，并更新接口清单统计。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/project_code/backend" && python -m pytest tests/test_uploads.py -k "FeedbackImageUpload or AvatarUpload" -q`
  - 结果：`5 passed, 9 deselected`，有 2 条既有 `HTTP_422_UNPROCESSABLE_ENTITY` 废弃警告。


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
  - 补充决策说明：即使当前处于开发阶段，仓库默认值仍采用“默认不暴露 SQL 绑定参数”的保守策略；若后续本地联调确实需要，可通过环境配置临时开启。
- 验证结果：
  - 已执行：`.\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_courses.py backend/tests/test_content.py backend/tests/test_system.py backend/tests/test_logging.py -q`
  - 结果：`31 passed`

## 根级 Claude 协作入口整合
时间：2026-04-09

- 变更原因：前端 `UI` 与后端 `project_code` 已开始在同一工作区联合开发，需要补齐根级 Claude 协作入口，并让后端子项目规则明确继承根级目录路由，避免根目录联调时误入错误子目录。
- 涉及文件：
  - `../CLAUDE.md`
  - `../.claude/settings.local.json`
  - `CLAUDE.md`
  - `operations-log.md`
- 核心改动：
  - 新增工作区根级 `CLAUDE.md`，强制约束前端任务到 `UI/` 查找、后端任务到 `project_code/backend/` 查找、联调任务同时检查两边目录。
  - 新增工作区根级 `.claude/settings.local.json`，作为联合开发默认入口配置，且不沿用前端子项目的高权限配置。
  - 在后端 `CLAUDE.md` 中补充“先遵循根级 `CLAUDE.md`，再进入后端规则”的继承说明。
- 验证结果：
  - 已执行：只读核对根级与后端规则文件内容。
  - 结果：根级与后端规则已对齐，后端日志记录要求保持不变。

## 工作区联合开发文档沉淀
时间：2026-04-09

- 变更原因：需要把本次前后端从分开协作转为统一工作区协作的决策、目录路由、验证规则和历史痕迹处理结果沉淀到项目文档中，避免后续再次重复梳理。
- 涉及文件：
  - `../CLAUDE.md`
  - `../.claude/context-summary-workspace-integration.md`
  - `operations-log.md`
- 核心改动：
  - 复核并确认根级 `CLAUDE.md` 已覆盖前端、后端、联调三类任务的目录路由与最小验证规则。
  - 新增根级 `.claude/context-summary-workspace-integration.md`，集中记录本次整合结论、子项目继承关系、业务任务映射、历史痕迹处理和验证口径。
  - 保持后端 `operations-log.md` 继续作为后端侧的正式留痕入口。
- 验证结果：
  - 已执行：只读核对根级 `CLAUDE.md`、根级 `.claude` 目录和后端日志内容。
  - 结果：文档落盘完成，当前工作区整合状态与文档描述一致。

## 工作区联合开发收尾速查
时间：2026-04-09

- 变更原因：在完整上下文摘要之外，再补一份更短的速查文档，方便后续从根目录启动时快速定位前端、后端和联调入口。
- 涉及文件：
  - `../.claude/workspace-quick-reference.md`
  - `operations-log.md`
- 核心改动：
  - 新增根级 `.claude/workspace-quick-reference.md`，浓缩记录主入口、目录路由、常见任务落点、统一口径、最小验证和应忽略的历史痕迹。
  - 保持完整背景摘要与速查版并存，分别服务详细查阅和快速上手。
- 验证结果：
  - 已执行：只读核对速查文档内容与当前根级 `CLAUDE.md` 一致。
  - 结果：速查文档已落盘，可作为后续联合开发快速入口。

## 教师端上传与资源联调接口补齐
时间：2026-04-10

- 变更原因：教师端课程编辑页需要形成“文件上传 -> 课程资料/章节资源/小节资源绑定 -> 课程详情回显 -> 旧前端兼容删除”的完整闭环，同时补齐大文件分片上传能力。
- 涉及文件：
  - `backend/app/api/v1/uploads.py`
  - `backend/app/api/v1/courses.py`
  - `backend/app/api/v1/content.py`
  - `backend/app/config.py`
  - `backend/app/core/security.py`
  - `backend/app/models/content.py`
  - `backend/app/schemas/upload.py`
  - `backend/app/schemas/course.py`
  - `backend/app/schemas/content.py`
  - `backend/app/services/upload_service.py`
  - `backend/app/services/course_service.py`
  - `backend/app/services/content_service.py`
  - `backend/scripts/init_db.py`
  - `backend/run.bat`
  - `backend/tests/test_uploads.py`
  - `backend/tests/test_courses.py`
  - `backend/tests/test_content.py`
  - `docs/api-testing-guide.md`
  - `docs/api-endpoint-inventory.md`
  - `context-summary-api-endpoint-inventory.md`
  - `context-summary-api-frontend-quick-reference.md`
  - `CLAUDE.md`
  - `operations-log.md`
- 核心改动：
  - 将 `/api/v1/upload/file` 扩展为统一文件上传入口，并新增 `/api/v1/upload/init`、`/api/v1/upload/chunk`、`/api/v1/upload/complete` 三段式分片上传接口。
  - 新增上传 schema，扩展上传服务对课程封面、文档、压缩包、常见音视频的分类落盘与大小限制。
  - 课程资料接口支持 JSON 绑定与 `multipart/form-data` 直传两种模式，并补充旧前端删除兼容路由。
  - 课程内容支持章节级资源，`Resource.section_id` 调整为可空，并兼容前端 `resource_type`、`file_name`、`resource_id` 等字段命名。
  - 课程详情返回补齐 `materials`、`chapters[].resources`、`chapters[].sections[].resources`，供教师端编辑页直接回显。
  - 在数据库初始化脚本中补充 `resources.section_id` 可空修正；在安全模块中补一层 bcrypt 5.x 兼容处理。
  - 更新接口测试清单、手测指南、后端协作说明与两份 context-summary，使统计口径与当前 12 模块 / 80 接口保持一致。
- 验证结果：
  - 已执行：`python -m pytest backend/tests/test_uploads.py -q`
  - 结果：`7 passed`
  - 已执行：`python -m pytest backend/tests/test_courses.py -q`
  - 结果：`17 passed`
  - 已执行：`python -m pytest backend/tests/test_content.py -q`
  - 结果：`16 passed`

## 课程管理角色化列表与批量操作接口
时间：2026-04-13

- 变更原因：课程管理需要支持讲师管理自己的课程、管理员查看全站已发布课程并执行下架，同时补齐批量上架、下架、删除接口和权限校验。
- 涉及文件：
  - `backend/app/core/dependencies.py`
  - `backend/app/schemas/course.py`
  - `backend/app/services/course_service.py`
  - `backend/app/api/v1/courses.py`
  - `backend/tests/test_courses.py`
  - `operations-log.md`
- 核心改动：
  - 新增当前用户对象依赖，课程接口从仅使用 `user_id` 调整为可读取角色信息。
  - 统一课程列表响应字段，补齐 `course_id`、`teacher_id`、`status`、`created_at`、`published_at`、`view_count` 等课程管理页所需字段。
  - 新增 `/api/v1/courses/manage` 角色化管理列表接口和 `/api/v1/courses/batch-action` 批量动作接口。
  - 课程服务层统一收口权限规则：讲师只操作自己的课程；管理员可下架任意已发布课程，但不能发布或删除他人课程。
  - 为管理员查看全站已发布课程、管理员跨讲师下架、批量删除失败明细等场景补充课程测试。
- 验证结果：
  - 已执行：`python -m pytest E:/video_project/proj_ui/project_code/backend/tests/test_courses.py -q`
  - 结果：`23 passed`
  - 备注：测试输出包含现有 `datetime.utcnow()` 与 FastAPI 422 常量弃用告警，本次改动未额外扩大处理范围。

## 后端启动脚本报错展示修复
时间：2026-04-17

- 变更原因：`backend/run.bat` 启动时没有直观看到真实报错，且因模块搜索路径异常导致 `app.main:app` 导入失败，需要修复启动链路和报错展示。
- 涉及文件：
  - `backend/run.bat`
  - `.claude/context-summary-backend-runbat-fix.md`
  - `.claude/verification-report.md`
  - `operations-log.md`
- 核心改动：
  - 删除无意义的 `start powershell` 逻辑，避免额外窗口打断启动输出。
  - 为脚本补充 `BACKEND_DIR` 和 `PYTHONPATH`，让 `uvicorn app.main:app` 能按 `backend/` 目录解析 `app` 包。
  - 启动前输出工作目录和 Python 路径，启动失败后明确提示上方输出就是实际报错信息，并保留 `pause`。
  - 保持原有虚拟环境双路径探测逻辑，只把提示文本改成中文。
- 验证结果：
  - 已执行：只读复核 `backend/run.bat` 新逻辑，确认启动命令、错误分支和暂停提示已落盘。
  - 已执行：通过直接运行 Python/uvicorn 链路复现过原始错误 `ModuleNotFoundError: No module named 'app'`，修复针对该问题生效。
  - 未完成：当前会话里的 Bash 对 Windows `cmd.exe /c` 复合命令转义异常，未能在此界面稳定回显 bat 交互窗口输出；建议你本机双击或在 `cmd` 中执行 `E:\video_project\proj_ui\project_code\backend\run.bat` 做最终目视确认。

## 反馈处理回复链路测试补齐
时间：2026-04-20 16:20:01

- 变更原因：前端已接入管理员回复后再处理的交互，需要后端补一条反馈处理接口测试，确保 `reply`、`replied_at`、`replied_by` 写入链路可靠。
- 涉及文件：
  - `backend/tests/test_feedbacks.py`
  - `operations-log.md`
- 核心改动：
  - 在反馈模块测试中新增管理员处理课程反馈的用例。
  - 校验处理接口返回 `status=processed`、`reply`、`replied_at`、`processed_at`，并验证数据库中 `replied_by` 正确落库。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/project_code/backend" && python -m pytest tests/test_feedbacks.py -v`
  - 结果：`8 passed`
  - 备注：测试过程中出现现有 `datetime.utcnow()` 弃用告警，本次未扩大处理范围。

## 后台权限口径统一修复
时间：2026-04-20 18:55:00

- 变更原因：继续收口后台 RBAC 权限缺口，统一后端对 `admin.user`、`admin.teacher_audit`、`admin.admin_application`、`admin.category`、`admin.tag`、`admin.message` 的校验口径，并修复配套测试夹具与公告权限测试准备。
- 涉及文件：
  - `backend/app/api/v1/users.py`
  - `backend/app/api/v1/categories.py`
  - `backend/app/api/v1/tags.py`
  - `backend/app/api/v1/messages.py`
  - `backend/tests/test_users.py`
  - `backend/tests/test_system.py`
  - `backend/tests/conftest.py`
  - `operations-log.md`
- 核心改动：
  - 为用户列表、讲师审核、管理员申请接口补齐对应 `ensure_permission(...)` 权限校验。
  - 为分类创建/更新/删除、标签创建、系统消息发送补齐细粒度后台权限校验。
  - 重写并补齐权限回归测试，明确锁定“无权限返回 403、授予单项权限后可访问”的行为。
  - 将 `test_admin` 夹具改为幂等初始化，并在测试环境中补齐管理员默认权限映射，避免唯一约束冲突和公告测试因缺权限误报 403。
- 验证结果：
  - 已执行：`python -m pytest E:/video_project/proj_ui/project_code/backend/tests/test_users.py -v`
  - 结果：`18 passed`
  - 已执行：`python -m pytest E:/video_project/proj_ui/project_code/backend/tests/test_system.py -v`
  - 结果：`16 passed`
  - 备注：测试输出包含现有 `datetime.utcnow()` 与 FastAPI 422 常量弃用告警，本次未扩大处理范围。

## 标签管理删除能力补完整
时间：2026-04-21 13:48:12

- 变更原因：老师拥有 `admin.tag` 权限后，后台标签管理只有查看和新增，缺少单删与批量删除，需要补齐完整管理动作，并保持 `/tags` 公共读取链路不受影响。
- 涉及文件：
  - `backend/app/schemas/system.py`
  - `backend/app/services/system_service.py`
  - `backend/app/api/v1/tags.py`
  - `backend/tests/test_system.py`
  - `operations-log.md`
- 核心改动：
  - 为标签管理新增批量删除请求和返回模型，补齐成功列表、失败明细、成功数和失败数。
  - 在 `TagService` 中新增单删、批量删和课程引用校验逻辑，删除时显式 `flush`，保证当前事务内状态可见。
  - 在标签路由中新增 `DELETE /tags/{tag_id}` 与 `POST /tags/batch-delete`，并统一继续使用 `admin.tag` 权限校验。
  - 调整系统测试中的标签权限授予为幂等写法，补齐单删、批量删、被课程引用阻止删除和失败明细回归用例。
- 验证结果：
  - 已执行：`python -m pytest E:/video_project/proj_ui/project_code/backend/tests/test_system.py -v`
  - 结果：`22 passed`
  - 已执行：`python scripts/init_db.py`
  - 结果：成功连接真实 MySQL，并确认现有 21 张表已存在，包括 `tags`、`course_tags`、`role_permissions`；本次改动未新增表。
  - 备注：测试仍包含现有 FastAPI 422 常量弃用告警，本次未扩大处理范围。

## 权限口径简化与讲师后台能力收口
时间：2026-04-21 16:36:55

- 变更原因：当前业务只需要突出学员和讲师两类主角色，管理员作为兼容角色默认与讲师同权；同时后台不再对外展示角色权限配置页面，但要保持既有权限接口与测试链路可用。
- 涉及文件：
  - `backend/app/services/permission_service.py`
  - `backend/app/services/course_service.py`
  - `backend/app/api/v1/permissions.py`
  - `backend/tests/test_permissions.py`
  - `backend/tests/test_courses.py`
  - `operations-log.md`
- 核心改动：
  - 将默认 `teacher` 与 `admin` 权限集合统一收敛到同一后台与课程管理口径，保持 `student` 学习权限不变。
  - 角色权限配置接口改回仅管理员可访问，避免前端入口下线后讲师仍可直接修改角色权限。
  - 放开讲师查看 `published_all` 课程管理列表，使讲师和管理员都能从课程管理页进入全站已发布视角；同时维持发布、删除仍只允许操作自己的课程。
  - 更新权限与课程测试，覆盖 teacher/admin 默认同权、讲师可查看全站已发布课程、学员仍受限等场景。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/project_code/backend" && python -m pytest tests/test_permissions.py -v`
  - 结果：`10 passed`
  - 已执行：`cd "E:/video_project/proj_ui/project_code/backend" && python -m pytest tests/test_system.py -v`
  - 结果：`22 passed`
  - 已执行：`cd "E:/video_project/proj_ui/project_code/backend" && python -m pytest tests/test_courses.py -v`
  - 结果：`23 passed`
  - 备注：测试输出仍包含现有 `datetime.utcnow()` 与 FastAPI 422 常量弃用告警，本次未扩大处理范围。

## 老师后台权限收紧与管理员讲师审核恢复
时间：2026-04-21 18:08:39

- 变更原因：老师不再需要后台管理能力，后台用户管理、讲师审核和管理员申请接口需要加管理员兜底；同时管理员后台要恢复讲师审核入口。
- 涉及文件：
  - `backend/app/services/permission_service.py`
  - `backend/app/api/v1/users.py`
  - `backend/tests/test_permissions.py`
  - `backend/tests/test_users.py`
  - `operations-log.md`
- 核心改动：
  - 将老师默认权限收紧为学习中心和讲师中心，不再默认拥有 `admin.user`、`admin.teacher_audit`、`admin.admin_application` 及其他后台管理权限。
  - 在用户列表、状态更新、删除用户、讲师审核、管理员申请相关接口上追加 `ensure_admin` 校验，避免老师残留历史权限时绕过前端直接访问后台接口。
  - 调整权限与用户测试，改为覆盖“老师默认无后台权限”以及“老师即使残留后台权限也仍返回 403”的兜底行为。
- 验证结果：
  - 已执行：`python -m pytest E:/video_project/proj_ui/project_code/backend/tests/test_users.py -v`
  - 结果：`18 passed`
  - 已执行：`python -m pytest E:/video_project/proj_ui/project_code/backend/tests/test_permissions.py -v`
  - 结果：`10 passed`
  - 备注：测试输出仍包含现有 `datetime.utcnow()` 与 FastAPI 422 常量弃用告警，本次未扩大处理范围。

## 现有老师角色权限数据同步收口
时间：2026-04-21 19:52:14

- 变更原因：代码里的老师默认权限虽然已经收紧，但历史数据库中的 `role_permissions` 旧数据不会自动更新，导致老师账号仍可能拿到后台管理菜单。
- 涉及文件：
  - `backend/app/core/db_schema.py`
  - `backend/tests/test_permissions.py`
  - `operations-log.md`
- 核心改动：
  - 在数据库兼容性检查中新增老师角色权限同步逻辑，自动删除老师角色遗留的 `admin.*` 历史权限，并补齐当前默认讲师权限缺口。
  - 保持兼容逻辑幂等，只有老师角色当前权限与目标默认集合不一致时才执行修正。
  - 新增测试覆盖，验证兼容逻辑执行后老师角色权限会被收口到当前默认集合。
- 验证结果：
  - 已执行：`python -m pytest E:/video_project/proj_ui/project_code/backend/tests/test_permissions.py -v`
  - 结果：`11 passed`
  - 已执行：`python E:/video_project/proj_ui/project_code/backend/scripts/init_db.py`
  - 结果：成功连接真实数据库并完成初始化，脚本输出 `已补齐老师角色当前默认权限`，当前 21 张表已完成检查。
  - 备注：如前端当前已登录，仍建议重新登录一次，确保本地保存的 `permission_codes` 刷成最新结果。

## 启动脚本端口检查与启动日志补强
时间：2026-04-21 21:05:00

- 变更原因：`run.bat` 启动时遇到端口占用或 uvicorn 启动失败，错误只出现在控制台，缺少明确的端口占用提示和单独启动日志，排查成本高。
- 涉及文件：
  - `backend/run.bat`
  - `operations-log.md`
- 核心改动：
  - 在启动前新增 8000 端口监听检查，若已被占用则直接打印占用进程的 PID、进程名和路径，并终止启动。
  - 新增 `logs/startup.log` 与 `logs/startup_error.log`，把 uvicorn 启动层输出与失败摘要单独留痕，不再只依赖应用内 `app.log`/`app_error.log`。
  - 保留原有虚拟环境探测与 `pause` 行为，确保双击启动时也能看清失败原因。
- 验证结果：
  - 已执行：本地关闭 8000 端口占用进程后，确认端口空闲。
  - 已执行：只读复核 `backend/run.bat` 新逻辑，确认端口检查、启动输出落盘和错误摘要写入均已落盘。
  - 备注：当前会话的 Bash 对 Windows bat/PowerShell 复合交互输出兼容性较差，未在本界面完整复现双击窗口表现；建议你本机再次执行 `E:/video_project/proj_ui/project_code/backend/run.bat` 做最终目视确认。

## 启动脚本 PowerShell 转义修复
时间：2026-04-21 21:16:00

- 变更原因：上一版 `run.bat` 把 PowerShell 管道直接写进批处理命令，导致 `cmd` 先行解析 `|` 和重定向符，实际启动时报出 `.venv is not recognized` 与 `| was unexpected at this time`。
- 涉及文件：
  - `backend/run.bat`
  - `operations-log.md`
- 核心改动：
  - 为端口检查命令里的 `|` 补上批处理转义，避免 `for /f` 子命令被 `cmd` 提前拆开。
  - 为 uvicorn 启动输出的 `2>&1 | Tee-Object ...` 补上批处理转义，确保 PowerShell 管道与重定向在运行时按原意执行。
- 验证结果：
  - 已执行：只读复核 `backend/run.bat`，确认批处理层的 `^|` 与 `2^>^&1 ^|` 已正确落盘。
  - 备注：建议你本机再次执行 `E:/video_project/proj_ui/project_code/backend/run.bat`，确认窗口内不再出现批处理语法错误。

## 启动脚本换行符修复（LF 转 CRLF）
时间：2026-04-21 22:10:00

- 变更原因：在 Windows 下执行 `backend/run.bat` 再次出现 `'\.venv"' is not recognized`、`'datetimePORT_INFO' is not recognized`、`'--reload' is not recognized`、`'|' is not recognized`、`'""' is not recognized` 等一串命令无法识别的报错。字节级检查发现 `run.bat` 大小 2385 字节，包含 66 个 LF 换行符但 0 个 CRLF，属于 Unix 风格换行。`cmd.exe` 对批处理文件要求 CRLF，遇到纯 LF 时会把多行命令粘成一条解析，才会把 `%date% %time%` 与 `set "PORT_INFO=..."` 拼成 `datetimePORT_INFO`、把 uvicorn 的 `--reload` 和 PowerShell 的 `|` 当作独立命令。此问题与 21:16:00 修复的 PowerShell 管道转义是两个不同层面：上次是内容层转义，本次是文件格式层换行。
- 涉及文件：
  - `backend/run.bat`：换行符由 66 个 LF 全部转为 CRLF，脚本文字内容未改动。
  - `backend/run.bat.bak`：保留修复前的 LF 版本，作为回退备份。
- 核心改动：
  - 以字节模式读取 `run.bat`，先归一化已有换行为 `\n`，再统一替换为 `\r\n`，保持原 UTF-8 无 BOM 编码不变。
  - 修复后体积 2385 → 2451 字节（66 字节增量即新增的 `\r`），`crlf=66`、`lf_only=0`。
  - 同步保留 `run.bat.bak` 备份，如本次修复引发新问题可用 `copy /y run.bat.bak run.bat` 一键回退。
- 验证结果：
  - 已执行：`python` 字节级校验 `run.bat`，确认 `crlf=66, lf_only=0`，BOM 头 `40 65 63`（`@ec`）即正常的 `@echo off` 开头。
  - 已执行：`Read` 工具重读前 15 行，每一行行号与预期一致，cmd 可按行识别。
  - 未执行：未在本会话实际启动 uvicorn，避免占用 8000 端口和干扰开发；请在本机 `backend` 目录下重新执行 `run.bat` 目视确认启动提示恢复正常。
  - 备注：后续维护此脚本时，请确保编辑器行尾设置为 `CRLF`（VSCode 右下角可切换），不要被跨平台工具改写成 `LF`，否则会再次复现同样错误。

## 启动脚本 PowerShell 转义回退（双引号内误加 `^`）
时间：2026-04-21 22:40:00

- 变更原因：CRLF 修复后 `run.bat` 在启动 PowerShell 时报 `The ampersand (&) character is not allowed ... AmpersandNotAllowed`，错误定位到 `--port 8000 2^>^&1 ^| Tee ...`。根因是 21:16:00 那次修复误把 `^|` 和 `2^>^&1` 放在 `powershell -Command "..."` 的双引号内部。在 cmd 中，双引号内的 `|`、`&`、`>` 本来就不会被 cmd 解释，**不需要** `^` 转义；加了 `^` 反而作为普通字符原样传递给 PowerShell，PowerShell 不识别 `^` 并把 `^&` 当成保留的 `&` 报错。
- 涉及文件：
  - `backend/run.bat`：去掉双引号内部的 3 处 `^`（第 31 行端口探测的 `^|`、第 51 行启动 uvicorn 的 `2^>^&1` 和 `^|`）。
  - `operations-log.md`
- 核心改动：
  - 第 31 行恢复为 `... -ErrorAction SilentlyContinue | Select-Object -First 1`。
  - 第 51 行恢复为 `... --port 8000 2>&1 | Tee-Object -FilePath '%STARTUP_LOG%' -Append; exit $LASTEXITCODE`。
  - Edit 工具在 Windows 上写文件会把 CRLF 规范化为 LF，所以修改后再次用 Python 字节级把换行符统一回 CRLF，最终 `crlf=66, lf_only=0, caret_count=0, size=2447`。
- 验证结果：
  - 已执行：`Read` 重读第 29-53 行，确认第 31、51 行的 PowerShell 命令去掉了 `^`，其他语句未受影响。
  - 已执行：`python` 字节级校验 `run.bat`，确认 CRLF 换行、`^` 数量为 0。
  - 未执行：未在本会话实际启动 uvicorn；请在 `backend` 目录下再次运行 `run.bat` 复验。
  - 备注：如本次修复仍失败，可用 `copy /y run.bat.bak run.bat` 回退到初始 LF 版本（注意回退后需自行按本条记录重新处理 `^`）。

### 教训总结
- cmd 双引号 `"..."` 内部：`|`、`&`、`>`、`<` 都是普通字符，PowerShell 管道/重定向可以直接写，不需要 `^` 转义。
- cmd 双引号外部（裸命令行）：才需要用 `^` 转义 `|`、`&`、`>`、`<`。
- 这两个层面混用会导致 PowerShell 收到字面 `^`，触发保留字符错误。

## 启动脚本重构：拆掉 PowerShell 嵌套，命令分开写
时间：2026-04-21 23:05:00

- 变更原因：上一版 `run.bat` 虽然去掉了 `^` 转义错，但 `powershell -Command "& { & 'python.exe' -m uvicorn ... 2>&1 | Tee-Object ... }"` 这种跨 cmd/PowerShell 嵌套本身就是问题源——uvicorn 把正常日志写到 stderr，被 PowerShell 当作 `NativeCommandError` 打印一大片红字（尽管 uvicorn 实际已经起来了）。用户反馈"服务其实起来了，但报错吓人"，并要求把命令拆开写，不要再纠结长命令转义。
- 涉及文件：
  - `backend/run.bat`：完整重构，移除所有 PowerShell 调用。
  - `operations-log.md`
- 核心改动：
  - 端口检查改为原生 `for /f "tokens=5" %%a in ('netstat -ano ^| findstr /c:":8000 " ^| findstr "LISTENING"') do set "PORT_PID=%%a"`，不再走 `Get-NetTCPConnection`；这里的 `^|` 在 `for /f 'in (\`...\`)'` 的反引号外，是 cmd 正确的管道转义位置。
  - uvicorn 启动改为 cmd 直接调用：`"%PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`，输出自然进控制台，不再 `Tee-Object` 做 stdout/stderr 合并与落盘。
  - `startup.log` 仅保留启动时间戳与命令行一行记录作为留痕，不再尝试 tee uvicorn 的实时输出——保留了"失败时能在 `startup_error.log` 看到退出码和时间"的核心需求。
  - 保留原有虚拟环境双路径探测、端口占用提示、失败 `pause`、退出码透传等基本行为。
- 验证结果：
  - 已执行：字节级校验，`size=1913, crlf=65, lf_only=0, caret=2, powershell_refs=0`。2 个 `^` 均位于 `for /f` 反引号外部的 `netstat ^| findstr` 管道上，属于 cmd 正确转义。
  - 未执行：未在本会话实际启动 uvicorn。请在 `backend` 目录下再次运行 `run.bat` 目视确认：启动过程只有 uvicorn 自己的 `INFO: ...` 行，不再出现 PowerShell 的 `NativeCommandError` / `AmpersandNotAllowed` 红字。
  - 回退方案：`copy /y run.bat.bak run.bat` 可还原到最初版本（带 PowerShell 嵌套）。
- 已放弃的能力：uvicorn 运行时日志不再自动写入 `logs/startup.log`。如需留档，运行时可自行 `run.bat > mylog.log 2>&1`，或在后续需求明确后再引入独立日志方案（如直接给 uvicorn 传 `--log-config`）。

## 2026-04-27 后端启动端口恢复为 8000

- 变更原因：课程封面 URL 指向 8000，当前后端启动脚本仍使用 8001，导致封面资源地址不可访问。
- 涉及文件：`backend/run.bat`。
- 核心改动：将端口占用检查、错误提示、启动日志和 uvicorn 启动参数从 8001 恢复为 8000。
- 验证结果：已检查 `backend/run.bat` 中端口配置均为 8000，且未检出残留 8001；未实际启动后端服务，避免占用本机端口。

## 2026-04-27 个人中心头像上传接口补齐

- 变更原因：个人中心头像上传误走 `/api/v1/upload/file`，该接口按课程封面/资源上传限制为讲师或管理员，导致普通学生更换头像时出现权限错误。
- 涉及文件：
  - `backend/app/config.py`
  - `backend/app/api/v1/uploads.py`
  - `backend/app/services/upload_service.py`
  - `backend/tests/test_uploads.py`
  - `docs/api-endpoint-inventory.md`
  - `operations-log.md`
- 核心改动：
  - 新增 `/api/v1/upload/avatar` 头像上传接口，允许 active 状态的已登录用户上传头像，不再限制角色。
  - 保留 `/api/v1/upload/file` 的讲师/管理员权限限制，继续用于课程封面、文档和常见音视频资源。
  - 上传服务新增头像保存能力，落盘到 `uploads/avatars/`，支持 JPG/PNG/GIF，文件大小限制 10MB。
  - 为头像上传补充学生成功、未登录失败、非 active 用户失败测试，并更新接口清单统计为 81 个业务接口。
- 验证结果：
  - 已执行：`python -m pytest "E:/video_project/proj_ui/project_code/backend/tests/test_uploads.py" -v`
  - 结果：`12 passed, 4 warnings`。
  - 已执行：登录后通过浏览器访问 `http://localhost:3000/profile`，点击“更换头像”上传 PNG 测试图片。
  - 结果：请求链路为 `POST /api/v1/upload/avatar => 200`，随后 `POST /api/v1/users/me => 200`，未再出现课程封面权限错误。
  - 备注：告警为现有 FastAPI `HTTP_422_UNPROCESSABLE_ENTITY` 弃用提示，本次未扩大处理范围；临时测试图片已删除。


## 反馈按课程讲师路由与处理权限优化
时间：2026-04-27

- 变更原因：课程/视频/学习反馈不应只进入管理员反馈管理，需要让负责课程的讲师可见并处理自己课程的反馈，同时保留管理员全局监管。
- 涉及文件：
  - `backend/app/api/v1/feedbacks.py`
  - `backend/app/services/feedback_service.py`
  - `backend/app/schemas/feedback.py`
  - `backend/tests/test_feedbacks.py`
  - `operations-log.md`
- 核心改动：
  - 反馈列表支持按 `Course.teacher_id` 过滤，讲师访问 `/api/v1/feedbacks` 时只返回自己课程的反馈。
  - 反馈详情和处理权限新增课程讲师判断，讲师只能处理自己课程反馈，管理员继续保留全局处理权限。
  - 反馈响应补充 `course_teacher_id`，便于前后端核对课程归属。
  - 补充课程讲师可查看/处理、非负责讲师不可查看/处理的后端测试。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/project_code/backend" && python -m pytest tests/test_feedbacks.py -q`
  - 结果：`12 passed, 7 warnings`，警告为既有 `datetime.utcnow()` 和 `HTTP_422_UNPROCESSABLE_ENTITY` 废弃提示。

## 反馈目标老师字段与处理权限改造
时间：2026-04-27

- 变更原因：课程反馈需要从“按课程负责老师自动分派”调整为“自动关联当前课程，学生手动选择目标老师”，老师侧查看和处理权限也应跟随学生选择的 `target_user_id`。
- 涉及文件：
  - `backend/app/models/feedback.py`
  - `backend/app/core/db_schema.py`
  - `backend/app/schemas/feedback.py`
  - `backend/app/services/feedback_service.py`
  - `backend/app/api/v1/feedbacks.py`
  - `backend/app/schemas/user.py`
  - `backend/app/api/v1/users.py`
  - `backend/tests/test_feedbacks.py`
  - `operations-log.md`
- 核心改动：
  - `Feedback` 模型新增 `target_user_id`，并在数据库兼容检查中为旧库补列。
  - 课程反馈创建时要求同时传入 `course_id` 和 `target_user_id`，后端校验课程存在且目标用户是 active 老师。
  - 反馈列表、详情和处理权限改为按 `Feedback.target_user_id` 判断老师侧可见与可处理范围，管理员或具备 `admin.feedback` 的用户仍保留全局权限。
  - 反馈响应补充 `target_user_id`、`target_username`、`target_nickname`，同时保留 `course_teacher_id` 作为课程归属信息。
  - 新增 `GET /api/v1/users/teachers/options`，登录用户可获取 active 老师简要选项，不暴露邮箱和手机号。
  - 补充测试覆盖目标老师可查看/处理、课程原老师不可越权、无效目标老师被拒绝、老师选项接口和旧库补列。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/project_code/backend" && python -m pytest tests/test_feedbacks.py -q`
  - 结果：`15 passed, 9 warnings`，警告为既有 `datetime.utcnow()` 和 `HTTP_422_UNPROCESSABLE_ENTITY` 废弃提示。

## macOS 本地测试邮箱格式修正
时间：2026-05-07

- 变更原因：测试用户邮箱需要使用更标准的邮箱格式，避免继续使用 `@test.com` 这类不合适的测试域。
- 涉及文件：
  - `backend/scripts/seed_data.py`
  - `backend/tests/utils.py`
  - `docs/test-plan.md`
  - `operations-log.md`
- 核心改动：
  - 将种子测试账号邮箱统一改为 `admin1@example.com`、`teacher1@example.com`、`student1@example.com`、`student2@example.com`。
  - 将测试工具生成的随机邮箱后缀改为 `@example.com`。
  - 同步更新测试计划文档中的测试用户邮箱示例。
  - 已同步更新本机 MySQL `learning_platform.users` 中现有测试账号邮箱。
- 验证结果：
  - 已执行：MySQL 查询确认 4 个测试账号邮箱均为 `example.com` 域。
  - 已执行：`grep -R "@test\\.com" backend/scripts backend/tests docs/test-plan.md`，结果无残留。
  - 已执行：`python -m pytest tests/test_auth.py -v`，结果 `19 passed, 1 failed`；失败用例为既有验证码断言 `test_register_invalid_captcha`，与邮箱格式修改无关。

## 测试账号文档化
时间：2026-05-07

- 变更原因：后续 AI 做 API、前端联调和浏览器测试时需要直接使用固定测试账号，避免反复要求用户手动输入账号密码。
- 涉及文件：
  - `../CLAUDE.md`
  - `CLAUDE.md`
  - `docs/api-testing-guide.md`
  - `operations-log.md`
- 核心改动：
  - 在根级协作说明中新增“联调测试账号”章节，列出管理员、教师、两个学生账号的用户名、密码和邮箱。
  - 在后端协作说明的“测试账号”章节补齐 `student2` 和邮箱列，并明确 AI 测试应直接使用这些账号。
  - 在 API 手动测试指南准备工作中新增测试账号表，方便人工和 AI 测试统一引用。
- 验证结果：
  - 已执行：只读核对三处文档已包含 `admin1`、`teacher1`、`student1`、`student2` 的账号、密码和邮箱。
  - 未执行自动化测试：本次只改文档，不影响运行时代码。

## 新增老师测试账号
时间：2026-05-07

- 变更原因：联调反馈、课程归属和老师侧权限时需要更多老师账号，便于 AI 自动化测试不同老师之间的可见性和越权场景。
- 涉及文件：
  - `backend/scripts/seed_data.py`
  - `../CLAUDE.md`
  - `CLAUDE.md`
  - `docs/api-testing-guide.md`
  - `docs/test-plan.md`
  - `operations-log.md`
- 核心改动：
  - 在种子数据脚本中新增 `teacher2`、`teacher3`、`teacher4`、`teacher5`、`teacher6` 五个 active 老师账号，统一密码 `Test123456`。
  - 同步更新根级协作说明、后端协作说明、API 测试指南和测试计划中的测试账号列表。
  - 已同步写入本机 MySQL `learning_platform.users` 表。
- 验证结果：
  - 已执行：MySQL 查询确认 `teacher1` 到 `teacher6` 共 6 个老师账号均为 `active`。
  - 已执行：调用 `POST /api/v1/auth/login` 验证 `teacher2 / Test123456` 登录成功。

## macOS 开发环境一键启动脚本
时间：2026-05-07

- 变更原因：macOS 开发时需要同时启动 MySQL、Redis、FastAPI 后端和 Vite 前端，手动分多条命令启动不方便，且不希望设置开机启动。
- 涉及文件：
  - `../start-dev-macos.sh`
  - `../README.md`
  - `operations-log.md`
- 核心改动：
  - 新增根目录 `start-dev-macos.sh`，一键手动启动 MySQL 8.4、Redis、后端和前端。
  - 脚本不会调用 `brew services start`，不会设置开机启动；如果服务已存在则复用，退出时只停止本脚本启动的服务。
  - 支持 `./start-dev-macos.sh --status` 查看 3306、6379、8000、3000 当前监听状态。
  - README 补充 macOS 启动脚本的使用方式、访问地址和日志目录。
- 验证结果：
  - 已执行：`bash -n start-dev-macos.sh`，语法检查通过。
  - 已执行：`./start-dev-macos.sh --status`，确认 MySQL、Redis、Backend、Frontend 状态可读。
  - 已执行：`curl http://127.0.0.1:8000/api/v1/health`，返回服务运行正常。
  - 已执行：`curl -I http://127.0.0.1:3000/login`，返回 200。
  - 已执行：`mysqladmin -u root ping` 和 `redis-cli ping`，分别返回 `mysqld is alive` 与 `PONG`。

## 学生到管理员平台反馈闭环检查
时间：2026-05-08

- 变更原因：需要确认学生提交 `system` 平台反馈后，管理员可在消息中心查看、回复并处理，学生可在我的反馈页看到回复与状态。
- 涉及文件：
  - `backend/tests/test_feedbacks.py`
  - `operations-log.md`
- 核心改动：
  - 新增平台反馈闭环后端测试，覆盖 `system` 反馈提交时不传 `course_id`/`target_user_id`、管理员按 `feedback_type=system` 查到反馈、管理员处理写入 `reply`/`replied_at`/`processed_at`、学生通过 `/users/me/feedbacks` 回显已处理状态和回复。
  - 复核现有 schema/service 已允许平台反馈缺省课程和目标用户，仅课程反馈强制校验两项字段。
- 验证结果：
  - 已执行：`python -m pytest --version`
  - 结果：失败，当前环境 Python 缺少 `pytest` 模块（`No module named pytest`），未按用户提示重新安装。
  - 已执行：前端 `npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。

## 管理员用户列表支持按用户 ID 搜索
时间：2026-05-08 19:45:00

- 变更原因：管理员发送站内消息时需要通过用户名或用户 ID 精准定位重名用户，昵称不再作为身份识别字段。
- 涉及文件：
  - `backend/app/services/user_service.py`
  - `operations-log.md`
- 核心改动：
  - 管理员用户列表关键词搜索调整为用户名模糊匹配。
  - 当关键词为纯数字时，同时按 `User.id` 精确匹配，支持在收件人选择中输入用户 ID 查找用户。
  - 不再把昵称作为管理员用户列表关键词匹配条件。
- 验证结果：
  - 已执行：`python3 -m py_compile "/Users/jacob/Developer/a3.learn_platform/learning-platform/project_code/backend/app/services/user_service.py"`。
  - 结果：通过。
