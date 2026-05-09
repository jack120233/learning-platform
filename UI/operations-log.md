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

## 教师消息中心独立 UI 优化
时间：2026-05-08 10:29:14

- 变更原因：教师角色不应继续复用学生/个人中心的通用消息中心，需要独立承载学生反馈与管理员平台公告/通知。
- 涉及文件：
  - `src/router/index.ts`
  - `src/components/layout/AppHeader.vue`
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `src/components.d.ts`
  - `operations-log.md`
- 核心改动：
  - 在教师路由下新增 `/teacher/messages`，保留 `/profile/messages` 给学生和普通个人中心使用。
  - 顶部 PC 下拉菜单与移动端菜单的“消息中心”改为按教师中心权限跳转，教师进入教师专属消息中心，其他角色仍进入个人消息中心。
  - 新增教师消息中心页面，使用“学生反馈 / 平台通知”双 Tab；学生反馈复用教师反馈列表、详情、回复处理接口，平台通知复用个人消息列表、详情、已读、全部已读和删除接口。
  - 页面采用教师端现有 Soft Blue 风格、卡片列表、详情抽屉、回复处理弹窗，并补充 768px 以下响应式布局。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`。
  - 结果：构建通过；仍有既有大体积 chunk 警告。
  - 已执行：安装 Playwright Chromium，并用教师账号 `teacher2@example.com / Test123456` 验证 PC 下拉菜单和 390px 移动端菜单均进入 `/teacher/messages`。
  - 已执行：用学生账号 `student1@example.com / Test123456` 验证 PC 下拉菜单和 390px 移动端菜单仍进入 `/profile/messages`。
  - 已检查：教师账号接口权限包含 `teacher.course`，路由守卫允许直接访问 `/teacher/messages`。

## 消息中心删除后空白占位修复
时间：2026-05-09

- 变更原因：学生在 `/profile/messages` 删除消息后，旧卡片区域会残留大块空白，多次删除会累积；同时需要检查老师消息中心的平台通知删除链路。
- 涉及文件：
  - `src/views/profile/MessagesPage.vue`
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `operations-log.md`
- 核心改动：
  - 学生消息中心单删和批量删除成功后，先从本地 `messages` 列表同步移除已删除 ID、扣减当前分页总数并清理选中项，再刷新后端数据，避免等待刷新期间残留旧占位。
  - 删除后刷新逻辑改为先根据本地扣减后的 `totalPages` 夹紧当前页；当前页被删空时跳转到上一有效页，避免停留在越界空页。
  - 老师消息中心“平台通知”单删和批量删除应用相同的本地移除、总数扣减、选中项清理和分页夹紧逻辑；管理员消息中心当前主功能为反馈处理/系统消息发送表单，未发现同类消息卡片删除问题。
- 验证结果：
  - 已执行：`npm --prefix "UI" run build`。
  - 结果：通过；构建仍提示既有大体积 chunk 警告。
  - 已执行：真实前后端联调浏览器验证。通过管理员真实 API 给 `student1@example.com` 与 `teacher1@example.com` 各发送临时消息，分别在 `/profile/messages` 学生消息列表与老师“平台通知”页删除；删除后目标卡片从 DOM 消失、后端列表不再返回、列表高度收缩未留白。

## 教师反馈详情对话气泡布局优化
时间：2026-05-08

- 变更原因：教师查看学生反馈详情时需要更清晰地区分学生反馈与教师回复，提升阅读体验并保持现有处理流程不变。
- 涉及文件：
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `src/views/teacher/FeedbackManagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 将两个教师反馈详情 drawer 的内容区改为左右对话气泡布局，学生反馈固定左侧、教师回复固定右侧。
  - 学生气泡保留截图预览，截图随学生消息展示；未处理反馈不渲染空的教师气泡。
  - 教师气泡使用当前登录教师昵称/用户名作为展示名，回复时间优先使用 `replied_at`，缺失时回退 `processed_at`。
  - 补充 PC 与移动端气泡宽度和换行样式，避免长文本和图片在窄屏下横向溢出。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过，仍有既有大体积 chunk 警告。
  - 未执行：浏览器手动联调；当前会话仅完成代码与构建级验证，未进一步打开页面核对实际渲染。
  - 2026-05-08 追加检查修复：将教师反馈详情相关抽屉宽度改为 `min(固定宽度, 92vw)`，并补充气泡和截图的 `box-sizing` / `max-width` 约束，进一步避免窄屏横向溢出。

## 管理员与教师消息中心入口整合
时间：2026-05-08

