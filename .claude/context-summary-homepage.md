# 首页开发上下文摘要

生成时间：2026-03-24

## 1. 项目概述

### 技术栈
- **核心框架**: Vue 3 (Composition API)
- **开发语言**: TypeScript
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **网络请求**: Axios

### 项目目录结构规划
```
src/
├── api/            # API接口定义
├── assets/         # 静态资源
├── components/     # 全局复用组件
│   ├── layout/     # 布局组件
│   └── common/     # 基础组件
├── router/         # 路由配置
├── store/          # Pinia状态管理
├── utils/          # 工具函数
├── views/          # 业务视图
└── App.vue
```

## 2. 首页组件结构

```
HomePage.vue
├── AppHeader.vue          ← 全局导航栏
│   ├── LogoSection
│   ├── MainNav
│   ├── QuickEntries
│   ├── SearchTrigger
│   └── UserArea
│
├── BannerCarousel.vue     ← Banner轮播
├── SearchFilterBar.vue    ← 搜索筛选
├── CourseListSection.vue  ← 课程列表
├── PaginationBar.vue      ← 分页
└── AppFooter.vue          ← 页脚
```

## 3. 核心数据模型

### 课程卡片
```typescript
interface HomeCourseItem {
  course_id: number
  title: string
  cover_url: string
  summary: string
  teacher_name: string
  published_at: string
}
```

### 分类
```typescript
interface Category {
  category_id: number
  name: string
  parent_id: number | null
  icon_url?: string
  sort_order: number
  is_enabled: boolean
  children?: Category[]
}
```

### Banner
```typescript
interface BannerItem {
  id: number
  image_url: string
  title: string
  link_url: string
  link_type: 'course' | 'announcement' | 'external'
}
```

## 4. 核心API接口

| 接口 | 方法 | 用途 |
|------|------|------|
| /api/v1/courses/homepage | GET | 首页课程列表 |
| /api/v1/courses/search | GET | 课程搜索 |
| /api/v1/categories | GET | 分类列表 |
| /api/v1/announcements | GET | 公告/Banner |
| /api/v1/messages/unread-count | GET | 未读消息数 |

## 5. 响应式布局要求

| 屏幕宽度 | 课程卡片列数 |
|----------|-------------|
| ≥1920px | 5 列 |
| 1440-1919px | 4 列 |
| 1280-1439px | 3 列 |
| <1280px | 2 列 |

## 6. 性能优化要点

- 课程封面懒加载
- 路由懒加载
- 分类数据缓存
- 搜索防抖 300ms
- 骨架屏展示

## 7. 状态管理

### useUserStore
- isLoggedIn: 登录状态
- role: 用户角色
- nickname/avatarUrl: 用户信息
- unreadMessageCount: 未读消息数

### useCategoryStore
- categories: 分类列表
- isLoaded: 加载状态

## 8. 关键交互

- 搜索：关键词搜索 + 历史记录 + 热门词
- 筛选：分类筛选 + 排序切换
- 分页：支持翻页和每页条数
- 导航：登录/未登录态不同展示