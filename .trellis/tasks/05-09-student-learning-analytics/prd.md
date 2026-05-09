# Student Learning Analytics Design

## Goal

设计在线学习视频播放平台的学生学习记录统计方案，用于从现有“学习记录列表/学习进度保存”能力扩展到可解释、可运营、可用于学生自我反馈和教师/管理员分析的学习统计体系。当前阶段只做多轮设计讨论，不实现代码；后续再评估如何改造现有项目。

## What I already know

* 用户希望先讨论成熟方案、常见指标、权限与数据边界、前后端/数据模型设计方向。
* 当前项目是在线学习视频播放平台，核心资源类型包括视频、音频、文档、图片。
* 现有设计已覆盖“我的学习记录”列表：时间筛选（近 7 天 / 近 30 天 / 全部）、分页、按最近学习时间倒序、继续学习入口。
* 现有学习进度规则：视频/音频播放进度 >= 95% 视为完成，每 30 秒保存；文档/图片打开即完成。
* 现有接口设计包括 `GET /api/v1/users/me/learning-records`、`POST /api/v1/learning/progress`、`GET /api/v1/learning/progress`、继续学习接口等。
* 当前文档没有完整的学习统计分析方案：缺少学习时长汇总、完成率、活跃趋势、课程维度统计、教师/管理员视角、数据口径与边界。

## Assumptions (temporary)

* 学习统计应先服务三类视角：学生自我查看、教师查看自己课程的学习效果、管理员查看平台概况。
* MVP 不一定需要复杂 BI 报表，但需要稳定的数据口径，避免后续统计不可解释。
* 统计设计需要兼顾实时进度和历史事件沉淀，不能只依赖当前进度表。

## Open Questions

* 已决定：采用 Hybrid MVP analytics（现有进度快照 + 轻量学习事件/会话事实 + 聚合统计）的总体技术方向。
* 已决定：当前任务只设计三个方案，不实现代码；三个方案分别是学生自我统计、教师课程统计、管理员平台统计。
* 已决定：三个方案设计完成后，再拆分为三个实现任务。
* 已决定：学习时长采用混合时长口径：视频/音频统计有效播放时长；文档/图片统计有效阅读/查看会话时长，并通过空闲超时和单次上限避免挂机虚高。
* 已决定：学生自我统计采用“成长反馈版”：基础统计卡片 + 连续/活跃学习天数 + 近 7/30 天趋势图 + 课程完成进度分布。
* 已决定：教师课程统计采用“课程 + 学生明细版”：课程总览指标 + 学生学习列表 + 低活跃/低进度/已完成筛选；资源诊断暂作为后续增强。
* 已决定：教师课程统计权限边界为“自己创建/负责的课程 + 管理员授权给自己的课程”。当前项目主要是 `Course.teacher_id` 单一负责人模型，因此本方案必须同时设计课程协作/授权教师能力，不能只预留空概念。
* 已决定：教师课程统计的学生明细采用最小身份信息边界，只显示用户名/昵称等必要标识和学习统计字段，不显示邮箱、手机号。
* 已决定：教师课程统计支持导出学生学习明细；课程负责人和被授权教师都可导出自己有权限课程的数据，导出内容仍遵循最小身份信息边界。
* 已决定：管理员平台统计采用“运营分析版”：平台概览 + 趋势图 + 分类/讲师/课程状态/时间范围筛选 + 热门课程与低完成率课程列表。
* 已决定：课程完成规则采用“必学资源完成才算课程完成”。当前项目内容模型没有必学/选学字段，只有 `is_free` 免费试看字段；因此本方案必须补充必学/选学资源设计。
* 已决定：课程一旦首次完成后永久保留完成状态；后续课程新增/调整必学资源不取消学生已完成状态，避免完成状态反复变化。
* 已决定：学习统计采集采用学习会话级，而不是心跳事件级或完整行为事件级；记录每次资源学习的开始、结束、有效时长和完成状态，用于支撑学生/教师/管理员统计。
* 已决定：文档/图片会话防挂机规则按资源类型区分：图片单次最多计 5 分钟；文档无操作 5 分钟停止累计，单次最多计 20 分钟。
* 已决定：后续实现任务按“学习统计底座 + 学生自我统计 + 教师课程统计/管理员平台统计”拆分，而不是按三个页面孤立实现，避免重复改底层数据口径。
* 已决定：统计数据刷新采用混合刷新：学生个人统计可实时/轻量聚合；教师和管理员看板以定时聚合为主；当天数据可实时补充，历史数据走聚合表。

