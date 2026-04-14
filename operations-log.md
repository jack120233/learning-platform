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
  * **导航精简**：移除 AppHeader 中与 Logo 功能重复的“首页”项。
- 验证结果：
  - 已执行：手动验证各资源类型进度同步正常。
  - 已执行：验证已发布课程编辑保存不再产生多重弹窗。
  - 结果：通过。
