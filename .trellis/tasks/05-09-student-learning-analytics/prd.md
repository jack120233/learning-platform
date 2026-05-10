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
* 已决定：教师课程统计的学生明细采用最小身份信息边界，只显示用户名等必要标识和学习统计字段，不显示邮箱、手机号。
* 已决定：教师课程统计支持导出学生学习明细；课程负责人和被授权教师都可导出自己有权限课程的数据，导出内容仍遵循最小身份信息边界。
* 已决定：管理员平台统计采用“运营分析版”：平台概览 + 趋势图 + 分类/讲师/课程状态/时间范围筛选 + 热门课程与低完成率课程列表。
* 已决定：课程完成规则采用“必学资源完成才算课程完成”。当前项目内容模型没有必学/选学字段，只有 `is_free` 免费试看字段；因此本方案必须补充必学/选学资源设计。
* 已决定：课程一旦首次完成后永久保留完成状态；后续课程新增/调整必学资源不取消学生已完成状态，避免完成状态反复变化。
* 已决定：学习统计采集采用学习会话级，而不是心跳事件级或完整行为事件级；记录每次资源学习的开始、结束、有效时长和完成状态，用于支撑学生/教师/管理员统计。
* 已决定：文档/图片会话防挂机规则按资源类型区分：图片单次最多计 5 分钟；文档无操作 5 分钟停止累计，单次最多计 20 分钟。
* 已决定：后续实现任务按“学习统计底座 + 学生自我统计 + 教师课程统计/管理员平台统计”拆分，而不是按三个页面孤立实现，避免重复改底层数据口径。
* 已决定：统计数据刷新采用混合刷新：学生个人统计可实时/轻量聚合；教师和管理员看板以定时聚合为主；当天数据可实时补充，历史数据走聚合表。
* 已决定：学习统计改造上线时，旧学习行为数据全部清零，学习进度、课程完成状态、学习记录、统计数据都从新方案上线后重新开始；清零范围仅限学习行为数据，不删除用户账号、课程、章节、小节、资源等基础内容；不清理现有课程/资源计数字段（如 `student_count`、`view_count` 等），避免误伤浏览/访问等其他业务统计；这是未来实现阶段的高风险迁移/清理操作，执行前必须再次显式确认。
* 已决定：学生个人统计页仅面向 `student` 角色；教师和管理员可以在数据层保留学习记录，但不提供个人学习统计页，他们只使用教师课程统计或管理员平台统计汇总。
* 已决定：教师课程统计也只统计 `student` 学习者，学习人数、活跃人数、完成率和学生明细都不包含 teacher/admin 学习行为。
* 已决定：学生端不保留老版学习记录页面；个人中心当前学习记录右侧内容区直接替换为新设计的“学习统计”页面，学习记录列表作为新页面的一部分展示；个人中心菜单名称改为“学习统计”。

## Requirements (evolving)

* 统计方案必须明确指标定义、计算口径、权限边界和异常边界。
* 统计方案必须能和现有学习记录/学习进度设计衔接。
* 采用混合方案：现有 `resource_progress` 继续承担“继续学习/当前进度”职责；新增轻量学习事件或会话事实用于学习时长、活跃天数、趋势等统计；必要时增加聚合统计表支撑报表性能。
* 当前任务产出三个设计方案：学生自我统计、教师课程统计、管理员平台统计。
* 当前任务暂不实现代码；三个方案确定后，再创建三个独立实现任务。
* 学习时长采用混合时长口径：视频/音频只计有效播放心跳时长；文档/图片计有效阅读/查看会话时长；页面后台、无操作超时、异常关闭等场景需要有防虚高规则。

## Acceptance Criteria (evolving)

* [x] 明确学生自我统计方案：指标、页面、接口、数据口径、边界。
* [x] 明确教师课程统计方案：指标、页面、接口、数据口径、权限边界。
* [x] 明确管理员平台统计方案：指标、页面、接口、数据口径、权限边界。
* [x] 明确三类统计共用的数据采集、事件/会话、聚合统计底座。
* [x] 明确三个后续实现任务的拆分边界。
* [x] 明确哪些高级分析暂不纳入 MVP。

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
* Replace the existing personal learning records content area with the new learning statistics page; keep the learning-record list as a section within the new page.
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
* 提交失败时进入离线队列，下次恢复网络或进入学习页时补交；离线队列最多保留 7 天，超过 7 天未成功提交的会话丢弃；不向用户弹出“统计保存失败”之类提示，避免打扰学习。
* 后端以 `session_id` 做全局唯一幂等键；同一会话重复提交允许补全更新，但不新增记录、不重复累计。

建议接口：`POST /api/v1/learning/sessions`。

请求体只要求前端传 `resource_id`，以及会话时间、进度和结束原因；`course_id`、`chapter_id`、`section_id`、`resource_type` 由后端根据 `resource_id` 推导，避免前端传错层级关系。当前项目已支持章节级资源：`resources.section_id` 可为空，`resource_progress.section_id` 也有兼容逻辑调整为可空；因此学习会话沿用该设计，章节级资源的 `section_id` 写入 `null`。

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
* `end_reason`：枚举值为 `switch_resource` / `leave_page` / `completed` / `timeout` / `beacon` / `offline_retry` / `manual_stop` / `error`。

