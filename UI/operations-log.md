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

## 管理员后台恢复讲师审核入口
时间：2026-04-21 18:08:39

- 变更原因：老师后台入口要继续隐藏，但管理员后台仍需要讲师审核入口和默认落地能力，方便继续处理老师申请。
- 涉及文件：
  - `src/router/index.ts`
  - `src/views/admin/AdminLayout.vue`
  - `operations-log.md`
- 核心改动：
  - 将 `admin.teacher_audit` 重新加入后台默认落地候选，让管理员访问 `/admin` 时可落到讲师审核页。
  - 恢复 `/admin/teacher-audits` 子路由，继续复用 `TeacherAuditPage.vue`。
  - 在 `AdminLayout` 菜单中恢复“讲师审核”入口，并保持菜单继续按权限码过滤展示。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围。

## 2026-04-27 前端开发代理恢复为后端 8000

- 变更原因：后端启动端口恢复为 8000，前端 Vite 开发代理需同步指向同一端口。
- 涉及文件：`vite.config.ts`。
- 核心改动：将 `/api` 代理目标从 `http://localhost:8001` 改回 `http://localhost:8000`。
- 验证结果：已检查 `vite.config.ts` 代理目标为 8000，且未检出残留 8001；未执行前端构建，因为本次仅改开发代理配置。

## 2026-04-27 个人中心头像上传接口切换

- 变更原因：个人中心更换头像误用课程封面/资源上传接口 `/upload/file`，普通学生上传时会收到讲师/管理员权限提示。
- 涉及文件：
  - `src/api/profile.ts`
  - `src/views/profile/ProfileInfoPage.vue`
  - `docs/前端接口文档.md`
  - `operations-log.md`
- 核心改动：
  - 在个人中心 API 中新增 `uploadAvatar(file)`，请求新的 `/upload/avatar` 专用头像上传接口。
  - 将 `ProfileInfoPage.vue` 的更换头像逻辑从 `@/api/learning.uploadFile` 切换为 `uploadAvatar`，避免继续走课程封面上传权限。
  - 将头像文件大小前端校验统一为 10MB，并保留 JPG/PNG/GIF 格式支持。
  - 更新前端接口文档，补充头像上传接口，并标明 `/upload/file` 仅用于讲师/管理员课程封面和资源资料上传。
- 验证结果：
  - 已执行：`npm --prefix "E:/video_project/proj_ui/UI" run build`
  - 结果：通过。
  - 已执行：登录后通过浏览器访问 `http://localhost:3000/profile`，点击“更换头像”上传 PNG 测试图片。
  - 结果：请求链路为 `POST /api/v1/upload/avatar => 200`，随后 `POST /api/v1/users/me => 200`，未再出现课程封面权限错误。
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围；临时测试图片已删除。

## 2026-04-27 个人中心提交反馈入口修复
时间：2026-04-27 14:47:14

- 变更原因：个人中心侧栏“提交反馈”按钮只跳转到 `/profile/feedbacks`，用户已在我的反馈页时点击没有明显反应；该入口应直接提交平台/系统问题反馈。
- 涉及文件：
  - `src/views/profile/ProfileLayout.vue`
  - `src/views/profile/MyFeedbacksPage.vue`
  - `operations-log.md`
- 核心改动：
  - 将个人中心侧栏“提交反馈”按钮改为打开反馈弹窗，复用现有 `FeedbackForm`。
  - 反馈弹窗固定 `default-type="system"` 且锁定类型，确保该入口提交平台/系统问题反馈。
  - 提交成功后关闭弹窗，并在当前位于 `/profile/feedbacks` 时触发列表刷新。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过。
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过。
  - 已执行：浏览器访问 `http://localhost:3000/profile/feedbacks`，点击侧栏“提交反馈”。
  - 结果：弹窗正常打开，反馈类型固定显示为“系统问题”。
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围；未提交真实反馈数据。

## 2026-04-27 反馈截图上传与教师布局动态导入修复
时间：2026-04-27 15:22:10

