# UI Soft Blue 风格统一改造计划

## Goal

把用户认可的首页“登录 / 注册”按钮风格沉淀为项目级视觉方向，并按优先级逐步改造现有页面中适合升级的操作区、按钮组、卡片和状态提示，让项目整体更统一、更精致，但不破坏 Element Plus 的基础可用性和后台表格的操作效率。

## What I already know

- 用户明确喜欢刚刚改过的 Soft Blue 风格：浅蓝操作面、胶囊按钮、蓝色渐变主按钮、轻量次按钮、圆角和柔和阴影。
- 该风格已记录在 `.trellis/spec/frontend/component-guidelines.md` 的 `Visual Style Convention: Soft Blue Action Surfaces`。
- 当前项目是 Vue 3 + TypeScript + Element Plus，页面样式大多使用 scoped SCSS。
- 当前已应用的参考实现位于 `UI/src/components/layout/AppHeader.vue`：
  - `.auth-actions`
  - `.auth-btn--login`
  - `.auth-btn--register`
  - `.drawer-auth-actions`
- 后续改造应优先复用该视觉语言，而不是每个页面各写一套完全不同的按钮风格。

## Requirements

- 先盘点现有 UI 中适合替换为 Soft Blue 风格的区域。
- 分批改造，避免一次性大面积改动导致页面风格、布局和验证成本失控。
- 优先改造用户高频看到、视觉收益明显、风险较低的区域。
- 保留后台表格行内操作的紧凑性，不把所有小按钮都强行做成大胶囊按钮。
- 每一批改造后都要执行前端构建，并用浏览器验证目标页面。
- 每次改动 `UI/` 文件都要更新 `UI/operations-log.md`。

## Visual Direction

命名：Soft Blue Action Surfaces

风格关键词：

- 柔和浅蓝背景
- 胶囊式操作区
- 蓝色渐变主按钮
- 白底/透明底次按钮
- 轻阴影
- 大圆角
- 清晰主次层级
- 不花哨，但比默认 Element Plus 更有产品感

推荐设计语言：

- 主要操作：渐变蓝 + 阴影 + 胶囊圆角
- 次要操作：白底/透明底 + 蓝色文字 + hover 浅蓝边框
- 操作组容器：浅蓝底 + 浅蓝边框 + 圆角
- 卡片/状态块：白底或浅蓝底 + 细边框 + 柔和阴影

## Candidate UI Areas

### P0：优先改造，收益最高

1. `UI/src/views/course/CourseDetailPage.vue`
   - 位置：课程详情顶部主操作区、课程资料下载区、反馈 Tab 内提交按钮。
   - 原因：首页进入后最重要的业务页面，按钮很多且现在以默认 Element Plus 为主。
   - 改造方向：
     - “开始学习 / 继续学习 / 收藏 / 分享”等主操作改为 Soft Blue 操作组。
     - 课程资料下载按钮改为统一渐变 CTA。
     - 反馈提交按钮沿用同一主 CTA 风格。
   - 风险：中等，课程详情交互较多，需要浏览器验证。

2. `UI/src/components/feedback/FeedbackForm.vue`
   - 位置：提交反馈按钮和弹窗取消按钮。
   - 原因：刚完成反馈分派功能，用户正在关注这条链路；适合马上统一风格。
   - 改造方向：
     - 表单底部 `.form-actions` 改为浅蓝操作面。
     - 提交按钮为渐变主按钮，取消按钮为轻量次按钮。
   - 风险：低。

3. `UI/src/views/profile/ProfileInfoPage.vue`
   - 位置：头像“更换头像”、验证码按钮、保存修改按钮。
   - 原因：个人中心是用户高频页面，当前按钮风格较默认。
   - 改造方向：
     - 保存修改按钮改为主 CTA。
     - 头像上传区域做浅蓝卡片/操作面。
     - 验证码按钮保持轻量但统一圆角。
   - 风险：低到中等，涉及上传和表单。

4. `UI/src/views/auth/LoginPage.vue`、`UI/src/views/auth/RegisterPage.vue`、`UI/src/views/auth/ForgotPasswordPage.vue`
   - 位置：登录、注册、找回密码主按钮和步骤按钮。
   - 原因：未登录用户入口和 AppHeader 新按钮风格要一致。
   - 改造方向：
     - 主提交按钮改为渐变蓝大圆角。
     - “上一步 / 下一步 / 返回登录”等按钮做主次层级。
   - 风险：中等，表单状态多，需要验证登录/注册/找回密码流程至少基础展示。

### P1：第二批改造，提升管理页统一感

5. `UI/src/views/teacher/CourseListPage.vue`
   - 位置：页面头部“课程反馈 / 创建课程”、筛选栏“搜索 / 重置”、批量操作区。
   - 原因：讲师端主页面，当前有多个操作区，适合统一操作面。
   - 改造方向：
     - `.header-actions` 改为 Soft Blue 操作组。
     - `.filter-bar` 的搜索/重置按钮做轻量操作组。
     - `.batch-actions` 维持警示色语义，但圆角、间距、卡片感统一。
   - 风险：中等。

6. `UI/src/views/teacher/FeedbackManagePage.vue`
   - 位置：筛选栏、详情抽屉底部“回复并处理”、处理弹窗底部。
   - 原因：反馈链路相关页面，应与反馈表单同风格。
   - 改造方向：
     - 筛选操作区轻量化。
     - 处理按钮使用渐变主 CTA。
   - 风险：低。

7. `UI/src/views/admin/FeedbackManagePage.vue`
   - 位置：筛选栏、批量处理条、回复处理按钮、弹窗底部。
   - 原因：管理员反馈管理要和老师侧反馈管理保持一致。
   - 改造方向：
     - 与老师反馈页同步改造。
     - 批量处理条保持信息提示语义，但视觉更柔和。
   - 风险：低到中等。

