# 首页课程门户页 - 实施计划

生成时间：2026-03-24
推荐方案：URL-Driven State（URL参数驱动状态）

---

## 1. 项目结构

```text
src/
├── api/
│   ├── index.ts            # Axios实例 & 拦截器
│   ├── auth.ts             # 登录、登出、刷新Token
│   ├── course.ts           # 课程列表、搜索
│   └── category.ts         # 分类树
├── components/
│   ├── layout/
│   │   ├── AppHeader.vue   # 全局导航栏
│   │   └── AppFooter.vue   # 全局页脚
│   └── common/
│       └── CourseCard.vue  # 课程卡片组件
├── composables/
│   ├── useUrlState.ts      # URL参数同步
│   └── useDebounce.ts      # 防抖
├── store/
│   ├── user.ts             # 用户状态
│   └── category.ts         # 分类缓存
├── views/
│   └── home/
│       ├── HomePage.vue    # 首页容器
│       └── components/
│           ├── BannerCarousel.vue
│           ├── SearchFilterBar.vue
│           ├── CourseListSection.vue
│           └── PaginationBar.vue
├── router/
│   └── index.ts
├── App.vue
└── main.ts
```

---

## 2. 实施阶段

### P1: 项目搭建（基础设施）
- [ ] 初始化 Vue 3 + Vite + TypeScript 项目
- [ ] 配置 Element Plus、Pinia、Vue Router
- [ ] 实现 Axios 实例和拦截器（Token自动刷新）
- [ ] 配置环境变量（API Base URL）

### P2: 布局组件
- [ ] AppHeader - 全局导航栏
  - Logo + 主导航菜单
  - 搜索入口
  - 用户区域（登录/注册 或 头像下拉）
- [ ] AppFooter - 全局页脚
  - 底部链接、联系信息、版权声明

### P3: 核心逻辑
- [ ] Pinia Store：useUserStore、useCategoryStore
- [ ] URL状态同步：useUrlState composable
- [ ] API接口封装：
  - GET /api/v1/courses/homepage
  - GET /api/v1/courses/search
  - GET /api/v1/categories

### P4: 首页UI开发
- [ ] BannerCarousel - Banner轮播区
- [ ] SearchFilterBar - 搜索筛选栏
  - 搜索框（防抖300ms）
  - 搜索历史（localStorage）
  - 分类筛选
  - 排序切换
- [ ] CourseListSection - 课程列表区
  - 骨架屏加载
  - 课程卡片网格（CSS Grid响应式）
  - 空状态、错误状态
- [ ] PaginationBar - 分页区

### P5: 优化完善
- [ ] 响应式布局适配（2-5列）
- [ ] 图片懒加载
- [ ] 性能优化
- [ ] 样式细节调整

---

## 3. 关键实现

### 3.1 Axios Token自动刷新
```typescript
// 拦截器处理401，自动刷新Token后重试
service.interceptors.response.use(
  response => response.data,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      await userStore.handleRefreshToken();
      return service(error.config);
    }
    return Promise.reject(error);
  }
);
```

### 3.2 CSS Grid响应式课程网格
```css
.course-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}
```

### 3.3 URL参数同步
```typescript
// keyword, category_id, page 同步到URL
const syncStateToUrl = (params) => {
  router.push({ query: { ...route.query, ...params } });
};
```

---

## 4. 组件接口定义

### CourseCard Props
```typescript
interface CourseCardProps {
  courseId: number
  title: string
  coverUrl: string
  summary: string
  teacherName: string
  publishedAt: string
}
```

### HomePage State
```typescript
interface HomePageState {
  courseList: HomeCourseItem[]
  isLoading: boolean
  isError: boolean
  currentPage: number
  pageSize: number
  totalCount: number
  searchKeyword: string
  selectedCategoryId: number | null
  sortBy: 'latest' | 'popular'
}
```

---

## 5. 验收标准

- [ ] 首页可正常加载课程列表
- [ ] 搜索功能正常（防抖、历史记录）
- [ ] 分类筛选和排序切换正常
- [ ] 分页功能正常
- [ ] 响应式布局适配（1280px-1920px）
- [ ] 骨架屏、空状态、错误状态展示正确
- [ ] Token过期自动刷新
- [ ] 权限控制正确（学员/讲师/管理员菜单区分）