## Requirements (evolving)

* 统计方案必须明确指标定义、计算口径、权限边界和异常边界。
* 统计方案必须能和现有学习记录/学习进度设计衔接。
* 采用混合方案：现有 `resource_progress` 继续承担“继续学习/当前进度”职责；新增轻量学习事件或会话事实用于学习时长、活跃天数、趋势等统计；必要时增加聚合统计表支撑报表性能。
* 当前任务产出三个设计方案：学生自我统计、教师课程统计、管理员平台统计。
* 当前任务暂不实现代码；三个方案确定后，再创建三个独立实现任务。
* 学习时长采用混合时长口径：视频/音频只计有效播放心跳时长；文档/图片计有效阅读/查看会话时长；页面后台、无操作超时、异常关闭等场景需要有防虚高规则。

## Acceptance Criteria (evolving)

* [ ] 明确学生自我统计方案：指标、页面、接口、数据口径、边界。
* [ ] 明确教师课程统计方案：指标、页面、接口、数据口径、权限边界。
* [ ] 明确管理员平台统计方案：指标、页面、接口、数据口径、权限边界。
* [ ] 明确三类统计共用的数据采集、事件/会话、聚合统计底座。
* [ ] 明确三个后续实现任务的拆分边界。
* [ ] 明确哪些高级分析暂不纳入 MVP。

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky

## Out of Scope (explicit)

* 当前讨论阶段不写代码、不改数据库、不改接口。
* 当前讨论阶段不承诺一次性实现完整 BI、复杂推荐算法、机器学习预测。

## Technical Notes

* Existing docs reviewed earlier in conversation:
  * `project_code/2.需求文档.md` — “我的学习记录功能”、课程统计数据缓存提及。
  * `project_code/3.用户管理模块详情.md` — `GET /api/v1/users/me/learning-records` 接口设计。
  * `project_code/6.学习模块详情.md` — 学习进度保存、继续学习、进度完成规则。
  * `UI/前端需求设计文档.md` — 个人中心“我的学习记录”页面设计。
* Existing design is record/progress oriented, not analytics/reporting oriented.

## Research References

* [`research/lms-learning-analytics-metrics.md`](research/lms-learning-analytics-metrics.md) — 成熟 LMS/在线视频平台常见学习分析指标及学生/教师/管理员视角。
* [`research/learning-analytics-data-modeling.md`](research/learning-analytics-data-modeling.md) — 事件日志、进度快照、聚合统计表、混合模型的取舍，以及和当前 `ResourceProgress`/`LearningProgress` 的映射。

## Research Notes

### What similar tools commonly track

* 学生侧：在学课程数、已完成课程数、课程进度、最近学习、学习时长、活跃天数/连续学习、资源完成情况。
* 教师侧：课程学习人数、活跃学生、完成率、平均进度、平均学习时长、资源热度/完成率、可能掉队学生。
* 管理员侧：平台活跃学习人数、课程热度、内容利用率、开始到完成漏斗、学习趋势、课程/分类/讲师维度统计。

### Current repo constraints

* 当前主数据是 `resource_progress` 这种“最新进度快照”，适合继续学习、当前进度、完成状态，但不适合精确学习时长、回看次数、暂停/拖动次数、视频热力图。
* 当前已有离线重试和 `sendBeacon` 思路，但发送的是进度快照，不是不可变事件。
* 当前归档课程会保留学习记录但禁止继续学习，这和历史统计保留是兼容的。
* `learning_progress` 课程级快照模型存在，但当前活跃逻辑主要使用 `ResourceProgress`，后续可评估是否复用、修正或迁移。

## Follow-up Implementation Task Split (draft)

### Task 1: Learning statistics foundation

Scope:

* Add learning session facts for effective duration and activity statistics.
* Add required/optional resource design via `is_required`.
* Add or formalize course-level completion state with `completed_at` and first-completion persistence.
* Define shared metric calculation services and tests.
* No large dashboard UI beyond what is required to verify the API/contract.