8. `UI/src/views/admin/CategoryManagePage.vue`、`TagManagePage.vue`、`AnnouncementPage.vue`、`UserManagePage.vue`
   - 位置：页面头部新增按钮、筛选栏、弹窗底部。
   - 原因：后台页结构相似，适合抽象/批量统一。
   - 改造方向：
     - 页面头部主按钮统一为渐变 CTA。
     - 弹窗 footer 统一主次按钮风格。
     - 行内编辑/删除继续保持 compact text button，不做大按钮。
   - 风险：中等，页面较多，建议分小批。

### P2：第三批改造，谨慎处理

9. `UI/src/views/learn/LearningPage.vue`
   - 位置：学习页工具栏、资源下载、自动下一节提示。
   - 原因：沉浸式学习页已有特殊深色/工具型布局，不能强行套浅蓝。
   - 改造方向：
     - 只改局部 CTA，如“下载文档”“继续播放”。
     - 顶部工具栏保持沉浸式低干扰。
   - 风险：中到高，建议后置。

10. `UI/src/components/common/CourseCard.vue` 和首页课程列表
   - 位置：课程卡片 hover、角标、进入详情暗示。
   - 原因：卡片是首页主体，但不是纯按钮区。
   - 改造方向：
     - 可增加浅蓝 hover 光晕、边框和主信息层次。
     - 不建议把整张卡片改成按钮组。
   - 风险：中等，影响首页视觉密度。

## Out of Scope

- 本计划不改变后端接口、不改 API payload、不改数据库。
- 不替换 Element Plus，也不引入新的 UI 框架。
- 不一次性重写全站主题变量。
- 不强行改造表格行内小按钮；编辑、删除、归档等低层级行内操作仍以 compact text button 为主。
- 不在学习页做大面积浅蓝化，避免破坏沉浸式学习体验。

## Recommended Implementation Batches

### Batch 1：反馈与课程详情链路（推荐先做）

目标：把用户刚关注过的反馈链路和课程详情页先统一。

文件：

- `UI/src/views/course/CourseDetailPage.vue`
- `UI/src/components/feedback/FeedbackForm.vue`
- `UI/src/views/teacher/FeedbackManagePage.vue`
- `UI/src/views/admin/FeedbackManagePage.vue`

验收：

- [ ] 课程详情主操作区使用 Soft Blue 风格。
- [ ] 反馈表单底部操作按钮统一为浅蓝操作面 + 渐变主按钮。
- [ ] 老师/管理员反馈处理按钮和弹窗 footer 统一风格。
- [ ] `npm run build` 通过。
- [ ] 浏览器验证课程详情、反馈表单、老师反馈管理、管理员反馈管理。

### Batch 2：个人中心与认证页

目标：让用户入口和个人信息页形成统一产品感。

文件：

- `UI/src/views/profile/ProfileInfoPage.vue`
- `UI/src/views/auth/LoginPage.vue`
- `UI/src/views/auth/RegisterPage.vue`
- `UI/src/views/auth/ForgotPasswordPage.vue`

验收：

- [ ] 登录/注册/找回密码主按钮和步骤按钮统一风格。
- [ ] 个人资料保存、头像上传、验证码按钮层级清晰。
- [ ] PC 与移动端无横向溢出。
- [ ] `npm run build` 通过。
- [ ] 浏览器验证未登录入口页和个人资料页。

### Batch 3：讲师/管理员列表页操作区

目标：统一后台和讲师端页面头部、筛选栏、批量操作区。

文件：

- `UI/src/views/teacher/CourseListPage.vue`
- `UI/src/views/admin/CategoryManagePage.vue`
- `UI/src/views/admin/TagManagePage.vue`
- `UI/src/views/admin/AnnouncementPage.vue`
- `UI/src/views/admin/UserManagePage.vue`

验收：

- [ ] 页面头部新增/创建类按钮统一为渐变主 CTA。
- [ ] 筛选栏按钮统一为轻量操作区。
- [ ] 批量操作条保留状态色语义但更柔和。
- [ ] 行内操作按钮仍保持紧凑，不影响表格密度。
- [ ] `npm run build` 通过。
- [ ] 浏览器验证讲师课程列表和至少 2 个管理员页面。

### Batch 4：首页卡片与学习页局部增强

目标：做低风险局部增强，不破坏原布局。

文件：

- `UI/src/components/common/CourseCard.vue`
- `UI/src/views/home/HomePage.vue`
- `UI/src/views/learn/LearningPage.vue`

验收：

- [ ] 首页课程卡片 hover 更接近 Soft Blue 风格。
- [ ] 学习页仅局部 CTA 优化，不破坏沉浸式布局。
- [ ] `npm run build` 通过。
- [ ] 浏览器验证首页和学习页。

## Technical Approach

- 先以局部 scoped SCSS 改造为主，避免一次性抽全局组件带来回归风险。
- 当同一按钮组样式重复出现 3 次以上，再考虑抽为共享组件或全局 utility class。
- 每批改造都对照 `.trellis/spec/frontend/component-guidelines.md` 的 `Visual Style Convention: Soft Blue Action Surfaces`。
- 每批改造都更新 `UI/operations-log.md`。

## Acceptance Criteria

- [ ] 已明确全站适合改造的 UI 区域和优先级。
- [ ] 每批都有文件范围、改造目标和验收标准。
- [ ] 保留了不适合强行套用该风格的区域说明。
- [ ] 后续可以按 Batch 1 -> Batch 4 逐个实施。

## Definition of Done

- PRD 计划落盘。
- 用户确认先做哪一批。
- 每批实施时遵循前端 code-spec。
- 每批实施后执行构建和浏览器验证。