### Effective duration rules

* 前端提交本地累计的 `effective_duration_seconds`。
* 后端同时计算外框时长 `ended_at - started_at`，最终有效时长取前端有效时长、外框时长、资源类型上限中的较小值。
* 视频/音频：前端有效时长来自实际播放时长累计，不把暂停时间计入；后端校验不能超过外框时长，也不能明显超过资源总时长。
* 文档：会话有效时长来自打开后的前台停留时间；无操作 5 分钟停止累计；单次会话最多计 20 分钟。
* 图片：会话有效时长来自打开后的前台查看时间；单次会话最多计 5 分钟。
* 页面后台、网络异常、异常关闭：通过结束原因和最终上报进行归档；无法确认的时间不计入或按上限截断。

### Aggregation direction

统计数据刷新采用混合刷新：

* 学生个人统计：允许实时/轻量聚合，保证个人中心反馈及时。
* 教师课程统计：以每日凌晨定时聚合为主；当天数据可从会话事实实时补充，历史数据走聚合表。
* 管理员平台统计：以每日凌晨定时聚合为主；当天数据可实时补充，历史数据走聚合表。

建议由学习会话事实表聚合出：

* 学生每日统计：`user_id + date`。
* 学生课程每日统计：`user_id + course_id + date`。
* 课程每日统计：`course_id + date`。
* 平台每日统计：`date`。

设计口径以会话事实为准；聚合表只作为查询性能优化和趋势查询来源。

### Student daily aggregate

建议新增学生每日统计聚合表，概念名可为 `student_daily_learning_stats`，用于学生个人趋势、总时长、活跃天数、连续学习天数。

核心字段建议：

* `id`
* `user_id`
* `stat_date`
* `effective_duration_seconds`
* `video_duration_seconds`
* `audio_duration_seconds`
* `document_duration_seconds`
* `image_duration_seconds`
* `session_count`
* `learned_course_count`
* `completed_resource_count`
* `created_at`
* `updated_at`

说明：

* 资源类型时长拆分不是学生侧 MVP 必须展示，但成本低，后续可用于学习类型占比。
* `effective_duration_seconds` 应等于各资源类型时长之和。
* `learned_course_count` 按当天产生有效学习会话的去重课程数计算。
* `completed_resource_count` 按当天完成资源数量计算。

### Student-course daily aggregate

建议新增学生课程每日统计聚合表，概念名可为 `student_course_daily_stats`，用于课程内学生学习趋势、教师学生明细、课程维度平均进度和平均学习时长。

核心字段建议：

* `id`
* `user_id`
* `course_id`
* `stat_date`
* `effective_duration_seconds`
* `session_count`
* `completed_resource_count`
* `course_progress_at_day_end`
* `is_course_completed_at_day_end`
* `created_at`
* `updated_at`

说明：

* 学生课程每日统计不拆分资源类型时长，资源类型诊断暂作为后续增强。
* `course_progress_at_day_end` 保存当天结束时课程级进度快照，便于趋势查询。
* `is_course_completed_at_day_end` 用于课程完成趋势和完成率统计。

### Course daily aggregate

建议新增课程每日统计聚合表，概念名可为 `course_daily_learning_stats`，用于教师课程看板、管理员热门课程和低完成率课程列表。

核心字段建议：

* `id`
* `course_id`
* `stat_date`
* `active_student_count`
* `new_started_student_count`
* `new_completed_student_count`
* `cumulative_started_student_count`
* `cumulative_completed_student_count`
* `total_effective_duration_seconds`
* `avg_progress`
* `completion_rate`
* `created_at`
* `updated_at`

说明：

* `active_student_count`：当天有有效学习会话的去重学生数。
* `new_started_student_count`：当天首次开始学习该课程的学生数。
* `new_completed_student_count`：当天首次完成该课程的学生数。
* `completion_rate`：截至当天累计完成率，即 `cumulative_completed_student_count / cumulative_started_student_count`。
* `avg_progress`：截至当天所有已开始学习学生的课程进度均值。

### Platform daily aggregate

建议新增平台每日统计聚合表，概念名可为 `platform_daily_learning_stats`，用于管理员平台运营分析。

核心字段建议：

* `id`
* `stat_date`
* `active_student_count`
* `new_started_course_count`
* `new_completed_course_count`
* `total_effective_duration_seconds`
* `active_course_count`
* `created_at`
* `updated_at`

说明：

* 平台级运营统计只统计 `student` 角色学习者，避免教师/管理员学习或测试行为污染运营指标。
* `active_student_count`：当天有有效学习会话的去重学生数。
* `new_started_course_count`：当天学生首次开始学习课程的次数，按用户-课程计数。
* `new_completed_course_count`：当天学生首次完成课程的次数，按用户-课程计数。
* `total_effective_duration_seconds`：当天学生有效学习时长总和。
* `active_course_count`：当天有学生学习行为的去重课程数。

