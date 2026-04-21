# UI 操作记录

## 教师端资源上传联调收口与前端留痕约束
时间：2026-04-10

- 变更原因：教师端课程编辑页已经接入课程资料、章节资源、小节资源和分片上传能力，但前端真实校验、接口文档和协作约束还没有完全同步，容易出现“界面提示支持、前端实际拦截”以及“改了 UI 却没有留痕”的问题。
- 涉及文件：
  - `CLAUDE.md`
  - `operations-log.md`
  - `docs/前端接口文档.md`
  - `src/views/teacher/CourseFormPage.vue`
  - `src/views/teacher/components/ResourceManager.vue`
- 核心改动：
  - 在 `UI/CLAUDE.md` 中新增前端硬约束：只要 `UI` 仓库有实际文件变更，必须更新 `UI/operations-log.md`；前端 API 契约、上传流程或开发脚本变化时，必须同步更新前端文档。
  - 新增 `UI/operations-log.md`，作为前端仓库正式留痕入口。
  - 修复教师端资源上传前端校验，补齐 `.mov`、Excel、CSV、Markdown、ZIP、`application/octet-stream` 等当前联调实际需要的格式判断，并在资源列表 props 更新时同步本地视图。
  - 将课程资料上传组件的 `accept` 属性与页面文案统一到当前支持范围。
  - 更新 `docs/前端接口文档.md`，补充章节级资源、课程资料双模式上传、分片上传链路与教师端资源绑定约定。
- 验证结果：
  - 已执行：`npx vue-tsc -b`
  - 结果：通过
  - 已执行：`npm run build`
  - 结果：通过
  - 备注：构建产物提示存在大于 500kB 的 chunk 警告，但不影响本次功能正确性。

## 教师课程管理页角色化批量操作与管理员下架能力
时间：2026-04-13

- 变更原因：教师课程管理页需要补齐上架、下架、删除的批量操作，并支持管理员对全站已发布课程执行单条和批量下架，同时保持编辑仅支持单条。
- 涉及文件：
  - `src/views/teacher/CourseListPage.vue`
  - `src/api/teacher.ts`
  - `operations-log.md`
- 核心改动：
  - 将 `/teacher/courses` 调整为角色化课程管理页，管理员默认查看全站已发布课程，讲师继续查看并管理自己的课程。
  - 新增管理员范围切换、多选表格、批量上架、批量下架、批量删除工具栏，并按角色和课程归属控制单条按钮展示。
  - 前端课程管理接口新增管理列表与批量动作请求模型，统一课程列表字段和批量结果结构。
- 验证结果：
  - 已执行：`npx vue-tsc`
  - 结果：通过
  - 已执行：`npm run build`
  - 结果：通过
  - 备注：构建仍提示大体积 chunk 警告，但不影响本次功能正确性。
## 课程讲师集成、详情页灵动布局与学习页深度交互优化
时间：2026-04-14

- 变更原因：需要集成真实的讲师字段，同时提升课程详情页和学习页的视觉“高级感”与交互效率，解决部分布局遮挡和重复操作提示的问题。
- 涉及文件：
  - `src/views/course/CourseDetailPage.vue`
  - `src/views/learn/LearningPage.vue`
  - `src/views/teacher/CourseFormPage.vue`
  - `src/views/teacher/CourseListPage.vue`
  - `src/components/layout/AppHeader.vue`
  - `src/api/` (teacher.ts, course.ts, learning.ts)
  - `operations-log.md`
- 核心改动：
  * **详情页精细化**：移除冗余 ID 和空标签，讲师信息动态显隐；引入“灵动布局”逻辑，简介行宽随字数动态调整（300/450/600px），垂直间距大幅收缩，提升内容紧凑度。
  * **学习页交互增强**：实现文档/图片资源“点击即完成（100%）”逻辑，保留音视频进度追踪；修复侧边栏 Tab 标题遮挡 Bug；目录页支持点击“小节标题”自动跳转首个资源并联动“当前任务”列表。
  * **管理端体验优化**：下架原因改为可选（支持空输入）；重构“保存并发布”逻辑，支持静默保存和状态预检，消除多重弹窗干扰。
  * **文档预览全能化**：在详情页和学习页同步接入 PDF、PPTX、DOCX 在线预览能力（引入 `@vue-office` 引擎），提升配套资料的阅读体验。
  * **导航精简**：移除 AppHeader 中与 Logo 功能重复的“首页”项。
- 验证结果：
  - 已执行：手动验证各资源类型进度同步正常。
  - 已执行：验证已发布课程编辑保存不再产生多重弹窗。
  - 结果：通过。

## 管理后台反馈管理回复交互补齐
时间：2026-04-20 16:20:01

- 变更原因：管理员在反馈管理页处理课程问题时只有状态修改，没有回复输入和结果展示，处理链路不完整，需要补上“回复并处理”的正确交互。
- 涉及文件：
  - `src/views/admin/FeedbackManagePage.vue`
  - `src/api/admin.ts`
  - `operations-log.md`