- 变更原因：个人中心提交反馈弹窗添加图片时复用 `/upload/file`，普通学生会被课程资源上传权限拦截；同时教师端布局动态导入会受 Vite 过期优化依赖影响，报 `Failed to fetch dynamically imported module`。
- 涉及文件：
  - `src/api/learning.ts`
  - `src/components/feedback/FeedbackForm.vue`
  - `src/views/teacher/TeacherLayout.vue`
  - `docs/前端接口文档.md`
  - `operations-log.md`
- 核心改动：
  - 新增前端 `uploadFeedbackImage(file)`，请求 `/upload/feedback-image`。
  - 将反馈表单截图上传从 `/upload/file` 切换到反馈截图专用接口，避免学生提交反馈时命中讲师/管理员资源上传权限。
  - 将 `TeacherLayout.vue` 中的 `el-container/el-aside/el-main` 替换为普通语义结构，保留原布局效果，避免动态加载时再请求失效的 Element Plus container 预构建样式依赖。
  - 更新前端接口文档，补充反馈截图上传接口。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过。
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过。
  - 已执行：浏览器直接动态导入 `/src/views/teacher/TeacherLayout.vue?t=...`。
  - 结果：返回 `{ ok: true, keys: ["default"] }`。
  - 已执行：浏览器访问 `http://localhost:3000/profile/feedbacks`，打开“提交反馈”弹窗并上传 PNG 测试图片。
  - 结果：请求链路为 `POST /api/v1/upload/feedback-image => 200`，不再走 `/upload/file`。
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围；首次上传前后端 8000 未运行导致 502，启动后端后复测通过。

## 2026-04-27 教师课程管理页侧栏精简
时间：2026-04-27 15:50:05

- 变更原因：`/teacher/courses` 页面 PC 端最左侧“讲师工作台”侧栏只有入口和返回按钮，信息价值较低且占用横向空间。
- 涉及文件：
  - `src/views/teacher/TeacherLayout.vue`
  - `operations-log.md`
- 核心改动：
  - 移除教师布局中的侧栏、移动端顶部栏和抽屉菜单，让课程管理页内容区域直接占满可用宽度。
  - 教师布局仅保留主内容出口，不再额外显示“讲师工作台”导航壳。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过。
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过。
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围。

## 2026-04-27 移动端抽屉消息中心菜单对齐修复
时间：2026-04-27 16:00:42

- 变更原因：移动端打开主导航抽屉后，第二行“消息中心”因未读角标组件被推到右侧，导致该行样式与其它菜单项不一致。
- 涉及文件：
  - `src/components/layout/AppHeader.vue`
  - `operations-log.md`
- 核心改动：
  - 调整移动端抽屉中 `mobile-message-badge` 的对齐方式，取消自动右推，让“消息中心”文字紧跟图标显示，未读角标继续贴在文字右上角。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过。
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过。
  - 备注：构建仍提示既有大体积 chunk 警告，本次未扩大处理范围。


## 讲师端课程反馈处理入口补齐
时间：2026-04-27