### Relationship with current progress, statistics, and display records

* `resource_progress` 继续作为当前资源进度快照，用于继续学习、资源完成状态、当前资源进度展示。
* `learning_progress` 正式作为用户-课程级学习汇总表，用于课程级当前进度、最后学习位置、首次完成时间 `completed_at`；课程完成检查由现有 `POST /learning/progress` 触发，在资源进度保存后检查必学资源完成情况，首次完成时写入 `completed_at`。
* `learning_sessions` 作为统计事实来源，用于学习时长、活跃天数、趋势图。
* 会话提交和进度保存保持分离：现有 `POST /learning/progress` 继续负责进度保存；新增 `POST /learning/sessions` 只负责统计事实写入，不顺便更新 `resource_progress`。
* 学习记录列表不直接复用 `learning_progress` 当前状态，新增独立的展示记录表，概念名可为 `learning_record_entries`。
* `learning_record_entries` 采用追加语义：学生删除记录只隐藏该条展示记录；再次学习同一课程时新增一条可见记录，原隐藏记录不改回可见。

### Learning record entries

建议新增学生学习记录展示表，概念名可为 `learning_record_entries`，用于支撑个人学习统计页下方的可删除学习记录列表。

核心字段建议：

* `id`
* `user_id`
* `course_id`
* `last_section_id`
* `last_resource_id`
* `last_learn_at`
* `course_progress_snapshot`
* `course_completed_snapshot`
* `visible`
* `hidden_at`
* `created_at`
* `updated_at`

规则：

* 同一用户同一课程最多存在一条 `visible = true` 的展示记录。
* 首次学习课程时新增一条 `visible = true` 的展示记录。
* 如果已有可见展示记录，再次学习只更新这条记录的 `last_learn_at`、`last_section_id`、`last_resource_id` 等展示定位字段。
* 如果之前的展示记录已被删除隐藏，再次学习同一课程时新增一条新的 `visible = true` 展示记录，旧隐藏记录不改回可见。
* 学生单条/批量删除统一使用同一个删除接口：`POST /api/v1/users/me/learning-records/delete`，入参为 `record_ids[]`；单条删除传一个 id，批量删除传多个 id；后端必须校验所有 `record_ids` 都存在且属于当前登录学生，只要存在不存在或不属于当前学生的 ID，本次删除整体失败，不做部分删除；校验通过后把对应展示记录置为 `visible = false`，并写入 `hidden_at`。
* 已隐藏记录不恢复、不改回可见。
* 查询个人学习记录列表时只返回 `visible = true` 的记录。
* 删除展示记录不影响 `learning_progress`、`resource_progress`、`learning_sessions`、学生统计、教师统计或管理员统计。
* 展示记录列表中的课程进度和完成状态展示当前值：查询时结合 `learning_progress` 返回当前课程进度和当前完成状态，而不是展示记录创建时的快照。

### Idempotency / retry boundaries

* 前端结束会话时应携带全局唯一 `session_id`，避免离线重试或 `sendBeacon` 重复造成重复时长。
* 同一 `session_id` 重复提交时允许补全更新，但不新增记录、不重复累计。
* 可更新字段包括更完整的 `ended_at`、`effective_duration_seconds`、`end_position_seconds`、`progress_percent_at_end`、`is_completed_at_end`、`end_reason`。
* 更新时仍重新应用有效时长校验：最终有效时长取前端有效时长、外框时长、资源类型上限中的较小值。
* 不允许重复提交把已存在会话更新为更早的开始时间、更小的结束位置或明显更差的完成状态。
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
* 课程发布前必须校验至少存在 1 个必学资源；没有必学资源时拒绝发布。
* 课程发布后修改必学/选学会影响完成率统计，需要有提示：修改后课程完成率可能重新计算。

### Course-level progress storage

正式复用/修正现有 `learning_progress` 作为用户-课程级学习汇总表，职责包括：

* 记录用户是否开始学习某课程。
* 保存课程级进度百分比。
* 保存最后学习位置，用于课程级最近学习记录。
* 保存首次课程完成时间 `completed_at`。
* 支撑学生已完成课程数、教师完成率、管理员低完成率课程等统计。

建议关键字段：

* `user_id`
* `course_id`
* `progress`
* `last_section_id`
* `last_resource_id`
* `last_position`
* `started_at` 或 `created_at`
* `last_learn_at` 或 `updated_at`
* `completed_at`

### Completion calculation

* `required_resource_count`：课程下 `is_required = true` 的资源数量。
* `completed_required_resource_count`：该学生已完成的必学资源数量。
* 课程级 `progress` 按必学资源数量等权计算，不按资源时长加权：`course_progress_percent = completed_required_resource_count / required_resource_count * 100`。
* `course_completed = required_resource_count > 0 AND completed_required_resource_count == required_resource_count`。
* 课程完成检查由现有 `POST /learning/progress` 触发：资源进度保存成功后，检查该学生是否已完成课程下所有必学资源。
* 学生首次满足课程完成条件时写入课程完成状态和 `completed_at`。
* 首次完成后永久保留完成状态；后续课程新增/调整必学资源，不取消该学生已完成状态。
* 课程发布前必须至少配置 1 个必学资源；如果课程没有任何必学资源，不允许发布。

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

