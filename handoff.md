# 教师反馈详情对话式展示优化任务交接

## 任务目录

- Trellis task: `.trellis/tasks/05-08-optimize-teacher-feedback-detail-chat-layout`
- 任务状态：`planning`
- 建议后续从项目根目录继续：`/Users/jacob/Developer/a3.learn_platform/learning-platform`

## 用户确认的目标

优化教师角色查看学生反馈详情的页面展示方式：

- 当前反馈详情展示比较居中、信息块化。
- 目标改成类似微信/IM 的两人对话样式。
- 学生反馈内容靠左展示。
- 老师回复内容靠右展示。
- 学生反馈气泡显示反馈人的学生用户名。
- 老师回复气泡显示当前登录老师的用户名/昵称。
- 每一条反馈/回复内容上方或下方都要带时间。
- 保持现有反馈处理流程、API 和响应式适配。

## 已讨论并确认的实现方向

### 展示结构

教师查看学生反馈详情时，详情主体应改为对话流：

1. 学生消息气泡
   - 左侧对齐。
   - 名称：反馈提交学生。
   - 内容：`currentFeedback.content`。
   - 时间：`currentFeedback.created_at`。
   - 如有截图，放在学生气泡下方或气泡内下方，继续保留图片预览。

2. 老师回复气泡
   - 右侧对齐。
   - 仅当 `currentFeedback.reply` 存在时展示。
   - 名称：当前登录教师。
   - 内容：`currentFeedback.reply`。
   - 时间：优先 `currentFeedback.replied_at`，没有则用 `currentFeedback.processed_at`。
   - 如果反馈还未处理，不展示空的右侧气泡，只保留“回复并处理”按钮。

### 名称来源

- 学生侧名称：
  - 优先 `currentFeedback.username`
  - 兜底 `用户${currentFeedback.user_id}`
- 教师侧名称：
  - 使用 `useUserStore()` 中的 `userStore.userInfo.nickname || userStore.userInfo.username`
  - 不直接读取 `localStorage`

### 样式方向

- 学生气泡：左侧，浅灰/浅蓝背景。
- 教师气泡：右侧，主色系浅蓝或渐变背景。
- 名称和时间使用小字号、弱化颜色。
- 内容支持换行：`white-space: pre-wrap`。
- 长文本自动换行，避免横向溢出。
- PC 端气泡最大宽度建议约 `72%`。
- 移动端气泡最大宽度建议放宽到 `86%`。
- 图片在移动端自动换行或缩小，不能出现横向滚动。

## 可能涉及的文件

### 主要修改文件

- `UI/src/views/teacher/TeacherMessageCenterPage.vue`
  - 教师消息中心新页面。
  - 当前“学生反馈详情” drawer 在这里。
  - 需要把当前 `rich-content` / `reply-box` 信息块改成 chat-style 气泡。

### 建议同步检查/可能同步修改

- `UI/src/views/teacher/FeedbackManagePage.vue`
  - 老的教师“课程反馈”管理页。
  - 也有反馈详情 drawer。
  - 如果希望两个入口展示一致，建议同步改成同样的对话式样式。

### 需要读但不应乱改

- `UI/src/store/user.ts`
  - 已有 `userStore.userInfo.nickname`、`userStore.userInfo.username`。
  - 继续用 Pinia 作为登录态/用户信息单一来源。

### 必须更新

- `UI/operations-log.md`
  - 按 `UI/CLAUDE.md` 要求，只要 UI 文件有实际变更就必须追加记录。
  - 记录内容至少包含：变更时间、变更原因、涉及文件、核心改动、验证结果。

## 当前已知代码位置

### TeacherMessageCenterPage.vue 当前结构

文件：`UI/src/views/teacher/TeacherMessageCenterPage.vue`

当前反馈详情 drawer 大致在：

```vue
<el-drawer v-model="showFeedbackDrawer" title="学生反馈详情" size="520px" class="message-drawer">
  <div v-if="isLoadingFeedbackDetail" class="loading-container">
    <el-skeleton :rows="7" animated />
  </div>
  <template v-else-if="currentFeedback">
    <div class="detail-section">...</div>

    <el-divider>反馈内容</el-divider>
    <div class="rich-content">{{ currentFeedback.content }}</div>

    <template v-if="currentFeedback.images.length">...</template>

    <template v-if="currentFeedback.reply">
      <el-divider>老师回复</el-divider>
      <div class="reply-box">
        <p>{{ currentFeedback.reply }}</p>
        <span>{{ formatTime(currentFeedback.replied_at) }}</span>
      </div>
    </template>

    <div v-if="currentFeedback.status === 'pending'" class="drawer-action-area">...</div>
  </template>
</el-drawer>
```