- 变更原因：课程反馈后端已按课程讲师路由，前端需要提供讲师查看和回复处理自己课程反馈的入口，避免继续只依赖管理员反馈管理页。
- 涉及文件：
  - `src/api/teacher.ts`
  - `src/router/index.ts`
  - `src/views/teacher/CourseListPage.vue`
  - `src/views/teacher/TeacherLayout.vue`
  - `src/views/teacher/FeedbackManagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 讲师 API 增加课程反馈列表、详情、回复处理请求函数和类型。
  - 新增 `/teacher/feedbacks` 路由，并在课程管理页顶部提供“课程反馈”入口，保留讲师页无侧栏布局。
  - 新增课程反馈管理页，支持状态筛选、搜索、详情抽屉、截图预览和“老师回复并处理”。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。

## 反馈目标老师手动选择链路
时间：2026-04-27

- 变更原因：课程反馈不应再自动分派给课程负责老师，而应让学生在当前课程上下文中选择反馈目标老师；个人中心没有课程上下文，因此隐藏直接提交入口，仅保留历史反馈查看。
- 涉及文件：
  - `src/api/learning.ts`
  - `src/api/profile.ts`
  - `src/api/admin.ts`
  - `src/api/teacher.ts`
  - `src/components/feedback/FeedbackForm.vue`
  - `src/views/course/CourseDetailPage.vue`
  - `src/views/profile/ProfileLayout.vue`
  - `src/views/profile/MyFeedbacksPage.vue`
  - `src/views/teacher/FeedbackManagePage.vue`
  - `src/views/admin/FeedbackManagePage.vue`
  - `docs/前端接口文档.md`
  - `operations-log.md`
- 核心改动：
  - 反馈表单在课程反馈场景新增“反馈给老师”下拉，默认当前课程老师，可切换其他 active 老师。
  - 课程详情页向反馈表单传入当前课程名称、课程老师 ID 和老师名称，提交时携带 `course_id` 与 `target_user_id`。
  - 个人中心移除直接提交反馈弹窗入口，保留“我的反馈”列表和处理回复展示。
  - 我的反馈、老师反馈管理、管理员反馈管理均补充目标老师字段展示，回复文案从固定管理员口径改为处理回复口径。
  - 前端接口文档补充 `target_user_id`、`/users/teachers/options` 和老师侧按目标老师处理的约定。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过。
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：浏览器访问 `http://localhost:3000/profile`。
  - 结果：个人中心侧栏不再显示“提交反馈”入口，仅保留“我的反馈”。
  - 已执行：浏览器从首页进入真实课程 `http://localhost:3000/courses/25` 并打开“反馈”标签页。
  - 结果：反馈类型锁定为“课程问题”，关联课程自动显示当前课程，老师下拉默认“张老师”并可展开。
  - 已执行：拦截 `POST /api/v1/feedbacks` 做提交 payload 验证。
  - 结果：请求体包含 `feedback_type: course`、`course_id: 25`、`target_user_id: 2` 和反馈内容；拦截返回模拟成功，未向后端写入真实反馈数据。

## 首页未登录按钮样式优化
时间：2026-04-27

- 变更原因：首页头部未登录状态下“登录”和“注册”按钮展示不够协调，需要提升按钮层次、间距和移动端抽屉里的视觉一致性。
- 涉及文件：
  - `src/components/layout/AppHeader.vue`
  - `operations-log.md`
- 核心改动：
  - 将 PC 端未登录按钮改为胶囊式组合按钮，登录为轻量按钮，注册为渐变主按钮。
  - 调整按钮高度、圆角、字重、间距、hover/focus 状态和阴影，让两个入口在首页头部更清晰。
  - 同步优化移动端抽屉底部未登录按钮样式，保持和 PC 端同一视觉口径。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npx vue-tsc --noEmit`
  - 结果：通过。
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：浏览器临时清空登录态访问 `http://localhost:3000/?sort_by=latest&page=1`，验证后恢复原登录态。
  - 结果：头部显示“登录 / 注册”胶囊式组合按钮，登录按钮与注册渐变主按钮样式均生效。

## Batch 1 Soft Blue 反馈与课程详情操作区改造
时间：2026-04-29