* 管理员平台统计入口：管理后台侧边栏新增“学习统计”菜单。
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
* 热门课程 Top N：默认按统计窗口内活跃学习人数排序，即近 7/30 天学习过该课程的去重学生数。
* 低完成率课程列表：仅纳入累计开始学习人数不少于 5 的课程，且完成率低于 30%；按完成率升序展示。
* 课程完成率：完成课程人数 / 开始学习课程人数。

### Admin filters

* 时间范围：默认近 7 天，支持切换近 30 天、全部；后续可扩展自定义日期。
* 课程分类：按课程分类过滤。
* 讲师：按课程负责人过滤；后续可扩展协作教师维度。
* 课程状态：published / archived 等。

### Admin permission boundaries

* 仅管理员可查看平台级统计。
* 管理员可查看所有课程的聚合统计和课程级明细统计。
* 管理员平台统计默认以聚合指标为主，不在平台总览页直接暴露学生个人明细。
* 如后续需要管理员查看单个学生学习明细，应进入独立用户管理/学习记录场景，并单独定义审计和权限。

### Edge boundaries

* 低样本课程：累计开始学习人数少于 5 的课程不进入低完成率课程列表，避免样本过小造成误判。
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
* 管理员可在后台课程管理页通过课程操作“统计授权”，把某课程的统计查看权限授权给一个或多个已审核通过且状态正常的教师；授权弹窗教师列表只展示已审核通过且状态正常的 `teacher` 用户，并排除当前课程负责人，因为课程负责人天然拥有统计权限。
* 被授权教师可以查看该课程统计、学生学习明细，并可导出该课程的学生学习明细；但默认不获得编辑课程、删除课程、发布/下架课程权限。
* 若未来要支持助教编辑课程，应另行扩展授权权限，不和本次统计查看权限混在一起。

### Proposed teacher pages

* 教师课程统计入口：仅 `teacher` 角色的右上角头像菜单中新增“课程统计”菜单项，点击进入教师可查看统计的课程列表。
* 教师课程统计列表：展示教师可查看统计的课程，包括自己负责和被授权课程；列表显示权限类型（负责人 / 被授权），让教师清楚课程来源；保留课程级“最近学习时间”，表示该课程最近一次被任意学生学习的时间。
* 单课程统计详情：课程总览指标 + 学生学习明细表。
* 学生明细表筛选：全部、最近未学习、低进度、已完成；“最近未学习”定义为最近 7 天没有学习该课程；“低进度”定义为课程进度低于 30%；默认按课程进度升序排序，让低进度学生优先显示。

### Proposed teacher metrics

* 学习人数：对该课程产生过学习行为的去重 `student` 用户数。
* 近 7/30 天活跃人数：统计窗口内有有效学习时长或学习事件的去重 `student` 用户数。
* 平均课程进度：所有学习该课程学生的课程完成百分比均值。
* 完成率：完成课程的学生数 / 开始学习课程的学生数。
* 平均学习时长：该课程下学生有效学习时长均值。
* 学生明细：最小学生标识（用户名）、课程进度、累计学习时长、最近学习时间、完成状态；不展示邮箱、手机号。

### Teacher permission boundaries

* 教师只能查看自己负责或被授权课程的数据，且统计对象仅包含 `student` 学习者。
* 教师不能通过任意 `course_id` 越权查看未授权课程统计。
* 教师明细中只展示学习统计必要身份字段：用户名等最小标识；不展示邮箱、手机号等联系信息。
* 被授权教师默认只有统计查看和学习明细导出权限，不自动获得课程内容编辑权限。
* 导出格式采用 CSV；需处理中文编码，建议导出 UTF-8 with BOM，避免 Excel 打开中文乱码。
* 导出内容仍遵循最小身份信息边界，不包含邮箱、手机号。
* 管理员授权和撤销需要可追溯，至少记录授权人和时间。

### Edge boundaries

* 授权撤销后，教师立即失去该课程统计访问和后续导出权限；已下载到本地的历史 CSV 文件不做追溯处理。
* 课程归档后，教师仍可查看历史统计，但不能引导学生继续学习。
* 课程删除/硬删除若允许发生，统计需要保留历史最小上下文或显示“课程已删除”。
* 课程负责人变更时，需要决定历史授权是否保留；MVP 建议保留显式授权，`Course.teacher_id` 新负责人自动拥有统计权限。

## Student Self-Statistics Scheme (draft)

### Product scope

学生侧采用“成长反馈版”，目标是把 student 角色的个人中心从单纯的学习记录列表升级为可反馈学习投入和成长趋势的页面。教师和管理员可以保留学习记录数据，但不提供个人学习统计页。

### Proposed page structure

