# Bootstrap Guidelines 学习说明

> 写给项目新手：解释本次“初始化/完善项目开发规范文档”到底做了什么，以及这些文档以后有什么用。

---

## 1. 这次任务一句话总结

这次不是在改业务功能，也不是在改前端页面或后端接口。

这次做的是：**把项目已有的开发习惯、目录结构、代码写法、禁用写法整理成一套规范文档，放到 `.trellis/spec/` 里面，方便以后 AI 或人继续开发时按项目原有风格工作。**

简单理解：

```text
CLAUDE.md 里原本有一些项目说明
真实代码里也体现了很多开发习惯

这次把这些内容整理成：
.trellis/spec/frontend/*.md
.trellis/spec/backend/*.md

以后 AI 开发前会读取这些规范，少犯“写得不像这个项目”的错误。
```

---

## 2. 什么是 Trellis？

Trellis 可以理解成一个“AI 协作开发工作流”。

它会帮项目维护这些东西：

```text
.trellis/
├── workflow.md       # 开发流程说明
├── tasks/            # 当前/历史任务
├── spec/             # 项目开发规范
└── workspace/        # 每次会话的工作记录
```

对你来说，最重要的是两个目录：

### `.trellis/tasks/`

这里放“任务”。

比如当前任务：

```text
.trellis/tasks/00-bootstrap-guidelines/
```

它代表：初始化项目开发规范。

里面有：

```text
prd.md           # 这个任务要做什么
 task.json        # 任务状态、子任务、负责人
 implement.jsonl  # 给实现 agent 注入哪些上下文
 check.jsonl      # 给检查 agent 注入哪些上下文
 debug.jsonl      # 给 debug agent 注入哪些上下文
```

### `.trellis/spec/`

这里放“项目开发规范”。

以后 AI 或开发者做前端/后端任务时，会先读这里的规范。

```text
.trellis/spec/
├── frontend/     # 前端开发规范
├── backend/      # 后端开发规范
└── guides/       # 通用思考指南
```

---

## 3. 什么是“开发规范文档”？

开发规范文档不是需求文档，也不是接口文档。

它主要回答这些问题：

- 代码应该放在哪个目录？
- 前端组件应该怎么写？
- 后端接口应该怎么分层？
- API 返回值应该是什么格式？
- 哪些写法是禁止的？
- 改完代码应该跑什么验证？
- 遇到错误应该怎么处理？
- 日志应该怎么打？

比如，你以后让 AI 改一个反馈功能，如果没有规范，它可能乱写：

```text
随便新建一个 axios 实例
随便在组件里读 localStorage
随便把后端 SQL 写到 route 里面
随便返回一个 { success: true }
```

但你的项目其实有固定规则：

```text
前端 API 必须走 UI/src/api/index.ts
登录状态必须走 useUserStore()
后端接口必须返回 { code, message, data }
数据库查询应该放 service 层
实际改 UI 文件要更新 UI/operations-log.md
实际改后端文件要更新 project_code/operations-log.md
```

这些规则整理进 `.trellis/spec/` 后，以后 AI 就更容易按项目风格写代码。

---

## 4. 为什么不能只靠 CLAUDE.md？

项目里已经有几个 `CLAUDE.md`：

```text
CLAUDE.md                         # 根目录总规则
UI/CLAUDE.md                      # 前端规则
project_code/CLAUDE.md            # 后端规则
```

它们的作用是：告诉 Claude Code 这个项目的大方向和入口规则。

比如：

- 前端任务应该去 `UI/`
- 后端任务应该去 `project_code/backend/`
- 登录态统一走 Pinia Store
- 后端响应格式是 `{ code, message, data }`

但 `CLAUDE.md` 更像“总说明书”。

Trellis 的 `.trellis/spec/` 更像“分门别类的开发手册”。

区别大概是：

| 文件 | 作用 |
|---|---|
| `CLAUDE.md` | 告诉 AI 项目入口、总体规则、重要约束 |
| `.trellis/spec/frontend/*.md` | 告诉 AI 前端每类代码怎么写 |
| `.trellis/spec/backend/*.md` | 告诉 AI 后端每类代码怎么写 |
| `.trellis/tasks/*` | 记录当前正在做什么任务 |
| `.trellis/workspace/*` | 记录一次会话做了什么 |