### Task 2: Student self-statistics

Scope:

* Add student-facing overview metrics, growth feedback, trend chart data, and course progress distribution.
* Integrate with existing personal learning records page or adjacent personal center route.
* Use foundation metrics and avoid redefining course completion/time rules.

### Task 3: Teacher course statistics and admin platform statistics

Scope:

* Add course collaborator / teacher authorization model and admin management flow for assigning course statistics access.
* Add teacher course statistics overview, student detail list, filters, and export.
* Add admin platform operational analytics overview, trends, filters, popular courses, and low-completion courses.
* Enforce teacher/admin permission boundaries and export restrictions.

## Shared Learning Statistics Data Foundation (draft)

### Collection granularity

学习统计采用学习会话级采集，不做心跳事件级或完整行为事件级。

### Learning session lifecycle

采用前端本地生成 `session_id`，会话结束时一次性提交：

* 进入资源时，前端生成全局唯一 UUID 作为稳定 `session_id`。
* 学习过程中前端本地累计有效学习时长。
* 资源切换、离开学习页、播放完成、文档/图片关闭、页面关闭时提交会话结果。
* 提交失败时进入离线队列，下次恢复网络或进入学习页时补交。
* 后端以 `session_id` 做全局唯一幂等键，同一会话重复提交不重复累计。

建议接口：`POST /api/v1/learning/sessions`。

### Learning session fact

建议新增学习会话事实表，概念名可为 `learning_sessions`。

核心字段建议：

* `id`
* `user_id`
* `course_id`
* `chapter_id`
* `section_id`，允许为空以兼容章节级资源。
* `resource_id`
* `resource_type`
* `started_at`
* `ended_at`
* `effective_duration_seconds`
* `start_position_seconds`，视频/音频适用。
* `end_position_seconds`，视频/音频适用。
* `progress_percent_at_end`
* `is_completed_at_end`
* `end_reason`：例如 `switch_resource` / `leave_page` / `completed` / `timeout` / `beacon`。

### Effective duration rules

* 视频/音频：会话有效时长来自实际播放时长累计，不把暂停时间计入。
* 文档：会话有效时长来自打开后的前台停留时间；无操作 5 分钟停止累计；单次会话最多计 20 分钟。
* 图片：会话有效时长来自打开后的前台查看时间；单次会话最多计 5 分钟。
* 页面后台、网络异常、异常关闭：通过结束原因和最终上报进行归档；无法确认的时间不计入或按上限截断。

### Aggregation direction

统计数据刷新采用混合刷新：

* 学生个人统计：允许实时/轻量聚合，保证个人中心反馈及时。
* 教师课程统计：以定时聚合为主；当天数据可从会话事实实时补充，历史数据走聚合表。
* 管理员平台统计：以定时聚合为主；当天数据可实时补充，历史数据走聚合表。

建议由学习会话事实表聚合出：

* 学生每日统计：`user_id + date`。
* 学生课程每日统计：`user_id + course_id + date`。
* 课程每日统计：`course_id + date`。
* 平台每日统计：`date`。

设计口径以会话事实为准；聚合表只作为查询性能优化和趋势查询来源。

### Relationship with current progress tables

* `resource_progress` 继续作为当前进度快照，用于继续学习、资源完成状态、当前进度展示。
* `learning_sessions` 作为统计事实来源，用于学习时长、活跃天数、趋势图。
* 课程完成状态需要有课程级记录，例如复用/修正 `learning_progress` 或新增课程学习汇总表，在首次完成时写入 `completed_at`。

### Idempotency / retry boundaries

* 前端结束会话时应携带稳定会话标识，避免离线重试或 `sendBeacon` 重复造成重复时长。
* 同一会话重复提交时应幂等更新，不重复累计。
* 会话结束失败时，可在下次进入或离线队列恢复时补交；补交仍受单次时长上限保护。

## Required / Optional Learning Content Scheme (draft)

### Current repo finding

* 当前 `Chapter`、`Section`、`Resource` 模型存在 `is_free` 字段，含义是免费试看。
* 未发现 `is_required`、`required`、`optional`、必学、选学、必修、选修等课程完成相关设计。
* 因此课程完成规则不能复用 `is_free`，必须新增独立的必学/选学口径。

### Product rule