* 顶部统计卡片：总学习时长、近 7 天学习时长、在学课程数、已完成课程数；其中“近 7 天学习时长”固定展示近 7 天，不随趋势图切换到近 30 天而变化。
* 成长反馈卡片：连续学习天数、累计活跃天数。
* 趋势图：默认展示近 7 天每日学习时长趋势，可切换近 30 天。
* 课程进度分布：只展示学习中 / 已完成课程数量或占比，不展示未开始课程。
* 最近学习记录：放在新“学习统计”页面下方，形成先统计概览、后记录明细的布局；默认展示全部记录，保留时间筛选、分页、继续学习入口；分页沿用当前项目默认每页 10 条；学生可删除自己的学习记录，支持单条删除和批量删除；批量删除采用列表复选框勾选模式，顶部显示已选择数量和批量删除操作；删除仅从个人列表隐藏，不影响学习会话事实、个人统计、教师统计或管理员统计；删除后不提供恢复，不做二次确认，点击删除后立即隐藏并提示删除成功；删除后如果学生再次学习同一课程，新增一条可见学习记录，原已隐藏记录保持隐藏状态不被改回；老版独立学习记录内容不保留。

### Metric definitions

* 总学习时长：该学生所有有效学习时长累计，按混合时长口径计算。
* 近 7 天学习时长：统计窗口内每日有效学习时长之和。
* 在学课程数：学生已产生学习进度但未满足课程完成规则的课程数。
* 已完成课程数：学生满足课程完成规则的课程数；课程完成规则需基于必学资源完成比例定义。
* 连续学习天数：从今天或最近一个有学习行为的日期向前连续存在有效学习时长的天数。
* 累计活跃天数：历史上存在有效学习时长的自然日数量。
* 每日学习趋势：按自然日聚合有效学习时长。
* 课程完成进度分布：按课程级完成状态聚合为学习中、已完成；不展示未开始课程。

### Data / API direction

* 数据来源：`resource_progress` 提供当前资源/课程进度；新增学习事件或学习会话事实提供有效学习时长和活跃日期；聚合统计表提供每日汇总。
* 学生统计接口拆分为多个职责清晰的接口：`GET /api/v1/learning/statistics/me/overview` 返回学生统计总览；`GET /api/v1/learning/statistics/me/trend?range=7d|30d` 返回每日学习时长趋势；`GET /api/v1/learning/statistics/me/course-distribution` 返回学习中/已完成课程分布；学习记录列表继续沿用现有 `GET /api/v1/users/me/learning-records` 路径，但底层改造为基于 `learning_record_entries` 返回可见记录。
* 权限边界：只有 `student` 角色可查看自己的个人学习统计；teacher/admin 调用学生统计接口返回 403；不允许通过传 user_id 查看他人数据。

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

## Detailed API Contract (draft)

### Learning session collection API

`POST /api/v1/learning/sessions`

用途：写入一次资源学习会话事实，只负责统计事实，不替代 `POST /api/v1/learning/progress`。

请求字段：

* `session_id: string`，前端生成的全局唯一 UUID，作为幂等键。
* `resource_id: number`，前端唯一需要传入的资源层级标识。
* `started_at: datetime`
* `ended_at: datetime`
* `effective_duration_seconds: number`
* `start_position_seconds?: number`，视频/音频适用。
* `end_position_seconds?: number`，视频/音频适用。
* `progress_percent_at_end?: number`
* `is_completed_at_end?: boolean`
* `end_reason: switch_resource | leave_page | completed | timeout | beacon | offline_retry | manual_stop | error`

后端处理规则：

* 根据 `resource_id` 查询资源，并推导 `course_id`、`chapter_id`、`section_id`、`resource_type`。
* 若资源不存在、资源不属于可学习课程、当前用户无学习权限，则拒绝写入。
* 校验 `ended_at >= started_at`，异常时间直接拒绝或按 0 秒处理；MVP 建议拒绝明显非法入参。
* 有效时长最终取前端有效时长、外框时长、资源类型上限中的较小值。
* 同一 `session_id` 首次提交时插入；重复提交时仅补全同一会话，不重复累计。
* 只有 `student` 学习者进入学生/教师/管理员统计口径；teacher/admin 的会话可以保留在事实表中，但不进入运营统计聚合。

响应：

* 返回统一 `{ code, message, data }`。
* `data` 至少包含 `session_id`、`effective_duration_seconds`、`accepted`。

### Learning progress API relationship

现有 `POST /api/v1/learning/progress` 保持为资源进度保存入口：

* 继续负责 `resource_progress` upsert。
* 继续负责课程继续学习定位。
* 在保存资源进度后触发课程级 `learning_progress` 更新。
* 资源完成后检查必学资源完成情况，首次满足课程完成条件时写入 `learning_progress.completed_at`。
* 同步维护 `learning_record_entries`：若有可见记录则更新展示定位；若没有可见记录则新增可见记录；如果只有隐藏记录则新增可见记录，不恢复隐藏记录。

### Student statistics APIs

`GET /api/v1/learning/statistics/me/overview`