这次操作的核心就是：**把 CLAUDE.md 和真实代码里的规则拆解、补充、整理到 `.trellis/spec/`。**

---

## 5. 我这次具体执行了什么？

### 第一步：读取当前任务

我先读取了：

```text
.trellis/tasks/00-bootstrap-guidelines/prd.md
.trellis/tasks/00-bootstrap-guidelines/task.json
.trellis/workflow.md
```

目的：确认当前任务到底要做什么。

结果发现任务要求是：

```text
Fill in project development guidelines for AI agents
```

也就是：为 AI agents 填写项目开发指南。

---

### 第二步：查看已有规则能不能复用

我检查了：

```text
CLAUDE.md
UI/CLAUDE.md
project_code/CLAUDE.md
AGENTS.md
```

目的：不要凭空编规范，而是复用你项目已经有的说明。

这一步发现：

- 根目录 `CLAUDE.md` 已经说明了前后端目录路由规则
- `UI/CLAUDE.md` 已经说明了前端技术栈、API、Store、路由、样式规范
- `project_code/CLAUDE.md` 已经说明了后端技术栈、API、测试、operations-log 要求
- `AGENTS.md` 是 Trellis 自动管理的入口说明

所以这些内容可以迁移到 `.trellis/spec/`。

---

### 第三步：查看真实代码

我读取了一些真实代码文件作为例子。

前端例子：

```text
UI/src/api/index.ts
UI/src/api/profile.ts
UI/src/api/learning.ts
UI/src/store/user.ts
UI/src/store/learn.ts
UI/src/components/feedback/FeedbackForm.vue
UI/src/components/common/CourseCard.vue
UI/src/composables/usePagination.ts
UI/src/router/index.ts
```

后端例子：

```text
project_code/backend/app/main.py
project_code/backend/app/core/exceptions.py
project_code/backend/app/core/logging.py
project_code/backend/app/middleware/logging_middleware.py
project_code/backend/app/models/base.py
project_code/backend/app/models/feedback.py
project_code/backend/app/models/course.py
project_code/backend/app/schemas/common.py
project_code/backend/app/schemas/feedback.py
project_code/backend/app/api/v1/feedbacks.py
project_code/backend/app/services/feedback_service.py
project_code/backend/tests/conftest.py
project_code/backend/tests/test_feedbacks.py
```

目的：规范文档不能只写“理想做法”，要写这个项目真实正在用的做法。

比如看到前端真实代码里：

```ts
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}
```

所以我把“前端 API 响应结构”写进了类型安全规范。

又比如看到后端真实代码里：

```py
return ApiResponse.success(
    data=FeedbackResponse.model_validate(detail),
    message="提交成功",
)
```

所以我把“后端成功响应必须走 ApiResponse”写进了后端质量规范。

---

### 第四步：初始化 Trellis 上下文文件

我运行了：

```bash
python ./.trellis/scripts/task.py init-context ".trellis/tasks/00-bootstrap-guidelines" fullstack
python ./.trellis/scripts/task.py start ".trellis/tasks/00-bootstrap-guidelines"
```

这一步生成/确认了：

```text
implement.jsonl
check.jsonl
debug.jsonl
```

这些文件的作用是：告诉不同 AI agent 在执行任务时应该自动读取哪些上下文。

例如：

- implement agent 写代码时读哪些规范
- check agent 检查代码时读哪些规范
- debug agent 修 bug 时读哪些规范

这就是 Trellis 里说的：

```text
Code-spec context is injected, not remembered.
```

意思是：不要指望 AI 靠记忆，而是把规范文件明确注入给它。

---

### 第五步：填充前端规范文档

我填了这些文件：

```text
.trellis/spec/frontend/directory-structure.md
.trellis/spec/frontend/component-guidelines.md
.trellis/spec/frontend/hook-guidelines.md
.trellis/spec/frontend/state-management.md
.trellis/spec/frontend/type-safety.md
.trellis/spec/frontend/quality-guidelines.md
```

每个文件的意义如下。

---

## 6. 前端规范文档分别有什么用？

### 6.1 `frontend/directory-structure.md`

