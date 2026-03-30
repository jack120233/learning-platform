# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

在线教育学习视频播放平台前端项目，支持课程浏览、视频学习、进度追踪等功能。包含学员、讲师、管理员三种角色。

## 开发命令

```bash
# 安装依赖
npm install

# 启动开发服务器（端口 3000）
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 技术栈

- **框架**: Vue 3 (Composition API + `<script setup>`)
- **语言**: TypeScript
- **构建工具**: Vite 8
- **UI 组件库**: Element Plus（中文语言包已配置）
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **样式**: SCSS + Element Plus 主题变量

## 项目结构

```
src/
├── api/           # API 接口层
│   ├── index.ts   # Axios 实例配置、拦截器、通用类型
│   ├── course.ts  # 课程相关接口
│   └── category.ts
├── assets/        # 静态资源
│   └── styles/    # 全局样式
│       ├── main.scss        # 全局样式入口
│       └── _variables.scss  # SCSS 变量定义
├── components/    # 公共组件
│   ├── layout/    # 布局组件 (AppHeader, AppFooter)
│   └── common/    # 通用业务组件 (CourseCard)
├── router/        # 路由配置（含路由守卫）
├── store/         # Pinia 状态管理
├── views/         # 页面视图
│   ├── home/      # 首页
│   ├── auth/      # 登录/注册
│   ├── course/    # 课程详情
│   ├── learn/     # 沉浸式学习页
│   ├── profile/   # 个人中心
│   ├── teacher/   # 讲师端
│   └── admin/     # 管理后台
├── App.vue
└── main.ts
```

## 架构要点

### API 层设计

- `src/api/index.ts` 导出 Axios 实例和通用类型 (`ApiResponse`, `PaginatedData`)
- 请求拦截器自动注入 JWT Token
- 响应拦截器处理 Token 过期刷新（401 自动刷新机制）
- 各模块 API 独立文件，导出类型化的请求函数

### 路由权限控制

路由 meta 字段定义权限：
- `public: true` - 公开页面
- `requiresAuth: true` - 需要登录
- `requiresTeacher: true` - 需要讲师权限
- `requiresAdmin: true` - 需要管理员权限

路由守卫在 `src/router/index.ts` 中实现，统一检查 `useUserStore()` 提供的 `isLoggedIn`、`isTeacher`、`isAdmin` 计算属性。

### 状态管理

Pinia Store 使用 Composition API 风格：
- `useUserStore` - 用户认证状态、Token 管理
- `useCategoryStore` - 分类数据缓存

Store 在初始化时自动从 localStorage 恢复持久化状态。

### 组件自动导入

Vite 配置了 `unplugin-auto-import` 和 `unplugin-vue-components`：
- Vue API (`ref`, `computed`, `watch` 等) 无需手动导入
- Element Plus 组件按需自动注册
- 类型定义生成在 `src/auto-imports.d.ts` 和 `src/components.d.ts`

## 开发约定

### 认证状态管理规范（最高优先级）

> ⚠️ **强制要求**：本项目必须遵循单一数据源原则，所有认证状态统一由 Pinia Store 管理。

**核心原则**：
- **禁止**业务代码直接读取 `localStorage`（唯一例外：API 请求拦截器注入 Token）
- **必须**统一通过 `useUserStore()` 获取认证状态
- **必须**使用 Store 提供的计算属性判断权限

**Store 提供的计算属性**：
- `isLoggedIn` - 是否已登录（accessToken + userId 双重校验）
- `isTeacher` - 是否讲师角色
- `isAdmin` - 是否管理员角色
- `userInfo` - 用户完整信息对象

**正确示例**：
```ts
// ✅ 路由守卫 - 使用 Store
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  if (userStore.isLoggedIn) { ... }
  if (to.meta.requiresAuth && !userStore.isLoggedIn) { ... }
})

// ✅ 组件 - 使用 Store
const userStore = useUserStore()
if (userStore.isTeacher) { ... }
```

**禁止示例**：
```ts
// ❌ 禁止直接读 localStorage
const token = localStorage.getItem('access_token')
const userInfo = JSON.parse(localStorage.getItem('user_info'))
```

详细规范见 `docs/login-auth-issue-review.md` 第九章节。

### 样式规范

- 全局 SCSS 变量定义在 `_variables.scss`
- 组件样式使用 `<style lang="scss" scoped>`
- 页面容器类名：`.page-container`（max-width: 1440px）
- 文字省略工具类：`.text-ellipsis`, `.text-ellipsis-2`

### 命名约定

- 组件文件：PascalCase (如 `CourseCard.vue`)
- 视图文件：PascalCase + Page 后缀 (如 `HomePage.vue`)
- API 函数：`fetch` / `get` / `post` 前缀 (如 `fetchHomepageCourses`)
- Store：`use` 前缀 + Store 后缀 (如 `useUserStore`)

### 响应式与移动端适配

- 要求采用响应式设计，必须同时保证 PC 和移动端网页的适配。
- 默认编写并保留 PC 端样式，对于移动端等小屏幕设备，必须使用 CSS 媒体查询（如 `@media (max-width: 768px)`）进行样式调整，例如缩减各处的页面外边距与内边距、修改布局排列方式或隐藏次要操作元素。
- 在后续开发新页面和组件时，都要遵循上述多端适配习惯，不能出现小屏幕横向溢出问题。

### 类型定义

- API 响应类型与接口函数同文件定义
- 接口命名：`XxxParams`, `XxxItem`, `XxxResponse`
- Store 类型在 Store 文件内定义

## API 基础信息

- 基础路径：`/api/v1`（开发环境代理到 `http://localhost:8000`）
- 认证方式：JWT Bearer Token
- 响应格式：`{ code: number, message: string, data: T }`
- 分页格式：`{ items: T[], total: number, page: number, page_size: number, total_pages: number }`

详细接口文档见 `5.接口文档.md`。