返回学生统计总览：

* `total_duration_seconds`
* `last_7_days_duration_seconds`
* `learning_course_count`
* `completed_course_count`
* `continuous_learning_days`
* `active_learning_days`

权限：仅 `student`；teacher/admin 返回 403。

`GET /api/v1/learning/statistics/me/trend?range=7d|30d`

返回每日学习时长趋势：

* `range`
* `items: [{ date, duration_seconds }]`

规则：默认 `7d`；仅允许 `7d` / `30d`；缺失日期补 0。

`GET /api/v1/learning/statistics/me/course-distribution`

返回课程状态分布：

* `learning_count`
* `completed_count`

规则：只统计已开始学习课程，不展示未开始课程。

`GET /api/v1/users/me/learning-records`

继续沿用现有路径，但底层数据源切换为 `learning_record_entries`：

* 只返回 `visible = true` 的展示记录。
* 默认每页 10 条。
* 默认按 `last_learn_at` 倒序。
* 支持现有时间筛选口径。
* 返回课程当前进度和当前完成状态时，以 `learning_progress` 当前值为准。

`POST /api/v1/users/me/learning-records/delete`

请求：

```json
{
  "record_ids": [1, 2, 3]
}
```

规则：

* 单条删除也使用数组，例如 `{ "record_ids": [1] }`。
* 批量删除传多个 ID。
* `record_ids` 为空或超过后端限制时拒绝；MVP 可限制单次最多 100 条。
* 所有 ID 必须存在、属于当前学生、且当前可见。
* 任意 ID 不存在、不属于当前学生或不可删，本次请求整体失败，不做部分删除。
* 成功后将这些展示记录置为 `visible = false`，写入 `hidden_at`。
* 不影响学习进度、会话事实和任何统计数据。

### Teacher course statistics APIs

`GET /api/v1/teacher/statistics/courses`

返回当前教师可查看统计的课程列表：

* 包含自己负责课程和管理员授权课程。
* 列表字段：课程 ID、课程标题、权限类型（负责人 / 被授权）、学习人数、近 7 天活跃人数、完成率、平均进度、最近学习时间。
* 仅 `teacher` 可访问；admin 使用管理员入口，不复用教师个人菜单接口。

`GET /api/v1/teacher/statistics/courses/{course_id}/overview?range=7d|30d`

返回单课程统计概览：

* `started_student_count`
* `active_student_count`
* `avg_progress`
* `completion_rate`
* `avg_duration_seconds`
* `total_duration_seconds`
* `recent_learn_at`

权限：课程负责人或有效授权教师可访问；其他教师 403。

`GET /api/v1/teacher/statistics/courses/{course_id}/students`

查询学生学习明细：

* 查询参数：`status=all|inactive|low_progress|completed`、`page`、`page_size`、排序参数。
* 默认筛选 `all`，默认按课程进度升序。
* `inactive`：最近 7 天没有学习该课程。
* `low_progress`：课程进度低于 30%。
* 返回字段：学生 ID、用户名、课程进度、累计学习时长、最近学习时间、完成状态；不返回邮箱、手机号、昵称。

`GET /api/v1/teacher/statistics/courses/{course_id}/students/export`

导出 CSV：

* 权限同学生明细接口。
* 导出字段遵循最小身份信息边界。
* CSV 使用 UTF-8 with BOM，避免中文在 Excel 中乱码。
* 授权撤销后不允许继续访问或导出。

### Course statistics authorization APIs

管理员在后台课程管理页维护课程统计授权。

`GET /api/v1/admin/courses/{course_id}/statistics-authorizations`

返回该课程当前统计授权教师列表。

`GET /api/v1/admin/courses/{course_id}/statistics-authorizations/candidates`

返回可授权候选教师：

* 只包含已审核通过、状态正常的 `teacher` 用户。
* 排除当前课程负责人。
* 已授权教师可标记为已授权或直接从候选新增列表中排除。

`POST /api/v1/admin/courses/{course_id}/statistics-authorizations`

请求：

```json
{
  "teacher_ids": [2, 3]
}
```

规则：

* 一个课程可授权多个教师。
* 重复授权同一教师应幂等处理，不创建重复有效授权。
* 授权只赋予课程统计查看、学生明细查看和导出权限，不赋予课程编辑/发布/删除权限。

`DELETE /api/v1/admin/courses/{course_id}/statistics-authorizations/{teacher_id}`

规则：

* 撤销后立即影响后续查看和导出。
* 历史已下载 CSV 不追溯。
* 撤销应保留授权历史信息，例如 `revoked_at`，不建议硬删除授权记录。

### Admin platform statistics APIs

`GET /api/v1/admin/learning-statistics/overview?range=7d|30d|all&category_id=&teacher_id=&course_status=`

返回平台统计总览：

* 总学习人数。
* 统计窗口活跃学习人数。
* 总学习时长。
* 活跃课程数。
* 新开始学习课程次数。
* 新完成课程次数。

`GET /api/v1/admin/learning-statistics/trend?range=7d|30d&metric=duration|active_students|completed_courses`