作用：告诉 AI 前端代码应该放在哪里。

它说明：

```text
UI/src/api/          # API 请求封装
UI/src/store/        # Pinia 状态管理
UI/src/router/       # Vue Router 路由
UI/src/components/   # 公共组件
UI/src/views/        # 页面
UI/src/composables/  # 可复用组合逻辑
UI/src/utils/        # 工具函数
```

意义：防止 AI 把文件放错地方。

比如：

- 页面应该放 `views/`
- 公共组件放 `components/`
- 页面专用小组件可以放 `views/xxx/components/`
- API 请求不要写在组件里，要放 `api/`

---

### 6.2 `frontend/component-guidelines.md`

作用：告诉 AI Vue 组件应该怎么写。

它说明：

- 使用 `<script setup lang="ts">`
- props 要有 TypeScript 类型
- emits 要有类型
- 样式用 `<style lang="scss" scoped>`
- 表单、按钮、上传、弹窗等优先用 Element Plus
- 页面要考虑移动端

意义：防止 AI 写出风格不一致的组件。

比如正确写法：

```ts
interface Props {
  mode?: 'inline' | 'dialog'
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'inline',
})
```

不要写成没有类型的 props。

---

### 6.3 `frontend/hook-guidelines.md`

这里的 hook 在 Vue 项目里通常叫 **Composable**。

作用：告诉 AI 什么时候该写 `useXxx.ts`。

比如项目里有：

```text
UI/src/composables/usePagination.ts
UI/src/composables/useProgressSync.ts
UI/src/composables/useBreakpoint.ts
```

规范里说明：

- 可复用的状态逻辑可以放 composable
- 一次性页面状态不要强行抽 composable
- API 请求函数不放 composable，放 `api/`
- 全局状态不放 composable，放 Pinia Store

意义：防止 AI 过度封装。

---

### 6.4 `frontend/state-management.md`

作用：告诉 AI 前端状态应该放哪里。

它把状态分成：

| 状态类型 | 放哪里 |
|---|---|
| 表单输入、弹窗开关、当前页 loading | 组件本地 `ref/reactive` |
| 登录状态、权限、用户信息 | `useUserStore()` |
| 学习页当前课程/资源/进度 | `useLearnStore()` |
| URL 参数 | Vue Router |
| 后端列表数据 | API + 页面/Composable |

最重要规则：

```text
业务代码不要直接读 localStorage 判断登录状态。
必须用 useUserStore()。
```

意义：防止登录状态混乱。

---

### 6.5 `frontend/type-safety.md`

作用：告诉 AI TypeScript 类型应该怎么组织。

它说明：

- API 类型和 API 函数放在同一个 `api/*.ts`
- Store 专用类型放 Store 文件里
- 组件 props/emits 在组件里定义
- 已知枚举用联合类型，不要随便写 string

比如：

```ts
export type UserRole = 'student' | 'teacher' | 'admin' | null
```

而不是：

```ts
role: string
```

意义：减少字段写错、接口对不上、运行时报错。

---

### 6.6 `frontend/quality-guidelines.md`

作用：前端开发完成前的质量检查清单。

它说明：

- API 调用必须走 `UI/src/api/index.ts`
- 登录/权限必须走 `useUserStore()`
- 路由权限应该写在 `router/index.ts` 的 meta/guard
- 页面要移动端适配
- 改前端后应该考虑运行：

```bash
npm run build
npx vue-tsc -b
```

如果改了真实 `UI/` 文件，还要更新：

```text
UI/operations-log.md
```

意义：保证前端改动不是“能写出来就算完”，还要能构建、类型正确、符合项目规则。

---

## 7. 后端规范文档分别有什么用？

我填了这些后端文件：

```text
.trellis/spec/backend/directory-structure.md
.trellis/spec/backend/database-guidelines.md
.trellis/spec/backend/error-handling.md
.trellis/spec/backend/logging-guidelines.md
.trellis/spec/backend/quality-guidelines.md
```

---

### 7.1 `backend/directory-structure.md`

作用：告诉 AI 后端代码应该放在哪里。

项目后端分层大概是：