- 核心改动：
  - 在反馈管理页新增统一“回复并处理”弹窗，列表入口和详情抽屉入口复用同一套回复表单与提交逻辑。
  - 管理端反馈类型补齐 `reply`、`replied_at` 字段，并将单条处理接口调整为携带 `reply` 请求体。
  - 详情抽屉补充管理员回复与回复时间展示，批量处理切换为已有的批量接口调用。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过

## 反馈页面展示与交互联动优化
时间：2026-04-20 16:48:00

- 变更原因：反馈查看权限已经统一到 `admin.feedback`，前端还需要补齐用户侧回复展示，并让管理端反馈表格的查看详情交互更顺手。
- 涉及文件：
  - `src/views/profile/MyFeedbacksPage.vue`
  - `src/views/admin/FeedbackManagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 用户侧“我的反馈”卡片新增管理员回复区，展示回复内容与回复时间，无回复时不占位。
  - 管理端反馈表格改为点击整行数据区直接打开详情抽屉，去掉操作列里的“详情”按钮。
  - 为截图预览、选择框和“回复并处理”按钮补充事件隔离，并同步收紧操作列宽度与移动端排版。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过
  - 备注：构建仍提示现有大体积 chunk 警告，本次未扩大处理范围。

## 管理后台入口补齐与后台新页面落地
时间：2026-04-20 23:41:56

- 变更原因：后端细粒度后台权限已经补齐，但前端后台仍缺少讲师审核、管理员申请、系统消息、分类管理、标签管理的实际入口，导致有权限码却无法进入对应后台能力。
- 涉及文件：
  - `src/router/index.ts`
  - `src/views/admin/AdminLayout.vue`
  - `src/api/admin.ts`
  - `src/views/admin/UserManagePage.vue`
  - `src/views/admin/TeacherAuditPage.vue`
  - `src/views/admin/AdminApplicationPage.vue`
  - `src/views/admin/AdminMessagePage.vue`
  - `src/views/admin/CategoryManagePage.vue`
  - `src/views/admin/TagManagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 扩展后台默认落地页和子路由，补齐 `admin.teacher_audit`、`admin.admin_application`、`admin.message`、`admin.category`、`admin.tag` 五组后台入口，并保持既有权限守卫模型不变。
  - 扩展 `AdminLayout` 菜单项，让后台导航按权限显示讲师审核、管理员申请、系统消息、分类管理和标签管理。
  - 在 `src/api/admin.ts` 中补齐管理员申请审核、分类管理、标签管理、系统消息发送等类型与接口映射，并把讲师审核提交结构统一为 `approve/comment`。
  - 新增五个后台页面，分别承接讲师审核、管理员申请、系统消息发送、分类管理、标签管理；同时同步修正 `UserManagePage.vue` 中旧的讲师审核提交结构。
  - 修复 `CategoryManagePage.vue` 中父分类下拉的 Element Plus 类型报错，改为通过清空选择表示一级分类，恢复前端构建链路。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 备注：构建仍提示现有大体积 chunk 警告，本次未扩大处理范围。

## 后台最小真实动作联调与公共复用链路回归
时间：2026-04-21 13:13:25

- 变更原因：前一轮已经补齐后台入口和权限口径，但还缺少真实页面动作验证与公共读链路回归，需要确认后台写操作可用，同时不误伤首页和讲师侧的分类、标签读取。
- 涉及文件：
  - `operations-log.md`
  - `src/views/admin/AdminMessagePage.vue`
  - `src/views/admin/CategoryManagePage.vue`
  - `src/views/admin/TagManagePage.vue`
  - `src/views/teacher/CourseFormPage.vue`
  - `src/api/category.ts`
  - `src/api/teacher.ts`
  - `src/store/category.ts`
  - `src/router/index.ts`
  - `src/views/admin/TeacherAuditPage.vue`
  - `src/views/admin/AdminApplicationPage.vue`
- 核心改动：
  - 完成系统消息页最小真实动作验证，向用户 `1` 成功发送一条系统消息，请求命中 `/api/v1/messages/send` 并返回 200。
  - 完成分类管理页最小真实动作验证，成功新增 `联调测试分类 20260421`，请求命中 `/api/v1/categories` 并在后台列表和首页分类筛选中都能看到新增项。
  - 完成标签管理页最小真实动作验证，成功新增 `联调标签 20260421`，请求命中 `/api/v1/tags`，后台标签总数由 14 增加到 15，讲师课程表单标签池同步出现新标签。
  - 回归首页、分类 store 和讲师课程创建页，确认分类读取仍走公共 `/categories`，标签读取仍走公共 `/tags`，后台权限改动没有阻断前台未登录读链路和讲师侧表单加载。
  - 补充联调结论：讲师审核页和管理员申请页当前可进入、接口可返回 200，但本地环境没有待处理数据；后端当前只暴露审核列表与审核动作入口，未在 `app/api/v1/users.py` 中发现对应公开申请路由。