- 变更原因：用户认可首页登录/注册的 Soft Blue Action Surfaces 风格，需要按 UI 改进计划先改造反馈与课程详情链路中的主要操作区，统一主次按钮层级和视觉口径。
- 涉及文件：
  - `src/assets/styles/main.scss`
  - `src/views/course/CourseDetailPage.vue`
  - `src/components/feedback/FeedbackForm.vue`
  - `src/views/teacher/FeedbackManagePage.vue`
  - `src/views/admin/FeedbackManagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 新增全局 `.soft-action-surface`、`.soft-action-btn`、尺寸和主次按钮修饰类，沉淀浅蓝操作面与蓝色渐变主按钮工具样式。
  - 将课程详情页顶部学习 CTA、课程资料下载/预览操作区替换为 Soft Blue 胶囊式按钮组。
  - 将反馈表单提交/取消区域改为 Soft Blue 操作面，兼容内联和弹窗模式。
  - 将讲师端、管理员端反馈管理页的搜索/重置、详情抽屉处理按钮、处理弹窗 footer 操作区统一到 Soft Blue 风格。
  - 为小屏补充操作区纵向布局，避免胶囊按钮组在窄屏横向溢出。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：浏览器访问 `http://localhost:3000/courses/25` 并打开“反馈”标签页。
  - 结果：课程详情顶部“开始学习”和反馈表单“提交反馈”均已挂载 Soft Blue 操作面与主按钮样式。
  - 已执行：浏览器访问 `http://localhost:3000/teacher/feedbacks`。
  - 结果：讲师端反馈管理页搜索/重置按钮组已挂载 Soft Blue 操作面样式；当前本地无反馈数据，未触发详情抽屉和处理弹窗。
  - 已执行：浏览器切换管理员账号访问 `http://localhost:3000/admin/feedbacks`。
  - 结果：管理员端反馈管理页搜索/重置按钮组已挂载 Soft Blue 操作面样式。
  - 已执行：将浏览器视口调整为 390px 宽检查管理页布局。
  - 结果：`documentElement.scrollWidth <= innerWidth`，未出现横向溢出。

## Batch 2 Soft Blue 个人中心与认证页改造
时间：2026-04-29

- 变更原因：继续执行项目 UI 改进计划第二批，让未登录入口页和个人资料页与首页登录/注册、反馈链路的 Soft Blue Action Surfaces 风格保持一致。
- 涉及文件：
  - `src/views/auth/LoginPage.vue`
  - `src/views/auth/RegisterPage.vue`
  - `src/views/auth/ForgotPasswordPage.vue`
  - `src/views/profile/ProfileInfoPage.vue`
  - `operations-log.md`
- 核心改动：
  - 登录页主提交按钮改为浅蓝操作面 + 渐变蓝主 CTA。
  - 注册页主提交按钮、邮箱验证码按钮和老师申请提示弹窗确认按钮统一为 Soft Blue 主次层级。
  - 找回密码页下一步、上一步、确认重置、重新发送验证码和成功页“去登录”统一为 Soft Blue 操作面和胶囊按钮。
  - 个人资料页头像区域改为浅蓝卡片式操作面，补充头像说明文案，并将“更换头像”“发送验证码”“保存修改”统一到 Soft Blue 风格。
  - 为个人资料页小屏补充头像区域、邮箱验证码输入组和保存按钮的纵向布局，减少窄屏溢出风险。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：静态核对 `LoginPage.vue`、`RegisterPage.vue`、`ForgotPasswordPage.vue`、`ProfileInfoPage.vue` 的目标按钮与操作区。
  - 结果：目标页面均已挂载 `.soft-action-surface`、`.soft-action-surface--card` 或 `.soft-action-btn` 相关样式类。
  - 已执行：Playwright 重新启动后访问 `http://localhost:3000/login`。
  - 结果：登录页主提交按钮已挂载 Soft Blue 操作面，页面无横向溢出。
  - 已执行：Playwright 访问 `http://localhost:3000/register`。
  - 结果：注册页主按钮和发送验证码按钮已挂载 Soft Blue 样式，页面无横向溢出。
  - 已执行：Playwright 访问 `http://localhost:3000/forgot-password`。
  - 结果：找回密码页下一步、上一步/下一步、上一步/确认重置、去登录操作区均已挂载 Soft Blue 样式，页面无横向溢出。
  - 已执行：登录学生测试账号后访问 `http://localhost:3000/profile`。
  - 结果：个人资料页头像卡片、更换头像和保存修改按钮已挂载 Soft Blue 样式。
  - 已执行：将个人资料页视口调整为 390px 宽检查布局。
  - 结果：`documentElement.scrollWidth <= innerWidth`，未出现横向溢出。

## Batch 3 Soft Blue 讲师与管理员列表页操作区改造
时间：2026-04-29