- 变更原因：管理员消息中心需要从发送型系统消息页调整为用户反馈处理入口；教师消息入口需要统一到 `/profile/messages`，减少 `/teacher/messages` 与个人中心消息中心并存带来的认知成本。
- 涉及文件：
  - `src/router/index.ts`
  - `src/views/admin/AdminLayout.vue`
  - `src/views/admin/AdminMessagePage.vue`
  - `src/views/profile/MessagesPage.vue`
  - `src/views/profile/MyFeedbacksPage.vue`
  - `src/api/admin.ts`
  - `docs/前端接口文档.md`
  - `operations-log.md`
- 核心改动：
  - 将 `/admin/messages` 调整为管理员消息中心主入口，复用现有反馈列表、详情、回复处理、批量处理 API，默认筛选平台反馈，并保留课程反馈筛选能力。
  - `/admin/feedbacks` 改为兼容重定向到 `/admin/messages`；后台菜单移除独立“反馈管理”，以“消息中心”承接反馈处理。
  - 管理员消息中心保留可折叠的站内消息发送表单，但主视图不再是公告/通知收件箱。
  - `/profile/messages` 在老师登录时渲染老师消息中心体验（学生反馈 + 平台通知），学生仍使用原个人消息列表；`/teacher/messages` 改为重定向到 `/profile/messages`。
  - 管理端反馈类型补宽用户名、邮箱、手机号可空口径，避免前端展示假造角色或身份字段。
  - 2026-05-08 追加闭环修复：`src/views/profile/MyFeedbacksPage.vue` 新增“提交平台反馈”入口，复用锁定为系统问题的 `FeedbackForm`，学生提交成功后自动刷新我的反馈列表。
  - 2026-05-08 检查修复：更新 `docs/前端接口文档.md`，同步平台反馈无需 `course_id/target_user_id`、管理员消息中心默认处理系统反馈、处理回复回显到我的反馈页的契约说明。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。
  - 2026-05-08 检查复跑：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。

## 管理员消息中心入口与发送表单体验修复
时间：2026-05-08 19:16:30

- 变更原因：管理员访问个人中心消息页仍停留在通用消息中心，且管理员消息中心窄屏布局和站内信发送表单的收件人选择体验不符合当前使用需求。
- 涉及文件：
  - `src/views/profile/MessagesPage.vue`
  - `src/views/admin/AdminMessagePage.vue`
  - `src/api/admin.ts`
  - `operations-log.md`
- 核心改动：
  - `/profile/messages` 在管理员角色下使用 `useUserStore()` 与 Vue Router 重定向到 `/admin/messages`，教师仍渲染教师消息中心，学生仍使用个人消息中心。
  - 管理员消息中心补充页面、卡片、英雄区、筛选区和表格的窄屏宽度约束，减少右侧留白和内容下坠。
  - 发送站内信收件人改为复用 `fetchUsers` 的远程搜索选择器，展示昵称/用户名、角色和用户 ID，提交时仍发送 `user_id`。
  - 移除发送表单的“互动消息”类型和跳转链接字段，并从 `AdminMessageFormData` 中移除 `interaction` 与 `link`。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；仍提示既有大体积 chunk 警告。
  - 已执行：使用管理员账号 `admin1@example.com / Admin123456` 做浏览器冒烟验证，访问 `/profile/messages` 会进入 `/admin/messages`。
  - 已检查：`900px` 与 `390px` 视口下页面无横向溢出；发送表单显示“接收用户”选择器，不再出现“接收用户 ID”、“互动消息”和“跳转链接”。

## 管理员收件人搜索与用户身份展示修正
时间：2026-05-08 19:45:00

- 变更原因：发送站内消息接收用户选择器不应在未输入时展示所有用户，且项目按实名制使用用户名，昵称不参与身份识别；重名用户需要通过用户 ID 区分。
- 涉及文件：
  - `src/api/admin.ts`
  - `src/views/admin/AdminMessagePage.vue`
  - `src/views/profile/ProfileInfoPage.vue`
  - `src/views/profile/MyFeedbacksPage.vue`
  - `src/views/admin/FeedbackManagePage.vue`
  - `src/views/teacher/FeedbackManagePage.vue`
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `src/components/feedback/FeedbackForm.vue`
  - `src/components/layout/AppHeader.vue`
  - `operations-log.md`