```text
project_code/backend/app/
├── api/v1/       # FastAPI 路由
├── schemas/      # Pydantic 请求/响应模型
├── services/     # 业务逻辑和数据库查询
├── models/       # SQLAlchemy 数据模型
├── core/         # 通用配置、安全、异常、依赖、日志
├── middleware/   # 中间件
└── main.py       # FastAPI 应用入口
```

意义：防止 AI 把业务逻辑直接塞进路由，或者把数据库查询写到 schema 里。

标准后端分层是：

```text
API route → schema → service → model → database
```

---

### 7.2 `backend/database-guidelines.md`

作用：告诉 AI 数据库模型和查询怎么写。

它说明：

- ORM 用 SQLAlchemy 2.x async
- 模型继承 `BaseModel`
- 字段用 `Mapped[...]` 和 `mapped_column(...)`
- 查询逻辑放 service 层
- 分页查询要算 total
- 改表结构要考虑兼容逻辑和测试

比如项目真实模型：

```py
class Feedback(BaseModel):
    __tablename__ = "feedbacks"

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="用户ID",
    )
```

意义：防止 AI 用错 ORM 风格，或者把 SQL 写乱。

---

### 7.3 `backend/error-handling.md`

作用：告诉 AI 后端错误怎么抛、怎么返回给前端。

项目里有自定义异常：

```text
AppException
UnauthorizedException
ForbiddenException
NotFoundException
ValidationException
ConflictException
AuthenticationException
AccountLockedException
```

比如：

```py
if not feedback:
    raise NotFoundException("反馈不存在")
```

不要随便：

```py
raise Exception("error")
```

意义：让错误返回格式稳定，前端才能统一处理。

---

### 7.4 `backend/logging-guidelines.md`

作用：告诉 AI 后端日志怎么打。

项目有统一日志配置：

```text
app/core/logging.py
app/middleware/logging_middleware.py
```

它说明：

- 用 `get_logger(__name__)`
- 请求日志由中间件统一记录
- 不要用 `print()`
- 不要记录 token、密码、验证码
- 异常日志要带 `exc_info=True`

意义：方便排查问题，同时避免泄露敏感信息。

---

### 7.5 `backend/quality-guidelines.md`

作用：后端开发完成前的质量检查清单。

它说明：

- 接口必须保持 `/api/v1`
- 正常响应保持 `{ code, message, data }`
- 权限要用 permission service 或显式 ownership 检查
- 改后端要跑相关 pytest
- 改后端真实文件要更新：

```text
project_code/operations-log.md
```

意义：保证后端改动不会破坏接口规范、权限、测试和日志记录。

---

## 8. 我还改了哪些索引？

我更新了：

```text
.trellis/spec/frontend/index.md
.trellis/spec/backend/index.md
```

把里面的状态从：

```text
To fill
```

改成：

```text
Filled
```

意义：告诉后续 AI 和人：这些规范已经填完，不再是空模板。

---

## 9. 我还更新了 task.json 的子任务状态

文件：

```text
.trellis/tasks/00-bootstrap-guidelines/task.json
```

里面原来有三个子任务：

```text
Fill backend guidelines
Fill frontend guidelines
Add code examples
```

我把它们改成：

```text
completed
```

意义：表示这个任务的具体子项已经做完。

但父任务还保持：

```text
status: in_progress
```

原因：Trellis 任务最好等你人工确认后，再执行 finish/archive。

---

## 10. 我还更新了 journal

文件：

```text
.trellis/workspace/liu/journal-1.md
```

作用：记录这次会话做了什么。

这类似一个“工作日志”。

以后你或其他 AI 回来看，可以知道：

- 这次填了哪些规范
- 验证了什么
- 当前任务为什么处于这个状态

---

## 11. 我做了哪些验证？

### 11.1 扫描占位符

我检查 `.trellis/spec/` 里是否还有这些未填模板：

```text
To fill
To be filled
(To be filled by the team)
Replace with your actual structure
```

结果：没有剩余。

说明文档不再是空模板。

---

### 11.2 校验 Trellis 上下文文件

我运行了：

```bash
python ./.trellis/scripts/task.py validate ".trellis/tasks/00-bootstrap-guidelines"
```

结果：通过。

它验证的是：

```text
implement.jsonl
check.jsonl
debug.jsonl
```