- 变更原因：继续执行项目 UI 改进计划第三批，统一讲师课程列表和管理员列表页中的页面头部、筛选栏、批量操作条与弹窗底部操作区，同时保持表格行内操作紧凑。
- 涉及文件：
  - `src/views/teacher/CourseListPage.vue`
  - `src/views/admin/CategoryManagePage.vue`
  - `src/views/admin/TagManagePage.vue`
  - `src/views/admin/AnnouncementPage.vue`
  - `src/views/admin/UserManagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 讲师课程列表页头部“课程反馈 / 创建课程”、筛选栏“搜索 / 重置”和批量操作条统一为 Soft Blue 操作面。
  - 分类管理、标签管理、公告管理页的新增按钮统一为渐变主 CTA，弹窗 footer 统一为 Soft Blue 主次按钮组。
  - 标签管理页批量删除条改为浅蓝卡片式操作面，筛选按钮组改为 Soft Blue 风格。
  - 用户管理页筛选按钮组和讲师审核弹窗 footer 统一为 Soft Blue 风格。
  - 保留表格行内编辑、删除、启用、禁用等 text button，不扩大表格操作密度。
  - 为改造页面补充小屏下操作区纵向布局，避免窄屏横向溢出。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：登录管理员测试账号后访问 `http://localhost:3000/teacher/courses`。
  - 结果：课程管理页头部操作区和筛选按钮组已挂载 Soft Blue 样式，页面无横向溢出。
  - 已执行：访问 `http://localhost:3000/admin/categories`。
  - 结果：分类管理页新增分类按钮已挂载 Soft Blue 样式，页面无横向溢出。
  - 已执行：访问 `http://localhost:3000/admin/tags`。
  - 结果：标签管理页新增标签和搜索/重置按钮组已挂载 Soft Blue 样式，页面无横向溢出。
  - 已执行：访问 `http://localhost:3000/admin/announcements`。
  - 结果：公告管理页新增公告和搜索/重置按钮组已挂载 Soft Blue 样式，页面无横向溢出。
  - 已执行：访问 `http://localhost:3000/admin/users`。
  - 结果：用户管理页搜索/重置按钮组已挂载 Soft Blue 样式，页面无横向溢出。
  - 已执行：将用户管理页视口调整为 390px 宽检查布局。
  - 结果：`documentElement.scrollWidth <= innerWidth`，未出现横向溢出。

## Batch 4 Soft Blue 首页卡片与学习页局部增强
时间：2026-04-29

- 变更原因：继续执行项目 UI 改进计划第四批，将首页课程卡片和学习页少量 CTA 与前几批 Soft Blue Action Surfaces 风格对齐，同时避免破坏学习页沉浸式布局。
- 涉及文件：
  - `src/components/common/CourseCard.vue`
  - `src/views/home/components/CourseListSection.vue`
  - `src/views/learn/LearningPage.vue`
  - `operations-log.md`
- 核心改动：
  - 首页课程卡片改为浅蓝描边、柔和蓝色投影、封面渐变高光和底部蓝色强调线，hover 时保持轻量上浮反馈。
  - 课程卡片讲师信息改为浅蓝胶囊标签，并补充 hover 显示的“查看课程”轻 CTA。
  - 首页课程列表错误重试按钮统一为 Soft Blue 操作面与渐变主按钮。
  - 学习页仅局部改造资源加载错误“重试”、暂不支持预览“下载文档”和自动跳转“取消”按钮，不调整播放器、目录和沉浸式主体结构。
  - 为学习页局部 CTA 补充小屏宽度适配，避免窄屏按钮溢出。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：浏览器访问 `http://localhost:3000/?sort_by=latest&page=1`。
  - 结果：首页课程卡片已挂载浅蓝描边、教师胶囊和 hover 入口提示，页面无横向溢出。
  - 已执行：将首页视口调整为 390px 宽检查布局。
  - 结果：`documentElement.scrollWidth <= innerWidth`，课程卡片无横向溢出。
  - 已执行：静态核对 `LearningPage.vue`。
  - 结果：资源加载错误“重试”、暂不支持预览“下载文档”和自动跳转“取消”按钮均已挂载 Soft Blue 操作面与按钮样式。
  - 备注：当前本地真实课程进入 `/learn/:courseId` 时因课程无可学习资源或业务数据不足被重定向回首页，未完成学习页真实资源场景浏览器验证；首页轮播图仍存在 `via.placeholder.com` 外链加载失败，属于既有环境问题。