- 核心改动：
  - 接收用户远程选择器改为仅在输入用户名或用户 ID 后查询，未输入时不展示全量用户。
  - `fetchUsers` 将后端用户列表返回的 `id` 映射为前端统一使用的 `user_id`，避免真实接口联调时收件人缺少用户 ID。
  - 接收用户选项与选中标签统一展示为 `username#user_id`，不再使用昵称。
  - 个人中心用户名展示改为 `username#user_id`，用于区分重名用户。
  - 管理员消息中心、我的反馈、管理员反馈管理、教师反馈管理、教师消息中心、反馈表单老师选择器和顶部登录用户展示均改为昵称无关的 `username#user_id` / `username#teacher_id` 口径；缺少用户名但有 ID 时展示 `用户#<id>` 或 `老师#<id>`。
  - 平台问题兜底仅根据课程和目标用户身份判断，不再依赖 `target_nickname`。
- 验证结果：
  - 已执行：针对本节 focused 文件 grep `target_nickname|userInfo.nickname|teacher.nickname|nickname |||currentFeedback.username|row.username ||`。
  - 结果：无命中，已确认目标文件中不再保留昵称 fallback。
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`。
  - 结果：通过；仍提示既有大体积 chunk 警告。
  - 已执行：使用真实后端 `/api/v1/auth/login` 登录管理员账号，并通过真实 `/api/v1/users` 接口验证用户名和用户 ID 搜索。
  - 结果：登录接口 200；`/api/v1/users?keyword=admin1` 返回真实后端字段 `id`，前端映射后页面展示 `admin1#1`；`/api/v1/users?keyword=1` 可返回 `student1#3`、`teacher1#2`、`admin1#1`。
  - 已执行：Playwright 在真实前后端联通状态下验证管理员消息中心页面。
  - 结果：`/profile/messages` 会进入 `/admin/messages`；900px 与 390px 视口无横向溢出；打开“发送站内消息”后空输入不展示全量用户；输入 `admin1` 展示 `admin1#1`；输入 `1` 展示 `student1#3`、`teacher1#2`、`admin1#1`；页面不再显示“互动消息”和“跳转链接”；个人中心显示 `admin1#1` 且不再显示昵称字段。

## 教师消息中心平台通知批量删除
时间：2026-05-09

- 变更原因：老师消息中心“平台通知”缺少批量管理能力，需要与学生消息中心批量选择、当前页全选、取消管理和确认删除交互保持一致。
- 涉及文件：
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `operations-log.md`
- 核心改动：
  - 平台通知 Tab 新增批量管理状态、卡片勾选、当前页全选/取消全选、取消管理和无选择禁用/提示。
  - 批量删除复用现有单条 `deleteMessage` 接口并发删除，使用 `Promise.allSettled` 处理部分失败并提示删除结果。
  - 删除成功后刷新平台通知列表、分页和全局未读数；当前打开详情被删除时自动关闭详情抽屉。
  - 保留平台通知单条查看、单条删除、全部已读流程，并补充移动端下批量工具条和卡片选择布局。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；仍提示既有大体积 chunk 警告。

## 管理员个人消息路由与反馈入口收口
时间：2026-05-09

- 变更原因：管理员不应继续使用管理后台独立“消息中心”入口，需要统一到个人中心消息页，并避免管理员进入个人反馈页；同时保留学生个人消息批量删除能力。
- 涉及文件：
  - `src/router/index.ts`
  - `src/views/admin/AdminLayout.vue`
  - `src/views/profile/ProfileLayout.vue`
  - `operations-log.md`
- 核心改动：
  - 从管理后台侧栏移除“系统消息”菜单，`/admin/messages` 改为重定向到 `/profile/messages`。
  - `/profile/messages` 保持普通认证页，不再对管理员做后台消息页跳转，管理员可直接使用个人中心消息中心。
  - 个人中心菜单对管理员隐藏“我的反馈”，管理员直接访问 `/profile/feedbacks` 时重定向到 `/profile/messages`。
  - 静态核对 `MessagesPage.vue` 现有批量管理、当前页全选、二次确认、并发单删、刷新列表/分页和未读数更新逻辑，未改动学生消息批量删除实现。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；仍提示既有大体积 chunk 警告。

## 管理端用户反馈详情抽屉样式对齐
时间：2026-05-09