课程完成采用“必学资源完成”规则：学生完成课程下所有必学资源后，课程记为完成；选学/补充资源不影响课程完成率。

### Recommended data design

建议在 `Resource` 资源层新增必学标记，而不是章节或小节层：

* `is_required: boolean`，默认 `true`。
* 含义：该资源是否计入课程完成规则。
* 默认 `true` 可以保证旧课程在迁移后仍按“全部现有资源必学”工作，不会突然降低课程完成要求。

不建议复用 `is_free`：

* `is_free` 表示是否免费试看，是访问/试看权限口径。
* `is_required` 表示是否计入课程完成，是学习完成口径。
* 两者语义不同，必须分离。

### Teacher/admin content management behavior

* 教师创建或编辑资源时，可设置资源为“必学”或“选学”。
* 默认新资源为必学。
* 管理员如可管理课程内容，也应看到同样字段。
* 课程发布后修改必学/选学会影响完成率统计，需要有提示：修改后课程完成率可能重新计算。

### Completion calculation

* `required_resource_count`：课程下 `is_required = true` 的资源数量。
* `completed_required_resource_count`：该学生已完成的必学资源数量。
* `course_progress_percent = completed_required_resource_count / required_resource_count * 100`。
* `course_completed = required_resource_count > 0 AND completed_required_resource_count == required_resource_count`。
* 学生首次满足课程完成条件时写入课程完成状态和 `completed_at`。
* 首次完成后永久保留完成状态；后续课程新增/调整必学资源，不取消该学生已完成状态。
* 如果课程没有任何必学资源，MVP 建议不允许发布，或在统计中显示“未配置必学资源”。

### Resource completion rule remains unchanged

* 视频/音频：播放进度达到 95% 或显式完成，资源完成。
* 文档/图片：打开后资源完成。
* 资源是否完成与资源是否必学是两个维度：选学资源也可以完成，但不计入课程完成率。

### Analytics impact

* 学生侧“已完成课程数”基于必学资源完成。
* 教师侧“完成率”基于完成所有必学资源的学生数 / 开始学习课程的学生数。
* 管理员侧“低完成率课程”同样基于必学资源完成口径。
* 选学资源可以作为后续资源参与度指标，但不影响课程完成。

### Edge boundaries

* 老课程迁移：所有已有资源默认 `is_required = true`。
* 必学资源被删除：未完成学生按剩余必学资源继续计算；已完成学生保持完成状态。
* 必学资源改为选学：未完成学生可能因此达到完成条件；已完成学生保持完成状态。
* 选学资源改为必学：未完成学生需要完成新增必学资源；已完成学生保持完成状态，不回退为未完成。

## Admin Platform Statistics Scheme (draft)

### Product scope

管理员侧采用“运营分析版”，目标是让管理员从平台、课程、分类、讲师等维度了解整体学习活跃度、课程效果和异常课程。

### Proposed admin pages

* 平台学习统计总览页：展示核心指标卡片、趋势图、热门/低完成课程列表。
* 筛选器：时间范围、课程分类、讲师、课程状态。
* 下钻入口：从热门课程或低完成率课程进入课程详情或教师课程统计视角。

### Proposed admin metrics

* 总学习人数：产生过学习行为的去重用户数。
* 近 7/30 天活跃学习人数：统计窗口内有有效学习时长或学习事件的去重用户数。
* 总学习时长：全平台有效学习时长累计，按混合时长口径计算。
* 每日活跃学习人数趋势：按自然日去重学习用户数。
* 每日学习时长趋势：按自然日聚合有效学习时长。
* 每日课程完成数趋势：按自然日统计新完成课程次数。
* 热门课程 Top N：按学习人数、学习时长或开始学习人数排序，MVP 默认按活跃学习人数排序。
* 低完成率课程列表：开始学习人数达到最小阈值后，按完成率升序展示。
* 课程完成率：完成课程人数 / 开始学习课程人数。

### Admin filters

* 时间范围：近 7 天、近 30 天、全部；后续可扩展自定义日期。
* 课程分类：按课程分类过滤。
* 讲师：按课程负责人过滤；后续可扩展协作教师维度。
* 课程状态：published / archived 等。

### Admin permission boundaries