这些上下文注入文件格式没问题。

---

## 12. 为什么我用 python 而不是 python3？

你当前机器上：

```bash
python --version
```

能正常运行，结果是：

```text
Python 3.13.9
```

但是：

```bash
python3
```

会指向一个坏路径：

```text
F:\Program Files\python.exe
```

所以我临时用：

```bash
python ./.trellis/scripts/...
```

代替：

```bash
python3 ./.trellis/scripts/...
```

这不是项目代码问题，是你本机 Python 命令别名/路径配置问题。

---

## 13. 这些规范以后怎么帮你？

以后你说：

```text
帮我优化 profile 页面反馈功能
```

AI 应该先判断这是联调任务，因为涉及：

```text
前端 profile 页面
前端 api/profile.ts 或 learning.ts
后端 feedbacks.py
后端 feedback_service.py
后端 schemas/feedback.py
```

然后 AI 会参考这些规范：

```text
frontend/directory-structure.md
frontend/component-guidelines.md
frontend/state-management.md
frontend/type-safety.md
backend/directory-structure.md
backend/database-guidelines.md
backend/error-handling.md
backend/quality-guidelines.md
guides/cross-layer-thinking-guide.md
```

这样它就更容易做到：

- 不把代码放错目录
- 不绕过 `useUserStore()`
- 不乱建 Axios
- 不破坏 `{ code, message, data }`
- 不把数据库查询写进路由
- 不忘记前后端字段对齐
- 不忘记测试和 operations-log

---

## 14. 你作为新手应该怎么学习这些文件？

建议按这个顺序看。

### 第一步：先看总入口

```text
CLAUDE.md
```

重点理解：

- 根目录不是前端项目，也不是后端项目
- 前端在 `UI/`
- 后端在 `project_code/backend/`
- 联调任务要同时看前后端

---

### 第二步：看前端目录规范

```text
.trellis/spec/frontend/directory-structure.md
```

你要搞懂：

- 页面放哪
- 组件放哪
- API 放哪
- Store 放哪
- Composable 放哪

---

### 第三步：看后端目录规范

```text
.trellis/spec/backend/directory-structure.md
```

你要搞懂后端五层：

```text
api → schema → service → model → database
```

---

### 第四步：看和你最常改功能相关的规范

如果你改页面，看：

```text
frontend/component-guidelines.md
frontend/state-management.md
frontend/type-safety.md
```

如果你改接口，看：

```text
backend/error-handling.md
backend/database-guidelines.md
backend/quality-guidelines.md
```

如果你改前后端联调，看：

```text
.trellis/spec/guides/cross-layer-thinking-guide.md
```

---

## 15. 以后你可以怎么指挥 AI？

你可以这样说：

```text
先按 Trellis workflow，读取相关 .trellis/spec 规范，再修改 profile 反馈功能。
```

或者：

```text
这是一个前后端联调任务，请同时检查 UI/src/api、UI/src/views、backend/app/api/v1、backend/app/services、backend/app/schemas。
```

或者：

```text
修改前先告诉我会涉及哪些 spec 文件和代码文件。
```

这样 AI 就会更稳，不容易乱改。

---

## 16. 当前状态总结

当前 Bootstrap Guidelines 文档任务已经基本完成：

```text
前端规范：已填完
后端规范：已填完
索引状态：已更新为 Filled
子任务状态：已 completed
上下文校验：已通过
父任务状态：仍为 in_progress
```

为什么父任务没直接完成？

因为一般 Trellis 流程里，任务最终 `finish/archive` 最好由你确认后再做。

如果你确认这些文档可以作为当前项目规范，下一步可以执行：

```bash
python ./.trellis/scripts/task.py finish
python ./.trellis/scripts/task.py archive 00-bootstrap-guidelines
```

但如果你还想继续学习或调整这些规范，也可以先不 archive。

---

## 17. 最重要的一句话

这次操作的意义是：

> 把“这个项目应该怎么写代码”从零散的 CLAUDE.md 和真实代码里，整理成 AI 能稳定读取、开发者也能学习的规范手册。

它不会直接改变业务功能，但会提高后续所有功能开发、修 bug、联调任务的稳定性。