- 变更原因：管理员“用户反馈详情”抽屉仍是旧的信息行与分段块展示，需要与老师侧反馈详情保持更一致的详情/对话式处理体验。
- 涉及文件：
  - `src/views/admin/FeedbackManagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 将管理端反馈详情抽屉标题调整为“用户反馈详情”，并改为浅蓝详情头、元信息卡片和对话流布局。
  - 在详情中集中展示提交人、反馈对象、处理状态、提交时间、反馈内容、截图和处理回复。
  - 保留原有“回复并处理”入口、处理弹窗和反馈数据刷新流程，补充长文本换行、图片预览和移动端单列布局。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；仍提示既有大体积 chunk 警告。

## Trellis 前端自检修正：管理员个人消息路由
时间：2026-05-09

- 变更原因：自检发现个人中心消息页仍保留管理员跳转 `/admin/messages` 的旧逻辑，导致管理员无法直接使用 `/profile/messages`。
- 涉及文件：
  - `src/views/profile/MessagesPage.vue`
  - `operations-log.md`
- 核心改动：
  - 移除管理员进入 `/profile/messages` 时替换到 `/admin/messages` 的页面内跳转。
  - 移除管理员消息页取空列表的特殊分支，保留教师账号复用教师消息中心的分支；管理员现在使用普通个人消息列表与批量管理逻辑。
  - 将管理员反馈详情抽屉宽度从固定 `540px` 调整为 `min(540px, 92vw)`，避免移动端横向溢出。
  - 补充教师平台通知单条/批量删除确认框关闭处理，避免点击关闭按钮时误提示删除失败。
  - 静态复查 `/admin/messages` 仅保留路由层重定向到 `/profile/messages`，未再发现反向跳转。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；仍提示既有大体积 chunk 警告。

## 统一用户身份展示组件与个人资料 ID 归一化
时间：2026-05-09

- 变更原因：全站多处 `用户名#id` 直接拼接显示较突兀，且个人资料接口后端返回 `id` 时前端 `user_id` 为空会出现 `#undefined`。
- 涉及文件：
  - `src/api/profile.ts`
  - `src/utils/format.ts`
  - `src/components/common/UserIdentity.vue`
  - `src/views/profile/ProfileInfoPage.vue`
  - `src/components/layout/AppHeader.vue`
  - `src/views/admin/FeedbackManagePage.vue`
  - `src/views/admin/AdminMessagePage.vue`
  - `src/views/profile/MyFeedbacksPage.vue`
  - `src/views/teacher/FeedbackManagePage.vue`
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `src/components/feedback/FeedbackForm.vue`
  - `operations-log.md`
- 核心改动：
  - 新增 `UserIdentity` 组件，将用户名作为主文本，用户 ID 作为浅蓝弱化徽标展示；补充 `formatUserIdentity` 字符串辅助函数用于 Element Plus 选项 label。
  - `fetchProfile()` 和 `updateProfile()` 统一将后端 `id` / `user_id` 映射为前端 `UserProfile.user_id`，个人资料页不再直接拼接 `username#user_id`。
  - 替换头部、个人资料、我的反馈、管理端反馈/消息、教师反馈/消息和反馈表单老师选择器中的主要身份展示，继续使用用户名 + 用户 ID 消歧，不使用昵称 fallback。
  - 缺少 ID 时仅展示用户名或 fallback，缺少用户名但有 ID 时展示 fallback + 弱化 ID 徽标，避免出现 `undefined`。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`。
  - 结果：通过；仍提示既有大体积 chunk 警告。

## 一次性用户名修改与老师开放改名机会入口
时间：2026-05-09

- 变更原因：用户需要在个人信息页自助修改用户名一次，并在提交前二次确认；老师需要有完整前端入口为指定用户开放一次额外改名机会。
- 涉及文件：
  - `src/api/profile.ts`
  - `src/api/teacher.ts`
  - `src/views/profile/ProfileInfoPage.vue`
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `operations-log.md`
- 核心改动：
  - 个人资料 API 类型与映射补充 `original_username`、`username_change_remaining`、`can_change_username`，资料更新请求支持提交 `username`。
  - 个人信息页新增用户名编辑、原用户名和剩余改名机会展示；用户名变更提交前使用 `ElMessageBox.confirm` 二次确认，成功后同步更新 Pinia 用户 Store。
  - 老师 API 新增用户搜索和开放改名机会调用，统一映射后端 `id/user_id` 与改名状态字段。
  - 教师消息中心新增“改名机会”Tab，老师可搜索用户名/用户 ID、选择目标用户并开放一次改名机会，保留二次确认和状态回显。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`。
  - 结果：通过；仍提示既有大体积 chunk 警告。

## 管理员个人消息中心整合与改名提示修正
时间：2026-05-09

- 变更原因：管理员访问 `/profile/messages` 仍显示旧个人消息列表，且管理员个人资料仍可能展示改名剩余次数提示；需要将新版管理员消息中心整合到个人中心消息页，并让管理员/老师免次数规则在前端表现一致。
- 涉及文件：
  - `src/views/profile/MessagesPage.vue`
  - `src/views/profile/ProfileInfoPage.vue`
  - `operations-log.md`