返回趋势图数据：

* 默认 `range=7d`。
* 可切换 30 天学习时长趋势。
* 缺失日期补 0。

`GET /api/v1/admin/learning-statistics/popular-courses?range=7d|30d|all`

热门课程：

* 默认按活跃学习人数排序。
* 返回课程标题、分类、负责人、活跃学习人数、总学习时长、完成率。

`GET /api/v1/admin/learning-statistics/low-completion-courses?range=7d|30d|all`

低完成率课程：

* 只纳入累计开始学习人数不少于 5 的课程。
* 完成率低于 30%。
* 默认按完成率升序。

## Data Model Details (draft)

### New / formalized tables

`learning_sessions`：学习会话事实表。

关键约束和索引：

* `session_id` 全局唯一。
* 索引：`user_id`、`course_id`、`resource_id`、`started_at`、`course_id + started_at`、`user_id + started_at`。
* 保留 `resource_type` 冗余字段，避免历史资源类型变更影响旧统计。

`learning_progress`：用户-课程当前学习汇总表。

关键约束和索引：

* 唯一约束：`user_id + course_id`。
* 索引：`course_id`、`completed_at`、`last_learn_at`。
* `completed_at` 首次写入后不因必学资源变化而清空。

`learning_record_entries`：学生可见学习记录展示表。

关键约束和索引：

* 业务约束：同一 `user_id + course_id` 最多一条 `visible = true` 记录。
* 如果数据库支持部分唯一索引，使用 `user_id + course_id WHERE visible = true`。
* 如果数据库不支持部分唯一索引，则在服务层事务内校验并加普通索引辅助查询。
* 索引：`user_id + visible + last_learn_at`、`course_id`。

`student_daily_learning_stats`：学生每日聚合。

* 唯一约束：`user_id + stat_date`。
* 用于学生概览、趋势和活跃天数。

`student_course_daily_stats`：学生-课程每日聚合。

* 唯一约束：`user_id + course_id + stat_date`。
* 用于教师学生明细、课程日趋势和平均值计算。

`course_daily_learning_stats`：课程每日聚合。

* 唯一约束：`course_id + stat_date`。
* 用于教师课程统计和管理员课程列表。

`platform_daily_learning_stats`：平台每日聚合。

* 唯一约束：`stat_date`。
* 用于管理员总览和趋势。

`course_teacher_assignments`：课程统计授权关系。

关键约束和索引：

* 字段：`course_id`、`teacher_id`、`permission_type`、`assigned_by`、`assigned_at`、`revoked_at`、`is_active`。
* MVP 的 `permission_type` 可固定为 `statistics_viewer`。
* 唯一有效授权：同一 `course_id + teacher_id + permission_type` 同时最多一条 `is_active = true`。
* 索引：`teacher_id + is_active`、`course_id + is_active`。

### Existing model changes

`resources`：新增 `is_required: boolean NOT NULL DEFAULT true`。

* 旧资源迁移时全部设为 `true`。
* 新建资源默认 `true`。
* 课程发布校验至少存在一个必学资源。

## Aggregation Job Design (draft)

### Daily aggregation

每日凌晨执行聚合任务，建议按自然日重算昨天数据：

* 从 `learning_sessions` 读取有效会话事实。
* 只把 `student` 角色用户纳入学生、教师、管理员统计聚合。
* 重算 `student_daily_learning_stats`。
* 重算 `student_course_daily_stats`。
* 重算 `course_daily_learning_stats`。
* 重算 `platform_daily_learning_stats`。

聚合任务应可重复执行：

* 同一天同一维度用 upsert 覆盖，避免重复累计。
* 如果离线队列补交 7 天内旧会话，后续任务需要能重算受影响日期。
* MVP 可在补交成功后标记受影响日期，或在每日任务中重算最近 7 天，保证离线补交最终进入统计。

### Current-day realtime supplement

教师和管理员看板展示“今天”或包含今天的时间范围时：

* 历史日期读取聚合表。
* 当前日期可从 `learning_sessions` 实时补充。
* 展示层合并历史聚合和当天实时数据，避免等到第二天才看到当天数据。

学生个人统计可直接从聚合表 + 当天会话轻量计算，保证个人反馈及时。

## Frontend Interaction Details (draft)

### Student learning statistics page

* 个人中心菜单“学习统计”替换原“学习记录”。
* 页面顶部先展示统计卡片和趋势，再展示学习记录列表。
* 学习记录列表支持复选框批量模式；单条删除和批量删除都调用同一个 POST 删除接口。
* 删除不做二次确认，成功后当前列表立即移除对应行并提示删除成功。
* 若删除后当前页为空，可自动回退上一页或刷新当前页；MVP 建议刷新当前页并保持分页参数。
* 无数据状态展示引导去课程列表学习。

### Teacher course statistics entry

* 仅 teacher 角色右上角头像菜单展示“课程统计”。
* 进入后先看到可查看统计的课程列表。
* 单课程详情以总览卡片 + 学生明细表为主。
* 表格列较多时移动端允许横向滚动。