* 仅管理员可查看平台级统计。
* 管理员可查看所有课程的聚合统计和课程级明细统计。
* 管理员平台统计默认以聚合指标为主，不在平台总览页直接暴露学生个人明细。
* 如后续需要管理员查看单个学生学习明细，应进入独立用户管理/学习记录场景，并单独定义审计和权限。

### Edge boundaries

* 低样本课程：若开始学习人数低于阈值，低完成率排序可能误导；MVP 建议低完成率列表只纳入达到最小开始人数阈值的课程。
* 归档课程：默认可纳入历史统计，可通过课程状态筛选排除。
* 已删除课程：历史统计需保留最小上下文或标记为“课程已删除”。
* 时间范围“全部”在数据量变大后应优先走聚合统计表，不直接扫描原始事件。

## Teacher Course Statistics Scheme (draft)

### Product scope

教师侧采用“课程 + 学生明细版”，目标是让教师能查看自己负责或被授权课程的学习情况，并能定位低活跃、低进度、已完成学生。

### Course permission model

* 当前项目已有 `Course.teacher_id` 单一课程负责人字段。
* 教师可查看统计的课程范围：
  * 自己作为 `Course.teacher_id` 创建/负责的课程。
  * 管理员显式授权给该教师查看/协作管理的课程。
* 需要新增课程授权/协作教师设计，避免“管理员授权课程给教师”成为空概念。

### Course collaborator / authorization design

建议新增课程教师授权关系，概念名可为 `course_teacher_assignments` 或 `course_collaborators`。

核心字段建议：

* `id`
* `course_id`
* `teacher_id`
* `role`：例如 `owner` / `collaborator` / `viewer`，MVP 可先只落 `viewer` 或 `assistant_teacher`。
* `permissions`：MVP 可先不用 JSON，先用明确字段或角色枚举，例如是否允许查看学习统计。
* `assigned_by`：管理员用户 ID。
* `assigned_at`
* `revoked_at` 或 `is_active`

MVP 权限建议：

* 原课程创建者 `Course.teacher_id` 默认拥有课程统计查看权限。
* 管理员可把某课程的统计查看权限授权给另一个已审核通过的教师。
* 被授权教师可以查看该课程统计、学生学习明细，并可导出该课程的学生学习明细；但默认不获得编辑课程、删除课程、发布/下架课程权限。
* 若未来要支持助教编辑课程，应另行扩展授权权限，不和本次统计查看权限混在一起。

### Proposed teacher pages

* 教师课程统计列表：展示教师可查看统计的课程，包括自己负责和被授权课程。
* 单课程统计详情：课程总览指标 + 学生学习明细表。
* 学生明细表筛选：全部、最近未学习、低进度、已完成。

### Proposed teacher metrics

* 学习人数：对该课程产生过学习行为的去重学生数。
* 近 7/30 天活跃人数：统计窗口内有有效学习时长或学习事件的去重学生数。
* 平均课程进度：所有学习该课程学生的课程完成百分比均值。
* 完成率：完成课程的学生数 / 开始学习课程的学生数。
* 平均学习时长：该课程下学生有效学习时长均值。
* 学生明细：最小学生标识（用户名/昵称）、课程进度、累计学习时长、最近学习时间、完成状态；不展示邮箱、手机号。

### Teacher permission boundaries

* 教师只能查看自己负责或被授权课程的数据。
* 教师不能通过任意 `course_id` 越权查看未授权课程统计。
* 教师明细中只展示学习统计必要身份字段：用户名/昵称等最小标识；不展示邮箱、手机号等联系信息。
* 被授权教师默认只有统计查看和学习明细导出权限，不自动获得课程内容编辑权限。
* 导出内容仍遵循最小身份信息边界，不包含邮箱、手机号。
* 管理员授权和撤销需要可追溯，至少记录授权人和时间。

### Edge boundaries

* 授权撤销后，教师立即失去该课程统计访问权限。
* 课程归档后，教师仍可查看历史统计，但不能引导学生继续学习。
* 课程删除/硬删除若允许发生，统计需要保留历史最小上下文或显示“课程已删除”。
* 课程负责人变更时，需要决定历史授权是否保留；MVP 建议保留显式授权，`Course.teacher_id` 新负责人自动拥有统计权限。

## Student Self-Statistics Scheme (draft)

### Product scope