- 核心改动：
  - `/profile/messages` 对管理员角色直接渲染新版 `AdminMessagePage`，老师继续渲染老师消息中心，普通用户保留原个人消息列表。
  - 个人资料页将老师和管理员统一视为不受改名次数限制，隐藏剩余次数提示，并调整二次确认文案避免提示会消耗次数。
- 验证结果：
  - 已执行：`cd "UI" && npx vue-tsc -b`
  - 结果：通过
  - 已执行：`cd "UI" && npm run build`
  - 结果：通过
  - 备注：构建仍提示既有大体积 chunk 警告，不影响本次功能正确性；浏览器烟测待执行。

## 个人资料、消息反馈历史管理与反馈处理体验修正
时间：2026-05-09

- 变更原因：个人资料只读区布局、老师消息中心改名机会搜索、个人反馈历史管理、管理员个人消息中心用户反馈处理体验需要按最新需求统一收口。
- 涉及文件：
  - `src/api/profile.ts`
  - `src/api/admin.ts`
  - `src/views/profile/ProfileInfoPage.vue`
  - `src/views/profile/MyFeedbacksPage.vue`
  - `src/views/teacher/TeacherMessageCenterPage.vue`
  - `src/views/admin/AdminMessagePage.vue`
  - `operations-log.md`
- 核心改动：
  - 个人资料只读信息区改为浅蓝卡片式网格，角色与状态标签集中展示，并补充移动端单列布局。
  - `/profile/feedbacks` 新增我的反馈单条删除、批量管理、当前页选择和删除后分页刷新能力，复用反馈提交人删除接口。
  - 老师消息中心改名机会搜索限定 `role=student`，并将 `active` 状态展示为“正常”；学生反馈详情抽屉移除删除按钮，保留列表单删和批量删除。
  - 管理员消息中心用户反馈列表新增单删和批量删除；详情抽屉改为与老师侧一致的反馈对话气泡布局，并保留回复处理入口。
  - 前端 API 补充我的反馈删除、管理端反馈删除和批量删除封装。
  - 自检补充：改名机会说明文案同步为“指定学生”，避免与实际只搜索学生用户的范围不一致。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。
  - 备注：本条记录为本轮前端变更留痕；自检后重新执行 `npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`，结果通过；未额外执行浏览器手动联调。

## 个人资料用户名历史与管理员反馈抽屉操作精简
时间：2026-05-09

- 变更原因：管理员用户反馈详情抽屉中的删除按钮视觉干扰较强，个人资料页不应展示数据库审计用的历史用户名。
- 涉及文件：
  - `src/views/admin/AdminMessagePage.vue`
  - `src/views/profile/ProfileInfoPage.vue`
  - `operations-log.md`
- 核心改动：
  - 移除管理员 `/profile/messages` 用户反馈详情抽屉内的“删除反馈”按钮，仅保留待处理反馈的“回复并处理”入口。
  - 保留管理员反馈列表行内删除和批量删除逻辑不变。
  - 移除个人资料只读区“原用户名”展示行，前端类型和 API 字段继续兼容后端返回。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。

## 管理员公告操作列布局优化
时间：2026-05-09

- 变更原因：管理员公告管理页表格右侧“操作”列的行内文字按钮视觉松散，需要与当前后台 Soft Blue 操作面风格对齐。
- 涉及文件：
  - `src/views/admin/AnnouncementPage.vue`
  - `operations-log.md`
- 核心改动：
  - 将公告表格操作列改为居中的浅蓝软操作面按钮组，保留编辑、发布、转草稿和删除动作。
  - 为发布、转草稿和删除按钮补充主次/警示/危险层级，收紧按钮间距并提高操作列可读性。
  - 补充小屏下两列网格排列，减少窄屏操作列横向拥挤。
- 验证结果：
  - 已执行：`npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build`
  - 结果：通过；构建仍提示既有大体积 chunk 警告。
  - 已执行：`git diff --check -- UI/src/views/admin/AnnouncementPage.vue`
  - 结果：通过。
  - 已执行：浏览器访问 `http://127.0.0.1:3000/admin/announcements`，分别检查 1280px 桌面和 390px 窄屏视口。
  - 结果：操作列已显示浅蓝软操作面按钮组，`编辑 / 转草稿 / 删除` 可见；390px 视口下 `documentElement.scrollWidth <= innerWidth`，未出现页面级横向溢出。
  - 备注：当前数据行均为已发布公告，浏览器冒烟只观察到 `转草稿`，未观察到草稿行的 `发布` 按钮；代码保留草稿行发布入口。