### Admin learning statistics entry

* 管理后台侧边栏新增“学习统计”。
* 管理员课程管理页增加“统计授权”操作入口。
* 授权弹窗支持搜索/选择多个教师，列表仅显示可授权教师。

## Migration / Cleanup Strategy (draft)

本方案上线学习统计底座时，用户已确认期望旧学习行为数据从新方案上线后重新开始，但执行前必须再次显式确认。

清理范围：

* 清理旧 `resource_progress` 学习进度数据。
* 清理旧 `learning_progress` 课程学习汇总数据，或重建为新口径空表。
* 清理旧个人学习记录展示数据。
* 清理新统计相关聚合表和会话事实表。

不清理范围：

* 不删除用户账号。
* 不删除课程、章节、小节、资源。
* 不清理课程/资源现有 `student_count`、`view_count` 等通用计数字段。
* 不删除消息、反馈、公告等非学习行为数据。

执行边界：

* 清理脚本必须单独实现，不能藏在普通应用启动兼容逻辑里自动执行。
* 执行前输出将清理的表和行数。
* 执行前需要人工确认。
* 清理后需要重新初始化必要默认字段，例如资源 `is_required = true`。

## Validation Strategy (draft)

### Backend validation

* 学习会话接口测试：正常提交、重复提交幂等、非法资源、非法时间、不同资源类型上限。
* 课程完成测试：必学资源完成后课程完成；选学资源不影响完成；首次完成后不回退。
* 学习记录删除测试：单条数组删除、批量数组删除、非本人 ID 整体失败、部分非法整体失败、删除不影响统计。
* 学生统计权限测试：student 可访问；teacher/admin 访问个人统计返回 403。
* 教师统计权限测试：课程负责人可访问；被授权教师可访问；未授权教师 403；撤销后 403。
* 管理员统计测试：仅 admin 可访问；只统计 student 角色学习行为。
* 导出测试：CSV 字段边界、UTF-8 BOM、中文内容正常。

### Frontend validation

* 学生学习统计页：统计卡片、趋势切换、课程分布、学习记录分页、单条/批量删除。
* 教师课程统计：头像菜单入口、课程列表、课程详情、筛选、导出入口权限。
* 管理员学习统计：侧边栏入口、筛选、热门课程、低完成率课程、统计授权弹窗。
* 移动端：学生页完整适配；教师/admin 表格可横向滚动且不破坏布局。

### Integration validation

* 前后端字段对齐：时间单位统一为秒，日期按自然日，响应结构保持 `{ code, message, data }`。
* 权限联调：不同角色菜单可见性与接口权限一致。
* 当前天数据：聚合表历史数据 + 今日实时数据合并后不重复。
* 中文导出：Excel 打开 CSV 中文不乱码。

## Implementation Readiness Checklist

* [x] 明确学习会话事实表和幂等口径。
* [x] 明确必学/选学资源设计。
* [x] 明确课程完成计算和首次完成保持规则。
* [x] 明确学生统计页面、接口、删除学习记录语义。
* [x] 明确教师课程统计权限、页面、明细、导出和授权模型。
* [x] 明确管理员平台统计指标、筛选、热门/低完成率列表。
* [x] 明确聚合表和每日聚合任务方向。
* [x] 明确迁移/清理边界和高风险确认要求。
* [x] 明确后续实现任务拆分。

## Decision (ADR-lite)

**Context**: 当前项目已有资源学习进度和个人学习记录，但缺少学习时长、活跃趋势、课程完成率、教师课程统计和管理员运营统计。单纯依赖当前进度快照无法准确支撑学习时长和趋势分析；完整事件 BI 又对当前阶段过重。

**Decision**: 采用 Hybrid MVP analytics：保留 `resource_progress` 作为继续学习和当前进度快照；新增学习会话事实用于有效学习时长、活跃天数和趋势；必要时增加每日聚合表支撑教师/管理员看板。课程完成基于必学资源，首次完成后永久保留完成状态。

**Consequences**: 该方案比纯快照复杂，但能支撑三类统计；比完整行为事件轻量，不支持视频热力图、暂停/拖动/回看分析等高级功能。

## Responsive / Mobile Design

* 学生“学习统计”页需要完整移动端适配：统计卡片可换行，趋势图自适应宽度，学习记录列表在小屏下采用卡片化或紧凑布局，避免横向溢出。
* 教师课程统计和管理员学习统计偏后台场景，移动端要求可用即可：统计卡片和筛选区自适应，明细表格允许横向滚动。
* 所有页面仍需保留 PC 端默认体验，移动端通过媒体查询或组件响应式布局适配。

## Out of Scope (final)

* 不做完整 BI 驾驶舱。
* 不做视频热力图、倍速分析、暂停/拖动/回看次数统计。
* 不做学习效果预测、掉队预测、推荐算法。
* 不在本任务中实现代码、数据库迁移、接口或页面。
* 不把教师课程统计授权扩展为课程编辑/发布/删除权限。