已有辅助函数：

```ts
const userStore = useUserStore()

function formatTime(time: string | null | undefined) { ... }

function getStudentName(feedback: TeacherFeedbackItem | TeacherFeedbackDetail) {
  return feedback.username || `用户${feedback.user_id}`
}

function getTargetName(feedback: TeacherFeedbackItem | TeacherFeedbackDetail) {
  return feedback.target_nickname || feedback.target_username || '当前讲师'
}
```

可以新增类似：

```ts
const teacherDisplayName = computed(() => userStore.userInfo.nickname || userStore.userInfo.username || '当前讲师')
```

也可以直接在模板中用 `userStore.userInfo.nickname || userStore.userInfo.username`。

### FeedbackManagePage.vue 当前结构

文件：`UI/src/views/teacher/FeedbackManagePage.vue`

当前详情 drawer 也采用信息块：

```vue
<el-drawer v-model="showDetailDrawer" title="课程反馈详情" size="500px">
  <template v-else-if="currentFeedback">
    <div class="detail-section">...</div>

    <el-divider>反馈内容</el-divider>
    <div class="feedback-content">{{ currentFeedback.content }}</div>

    <template v-if="currentFeedback.reply">
      <el-divider>老师回复</el-divider>
      <div class="reply-content">{{ currentFeedback.reply }}</div>
    </template>

    <template v-if="currentFeedback.images?.length">...</template>

    <div class="action-area" v-if="currentFeedback.status === 'pending'">...</div>
  </template>
</el-drawer>
```

如果同步修改，需要在该文件也引入并使用：

```ts
import { useUserStore } from '@/store/user'
const userStore = useUserStore()
const teacherDisplayName = computed(() => userStore.userInfo.nickname || userStore.userInfo.username || '当前讲师')
```

该文件已经 import 了 `computed`，可直接复用。

## Trellis / worktree 情况

用户说“存在 git 仓库了，重新用 worktree”。

实际检查结果：

- 会话初始目录是：`/Users/jacob/Developer/a3.learn_platform`
- 该目录本身不是 git 仓库。
- 真正 git 仓库是：`/Users/jacob/Developer/a3.learn_platform/learning-platform`
- `git -C /Users/jacob/Developer/a3.learn_platform/learning-platform rev-parse --show-toplevel` 返回仓库根目录。

尝试过内置 `EnterWorktree` 和 Agent `isolation: "worktree"`，均失败，原因是工具按会话初始目录判断，不识别子目录仓库：

```text
Cannot create a worktree: not in a git repository and no WorktreeCreate hooks are configured.
```

已手动创建过一个 git worktree：

```text
/Users/jacob/Developer/a3.learn_platform/learning-platform/.claude/worktrees/teacher-feedback-chat-layout
```

分支：

```text
claude/teacher-feedback-chat-layout
```

创建命令曾执行：

```bash
git -C "/Users/jacob/Developer/a3.learn_platform/learning-platform" worktree add "/Users/jacob/Developer/a3.learn_platform/learning-platform/.claude/worktrees/teacher-feedback-chat-layout" -b "claude/teacher-feedback-chat-layout"
```

注意：主工作区已有大量未提交改动，包括前面教师消息中心、启动脚本、文档、operations-log 等。已尝试将这些基线改动同步到手动 worktree。

建议后续如果从项目根目录重新启动 Claude：

1. 直接在 `/Users/jacob/Developer/a3.learn_platform/learning-platform` 启动。
2. 再用内置 worktree 或手动 worktree。
3. 如果继续使用已有手动 worktree，先检查：

```bash
git -C "/Users/jacob/Developer/a3.learn_platform/learning-platform/.claude/worktrees/teacher-feedback-chat-layout" status --short
```

## Trellis 下一步要求

当前 workflow-state 显示任务仍在 `planning`：

```text
Task: optimize-teacher-feedback-detail-chat-layout (planning)
```

后续必须完成：

1. 加载/遵循 `trellis-brainstorm`。
2. 创建并迭代 `prd.md`。
3. Phase 1.3 必须整理：
   - `implement.jsonl`
   - `check.jsonl`
4. 然后运行：

```bash
python3 ./.trellis/scripts/task.py start 05-08-optimize-teacher-feedback-detail-chat-layout
```

或根据实际 task.py 所在目录调整路径。