学生侧采用“成长反馈版”，目标是把个人中心从单纯的学习记录列表升级为可反馈学习投入和成长趋势的页面。

### Proposed page structure

* 顶部统计卡片：总学习时长、近 7 天学习时长、在学课程数、已完成课程数。
* 成长反馈卡片：连续学习天数、累计活跃天数。
* 趋势图：近 7/30 天每日学习时长趋势，可切换周期。
* 课程进度分布：未开始/学习中/已完成课程数量或占比。
* 最近学习记录：沿用现有“我的学习记录”列表，保留时间筛选、分页、继续学习入口。

### Metric definitions

* 总学习时长：该学生所有有效学习时长累计，按混合时长口径计算。
* 近 7 天学习时长：统计窗口内每日有效学习时长之和。
* 在学课程数：学生已产生学习进度但未满足课程完成规则的课程数。
* 已完成课程数：学生满足课程完成规则的课程数；课程完成规则需基于必学资源完成比例定义。
* 连续学习天数：从今天或最近一个有学习行为的日期向前连续存在有效学习时长的天数。
* 累计活跃天数：历史上存在有效学习时长的自然日数量。
* 每日学习趋势：按自然日聚合有效学习时长。
* 课程完成进度分布：按课程级完成百分比聚合为未开始、学习中、已完成。

### Data / API direction

* 数据来源：`resource_progress` 提供当前资源/课程进度；新增学习事件或学习会话事实提供有效学习时长和活跃日期；聚合统计表提供每日汇总。
* 建议接口：`GET /api/v1/learning/statistics/me/overview` 返回学生统计总览；`GET /api/v1/learning/statistics/me/trend` 返回趋势；现有 `GET /api/v1/users/me/learning-records` 可保留或扩展。
* 权限边界：只能查看当前登录用户自己的统计，不允许通过传 user_id 查看他人数据。

### Edge boundaries

* 归档课程：继续保留在学习记录和历史统计中，但不能继续学习。
* 删除课程/资源：若业务允许硬删除，统计需要保留历史最小展示信息或标记“课程已删除”。
* 无学习记录：所有数值为 0，趋势为空或补 0，展示引导去学习。
* 当天跨设备学习：按同一用户、同一自然日汇总。

## Detailed Design Discussion Backlog

后续需要继续确认的细节：

* 学习会话生命周期：已决定前端本地生成 `session_id`，资源切换/离开/完成/关闭时一次性提交会话结果；后端按 `session_id` 幂等写入，失败时允许离线补交。
* 学习时长计算：前端累计 vs 后端校验、媒体播放时长与文档/图片停留时长的边界。
* 课程完成状态：课程级记录表、首次完成写入时机、必学资源变化后的处理。
* 聚合统计表：学生日统计、学生课程日统计、课程日统计、平台日统计的字段。
* 学生统计接口与页面：overview/trend/distribution/records 的边界。
* 教师授权模型：授权管理接口、撤销、导出、学生明细筛选。
* 管理员统计接口与页面：筛选项、热门课程、低完成率课程、下钻。
* 验证策略：后端测试、前端类型/页面验证、历史数据迁移。

## Decision (ADR-lite)

**Context**: 当前项目已有资源学习进度和个人学习记录，但缺少学习时长、活跃趋势、课程完成率、教师课程统计和管理员运营统计。单纯依赖当前进度快照无法准确支撑学习时长和趋势分析；完整事件 BI 又对当前阶段过重。

**Decision**: 采用 Hybrid MVP analytics：保留 `resource_progress` 作为继续学习和当前进度快照；新增学习会话事实用于有效学习时长、活跃天数和趋势；必要时增加每日聚合表支撑教师/管理员看板。课程完成基于必学资源，首次完成后永久保留完成状态。

**Consequences**: 该方案比纯快照复杂，但能支撑三类统计；比完整行为事件轻量，不支持视频热力图、暂停/拖动/回看分析等高级功能。

## Out of Scope (final)

* 不做完整 BI 驾驶舱。
* 不做视频热力图、倍速分析、暂停/拖动/回看次数统计。
* 不做学习效果预测、掉队预测、推荐算法。
* 不在本任务中实现代码、数据库迁移、接口或页面。
* 不把教师课程统计授权扩展为课程编辑/发布/删除权限。