## 首页品牌与筛选字体 Soft Blue 统一
时间：2026-04-29

- 变更原因：首页头部“职业培训课堂”、Banner 标题、筛选栏“分类 / 排序”和筛选选项仍保留旧字体层级，与已完成的 Soft Blue 按钮和卡片风格不统一，需要补齐同类字体与筛选胶囊样式。
- 涉及文件：
  - `src/components/layout/AppHeader.vue`
  - `src/views/home/components/BannerCarousel.vue`
  - `src/views/home/components/SearchFilterBar.vue`
  - `src/views/home/components/CourseListSection.vue`
  - `src/views/home/components/PaginationBar.vue`
  - `operations-log.md`
- 核心改动：
  - 头部品牌字改为更高字重、深蓝灰文字和蓝色渐变下划线强调，移动端抽屉品牌同步加粗。
  - 首页筛选栏改为浅蓝卡片面，`分类`、`排序` 标签加粗并提升字距，分类/排序选项改为蓝色胶囊，选中态为渐变主按钮风格。
  - Banner 标题改为半透明蓝色胶囊标题，提升与 Soft Blue 主风格的一致性。
  - 首页空/错误状态文字和移动端分页辅助文字改为统一的深蓝灰加粗层级。
  - 分页容器补充浅蓝描边、柔和投影和圆角，与首页课程卡片、筛选栏保持同一视觉口径。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：浏览器访问 `http://localhost:3000/?sort_by=latest&page=1`。
  - 结果：头部“职业培训课堂”、Banner 标题、`分类 / 排序` 标签和筛选选项均已应用加粗字体层级、蓝色胶囊或渐变选中态，页面无横向溢出。
  - 已执行：将首页视口调整为 390px 宽检查布局。
  - 结果：`documentElement.scrollWidth <= innerWidth`，筛选胶囊正常换行，无横向溢出。
  - 备注：首页轮播图仍存在 `via.placeholder.com` 外链加载失败，属于既有环境问题。

## Soft Blue 收尾移动端溢出修复
时间：2026-04-30

- 变更原因：执行 `/trellis:finish-work` 浏览器复测时，发现首页在 390px 移动端视口下存在轻微横向溢出，需要补齐收尾修复。
- 涉及文件：
  - `src/components/layout/AppHeader.vue`
  - `src/views/home/components/BannerCarousel.vue`
  - `operations-log.md`
- 核心改动：
  - 在 480px 以下隐藏头部搜索框，避免未登录按钮组与搜索框共同挤压导致头部宽度溢出。
  - 为首页轮播容器增加 `overflow: hidden`，避免 Element Plus 相邻轮播项参与页面横向滚动宽度计算。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 已执行：浏览器访问 `http://127.0.0.1:3002/` 并在 390px 视口核对首页布局。
  - 结果：`documentElement.scrollWidth <= innerWidth`，未出现横向溢出；Soft Blue 相关元素仍正常挂载。
  - 备注：首页轮播图仍存在 `via.placeholder.com` 外链加载失败，属于既有环境问题。

## 课程详情反馈区域展示优化
时间：2026-05-06 17:35:35

- 变更原因：课程详情页“反馈”标签页只显示左侧窄表单，右侧出现大片空白；锁定的“反馈类型”字段只有短文本却占满整行，视觉上显得突兀。
- 涉及文件：
  - `src/views/course/CourseDetailPage.vue`
  - `src/components/feedback/FeedbackForm.vue`
  - `operations-log.md`