当前 task 目录里已经有：

- `task.json`
- `implement.jsonl`
- `check.jsonl`

但还没有确认看到 `prd.md` 和 `research/*.md`。

## 建议写入 PRD 的内容

PRD 可包含以下内容：

### Goal

优化教师查看学生反馈详情时的阅读体验，将反馈和回复从信息块改成对话气泡，让教师更直观地区分学生反馈与自己的回复。

### Requirements

- 教师反馈详情中，学生反馈以左侧气泡展示。
- 教师回复以右侧气泡展示。
- 学生气泡显示学生用户名和提交时间。
- 教师气泡显示当前登录教师用户名/昵称和回复时间。
- 每条内容都显示时间。
- 图片继续跟随学生反馈展示并保留预览能力。
- 未处理反馈只展示学生反馈和“回复并处理”按钮。
- 已处理反馈展示学生反馈和教师回复。
- 保持现有 API、处理 dialog、刷新逻辑不变。
- 移动端无横向溢出。

### Acceptance Criteria

- [ ] 教师在 `/teacher/messages` 打开学生反馈详情，学生反馈靠左显示。
- [ ] 学生反馈气泡显示学生用户名和反馈提交时间。
- [ ] 已处理反馈中，教师回复靠右显示。
- [ ] 教师回复气泡显示当前登录教师用户名/昵称和回复时间。
- [ ] 未处理反馈不显示空教师回复气泡，并仍可点击“回复并处理”。
- [ ] 有截图的反馈仍能预览截图。
- [ ] 移动端宽度下无横向溢出。
- [ ] `npm run build` 通过。
- [ ] `UI/operations-log.md` 已追加记录。

### Out of Scope

- 不修改后端反馈 API。
- 不修改学生“我的反馈”页面。
- 不改变反馈提交、处理、筛选、搜索、分页逻辑。
- 不新增全局 store。
- 不直接读取 `localStorage`。

## 建议实现步骤

1. 在项目根目录或 worktree 中检查当前状态。
2. 补齐 Trellis `prd.md`。
3. 补齐 `implement.jsonl` / `check.jsonl`，至少让实现/检查代理读取：
   - `UI/CLAUDE.md`
   - `CLAUDE.md`
   - `UI/src/views/teacher/TeacherMessageCenterPage.vue`
   - `UI/src/views/teacher/FeedbackManagePage.vue`
   - `UI/src/store/user.ts`
   - `UI/operations-log.md`
4. `task.py start` 切到 in_progress。
5. 修改 `TeacherMessageCenterPage.vue` 的反馈详情 drawer。
6. 视一致性需要修改 `FeedbackManagePage.vue`。
7. 追加 `UI/operations-log.md`。
8. 运行：

```bash
npm --prefix "/Users/jacob/Developer/a3.learn_platform/learning-platform/UI" run build
```

9. 如果开发服务仍在运行，可用 Playwright 简单验证：
   - 教师 `teacher1@example.com / Test123456`
   - 打开 `/teacher/messages`
   - 查看已处理反馈详情，检查左右气泡。
   - 查看未处理反馈详情，检查只有左侧学生气泡和处理按钮。

## 前置上下文：已完成的相关工作

之前已完成教师消息中心功能：

- 新增 `/teacher/messages`。
- 教师顶部/移动端“消息中心”跳转到 `/teacher/messages`。
- 学生仍跳转 `/profile/messages`。
- `TeacherMessageCenterPage.vue` 包含：
  - “学生反馈”Tab。
  - “平台通知”Tab。
  - 反馈详情 drawer。
  - 回复处理 dialog。

之前已用 Playwright 验证完整反馈流程通过：

- 学生 `student1@example.com / Test123456` 在课程 `Python入门` 提交反馈。
- 教师 `teacher1@example.com / Test123456` 在 `/teacher/messages` 能看到反馈。
- 教师回复并处理。
- 学生在 `/profile/feedbacks` 能看到已处理和教师回复。

已验证的反馈数据示例：

- `feedback_id=2`
- 学生：`student1`
- 教师：`teacher1 / 张老师`
- 课程：`Python入门`
- 状态：`processed`

## 注意事项

- UI 项目规则要求所有前端实际文件变更都必须更新 `UI/operations-log.md`。
- 业务代码不要直接读取 `localStorage`，登录态和用户信息必须通过 `useUserStore()`。
- 响应式适配是强制要求，移动端不能横向溢出。
- 不要为了这个任务改后端。
- 不要新增不必要的公共组件，优先在现有页面内完成。