- 验证结果：
  - 已执行：Playwright 真实页面联调
  - 结果：系统消息发送成功，分类新增成功，标签新增成功，首页与讲师课程表单公共读取正常。
  - 已执行：网络请求核对
  - 结果：`POST /api/v1/messages/send`、`POST /api/v1/categories`、`POST /api/v1/tags` 均返回 200；`GET /api/v1/categories?is_enabled=true` 与 `GET /api/v1/tags?page_size=100` 正常返回。
  - 异常说明：讲师审核和管理员申请页面暂无待审核数据，未完成审核提交动作；首页轮播图存在 `via.placeholder.com` 外链资源加载失败，但与本轮后台权限和入口联调无直接关系。

## 标签管理删除交互补完整
时间：2026-04-21 13:48:12

- 变更原因：老师拥有 `admin.tag` 权限时，后台标签页仍缺少单删、批量删和选中交互，需要把标签管理补成完整可操作页面。
- 涉及文件：
  - `src/api/admin.ts`
  - `src/views/admin/TagManagePage.vue`
  - `docs/前端接口文档.md`
  - `operations-log.md`
- 核心改动：
  - 在管理端标签 API 中新增 `deleteAdminTag`、`batchDeleteAdminTags` 和批量删除结果类型。
  - 在标签管理页补齐多选列、批量工具栏、单删按钮、批量删除确认和删除结果提示。
  - 删除完成后统一刷新列表并清空选中状态，部分失败时展示后端返回的失败明细。
  - 更新前端接口文档中的标签管理章节，补齐删除和批量删除接口说明。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围。

## 权限口径简化与角色权限页下线
时间：2026-04-21 16:36:55

- 变更原因：当前权限展示不需要再细化到独立管理员口径，后台也不应继续暴露角色权限配置入口，需要把前端展示主口径收敛为学员和讲师，同时保持既有权限守卫链路可用。
- 涉及文件：
  - `src/router/index.ts`
  - `src/views/admin/AdminLayout.vue`
  - `src/store/user.ts`
  - `src/components/layout/AppHeader.vue`
  - `src/views/teacher/CourseListPage.vue`
  - `operations-log.md`
- 核心改动：
  - 从后台路由和菜单中移除 `角色权限` 页面入口，不再暴露 `/admin/roles`。
  - 收紧后台入口权限集合，移除前端对 `admin.role_permission` 的后台落地依赖。
  - 头部移动端角色文案改为以学员、讲师两类主口径展示，管理员兼容显示为讲师。
  - 课程管理页改为讲师和管理员都可切到 `全站已发布` 视角，讲师也可进入后台管理，同时保持创建、上架、删除等仅在 `我的课程` 视角可操作。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围。

## 后台管理移除讲师审核与管理员申请入口
时间：2026-04-21 17:05:00

- 变更原因：当前后台管理不再需要展示讲师审核和管理员申请，两组入口需要从后台菜单与路由落地中一并移除，避免继续出现在管理端导航里。
- 涉及文件：
  - `src/router/index.ts`
  - `src/views/admin/AdminLayout.vue`
  - `operations-log.md`
- 核心改动：
  - 从后台默认落地页候选中移除 `admin.teacher_audit` 和 `admin.admin_application`，避免 `/admin` 再跳到这两页。
  - 从后台子路由中移除 `/admin/teacher-audits` 和 `/admin/admin-applications`。
  - 从 `AdminLayout` 菜单中移除讲师审核与管理员申请两项展示，并同步清理未使用图标引用。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围。

## 注册页移除管理员选项并统一学生文案
时间：2026-04-21 17:12:00

- 变更原因：注册页当前不再允许管理员自助注册，只保留讲师和学生两种注册入口，同时把前端展示中的“学员”文案统一为“学生”。
- 涉及文件：
  - `src/views/auth/RegisterPage.vue`
  - `src/components/layout/AppHeader.vue`
  - `src/views/teacher/CourseListPage.vue`
  - `src/views/profile/ProfileInfoPage.vue`
  - `src/views/admin/UserManagePage.vue`
  - `src/views/admin/RolePermissionPage.vue`
  - `operations-log.md`
- 核心改动：
  - 注册页角色选择器移除管理员选项，仅保留 `student` 和 `teacher`。
  - 删除管理员推荐邮箱相关表单、校验和提交字段。
  - 将注册页、头部角色标签、课程上下架提示、个人信息页、用户管理页和角色权限页中的“学员”统一改为“学生”。
  - 将注册页中的老师角色展示文案由“讲师”优化为“老师”，并同步更新申请提交提示。
  - 将头部搜索框默认提示从“搜索课程、讲师”改为“搜索课程”，避免注册页出现多余提示。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围。