- 核心改动：
  - 将课程详情反馈标签页改为左侧反馈表单、右侧提交说明的双卡片布局，用课程标题、反馈对象和提交提示承接原来的右侧空白。
  - 为反馈区域补充标题、说明文案、浅蓝描边、柔和阴影和移动端单列布局，保持 Soft Blue 视觉口径。
  - 将锁定状态的反馈类型从整行只读块改为紧凑胶囊展示，并增加“已根据当前页面自动选择”的辅助说明。
- 验证结果：
  - 已执行：`cd "E:/video_project/proj_ui/UI" && npm run build`，构建通过。
  - 已执行：使用学生种子账号登录后访问 `http://localhost:3000/courses/29`，打开“反馈”标签页核对 PC 视口；反馈区显示左侧表单、右侧提交说明卡片，原右侧空白被承接。
  - 已执行：在 390px 移动端视口核对反馈标签页；反馈表单和说明卡片按单列堆叠，未见明显横向溢出。
  - 已检查：控制台仅有登录前未授权请求和首页外链占位图加载失败，未发现本次反馈区域改动引入的新错误。
  - 2026-05-07 11:12 追加调整：按页面文案要求将主标题改为“课程内容错误反馈”、提交说明标题改为“反馈将由教师处理”、更新三条提交说明文案，并将左侧“反馈给老师”改为“反馈对象”。
  - 2026-05-07 11:12 追加调整：反馈表单新增 `teacherChange` 事件，右侧卡片“反馈对象”会随左侧下拉选择同步更新。
  - 追加验证：已执行 `cd "E:/video_project/proj_ui/UI" && npm run build`，构建通过；已在 `http://localhost:3001/courses/29` 打开反馈标签页，确认文案生效，并将左侧反馈对象从“张老师”切换为“tset1”，右侧卡片同步更新为“tset1”。

## 讲师与管理员学习统计页面补齐
时间：2026-05-10

- 变更原因：需要落地学生学习分析中的讲师课程统计、管理员平台学习统计，并将课程统计授权 UI 放到管理员课程管理，确保被授权老师只能查看、明细和导出统计，不获得课程编辑类权限。
- 涉及文件：
  - `src/api/index.ts`
  - `src/api/teacher.ts`
  - `src/api/admin.ts`
  - `src/router/index.ts`
  - `src/components/layout/AppHeader.vue`
  - `src/views/admin/AdminLayout.vue`
  - `src/views/admin/LearningStatisticsPage.vue`
  - `src/views/admin/CourseManagePage.vue`
  - `src/views/teacher/CourseStatisticsPage.vue`
  - `src/views/teacher/CourseStatisticsDetailPage.vue`
  - `docs/前端接口文档.md`
  - `operations-log.md`
- 核心改动：
  - 新增讲师“课程统计”入口、课程统计列表页和课程统计详情页，支持负责人/被授权课程查看、概览指标、学生明细筛选和 CSV 导出。
  - 新增管理员“学习统计”页，支持时间范围、分类、课程老师、课程状态筛选，并展示平台概览、趋势、热门课程和低完成率课程。
  - 新增管理员“课程管理”统计授权抽屉，支持查看授权、搜索候选老师、批量授权和撤销授权；授权身份展示使用 `username#teacher_id`，不使用昵称。
  - 扩展前端 API 类型和请求函数，接入讲师统计、管理端学习统计、课程统计授权接口，并让 Axios 对 `responseType: 'blob'` 的 CSV 导出直接返回原始 Blob。
  - 更新前端接口文档，补充讲师统计、管理员学习统计、课程统计授权和 CSV Blob 导出约定。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/.claude/worktrees/agent-a8083faf62fda9abc/UI" run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。
  - 未执行：浏览器真实联调未执行，当前仅完成构建级验证。

## 课程统计授权权限边界自检修复
时间：2026-05-10 08:58 CST

- 变更原因：后端已收紧“全站已发布”课程下架权限为管理员或课程负责人，前端课程管理按钮展示需同步，避免普通老师在全站已发布视图看到不可执行的下架入口。
- 涉及文件：
  - `src/views/teacher/CourseListPage.vue`
  - `operations-log.md`
- 核心改动：
  - 将课程下架按钮显示条件调整为：管理员在全站已发布视图可下架，课程负责人可下架自己的已发布课程；普通老师不再因位于全站已发布视图而看到他人课程下架入口。
- 验证结果：
  - 已执行：`cd "/Users/jacob/Developer/a3.learn_platform/learning-platform/.claude/worktrees/agent-a8083faf62fda9abc/UI" && npm run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。
  - 未执行：浏览器真实联调未执行，当前仅完成构建级验证。


## 教师/管理员学习统计真实浏览器联调
时间：2026-05-10 09:14

- 变更原因：完成 teacher/admin learning statistics 后，按真实浏览器执行管理员授权与教师查看统计的完整业务流程，确认前后端接口、路由、权限和导出链路可用。
- 涉及文件：
  - `src/views/admin/CourseManagePage.vue`
  - `src/views/admin/LearningStatisticsPage.vue`
  - `src/views/teacher/CourseStatisticsPage.vue`
  - `src/views/teacher/CourseStatisticsDetailPage.vue`
  - `src/api/admin.ts`
  - `src/api/teacher.ts`
  - `operations-log.md`
- 核心改动：
  - 本次仅追加联调验证记录；未修改页面业务逻辑。
  - 使用 Playwright 真实浏览器验证：管理员 `admin1@example.com` 登录后进入 `/admin/courses`，对课程 `FastAPI实战` 执行“统计授权”；教师 `teacher6@example.com` 登录后进入 `/teacher/statistics` 查看被授权课程、进入 `/teacher/statistics/courses/2` 查看学生明细并导出 CSV；管理员移动端视口访问 `/admin/learning-statistics`。
  - 追加验证授权撤销：管理员撤销 `teacher6#9` 后，教师再次访问课程统计详情展示无权限提示。
- 验证结果：
  - 已执行：真实浏览器业务流（Playwright，PC 1440x1000 + 移动端 390x844）。
  - 结果：通过。课程统计授权成功，教师可查看被授权课程统计详情，CSV 下载文件 `course-2-students.csv` 包含 UTF-8 BOM，管理员学习统计移动端页面可打开。
  - 已执行：撤销授权后教师访问 `/teacher/statistics/courses/2`。
  - 结果：通过，页面显示“无法加载课程统计，请确认你仍有访问权限”。


## 教师访问学生个人学习统计入口权限修正
时间：2026-05-10 09:30

- 变更原因：真实浏览器联调发现教师角色可打开 `/profile/records` 学生个人学习统计页面；后端学生统计接口已返回 403，但前端仍展示学生统计 UI，容易混淆教师端“课程统计”和学生端“我的学习”。
- 涉及文件：
  - `src/router/index.ts`
  - `src/store/user.ts`
  - `src/views/profile/ProfileLayout.vue`
  - `src/components/layout/AppHeader.vue`
  - `operations-log.md`
- 核心改动：
  - 为 `/profile/records` 增加 `requiresStudent` 路由元信息，非学生访问时重定向：教师进入 `/teacher/statistics`，其他非学生回到个人信息页。
  - `useUserStore` 补充 `isStudent` 计算属性，供路由守卫和菜单显隐复用。
  - 头像下拉、移动端菜单和个人中心侧栏仅对学生展示“我的学习/学习统计”，教师保留“课程统计”入口。
- 验证结果：
  - 已执行：`npm run build`。
  - 结果：通过，保留既有大 chunk 警告。
  - 已执行：真实浏览器回归验证。
  - 结果：通过。教师访问 `/profile/records` 会重定向到 `/teacher/statistics`，头像/个人中心不再展示学生“我的学习/学习统计”入口；学生 `student1@example.com` 仍可打开 `/profile/records`；教师 `teacher1@example.com` 可打开 `/teacher/statistics/courses/1` 并查看学生学习明细。
