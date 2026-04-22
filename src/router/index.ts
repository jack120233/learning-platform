import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/store/user'

const ADMIN_ROUTE_PERMISSIONS = [
  { path: '/admin/users', permissionCode: 'admin.user' },
  { path: '/admin/teacher-audits', permissionCode: 'admin.teacher_audit' },
  { path: '/admin/announcements', permissionCode: 'admin.announcement' },
  { path: '/admin/feedbacks', permissionCode: 'admin.feedback' },
  { path: '/admin/messages', permissionCode: 'admin.message' },
  { path: '/admin/categories', permissionCode: 'admin.category' },
  { path: '/admin/tags', permissionCode: 'admin.tag' },
]

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/home/HomePage.vue'),
    meta: {
      title: '首页',
      public: true,
    },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginPage.vue'),
    meta: {
      title: '登录',
      public: true,
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterPage.vue'),
    meta: {
      title: '注册',
      public: true,
    },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/auth/ForgotPasswordPage.vue'),
    meta: {
      title: '找回密码',
      public: true,
    },
  },
  {
    path: '/courses/:courseId',
    name: 'CourseDetail',
    component: () => import('@/views/course/CourseDetailPage.vue'),
    meta: {
      title: '课程详情',
      public: true,
    },
  },
  {
    path: '/learn/:courseId',
    name: 'Learning',
    component: () => import('@/views/learn/LearningPage.vue'),
    meta: {
      title: '学习中',
      requiresAuth: true,
      hideAppChrome: true,
    },
  },
  {
    path: '/profile',
    component: () => import('@/views/profile/ProfileLayout.vue'),
    meta: {
      title: '个人中心',
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        name: 'Profile',
        component: () => import('@/views/profile/ProfileInfoPage.vue'),
        meta: { title: '个人信息' },
      },
      {
        path: 'password',
        name: 'ProfilePassword',
        component: () => import('@/views/profile/ChangePasswordPage.vue'),
        meta: { title: '修改密码' },
      },
      {
        path: 'records',
        name: 'ProfileRecords',
        component: () => import('@/views/profile/LearningRecordsPage.vue'),
        meta: { title: '学习记录' },
      },
      {
        path: 'messages',
        name: 'ProfileMessages',
        component: () => import('@/views/profile/MessagesPage.vue'),
        meta: { title: '消息中心' },
      },
      {
        path: 'feedbacks',
        name: 'ProfileFeedbacks',
        component: () => import('@/views/profile/MyFeedbacksPage.vue'),
        meta: { title: '我的反馈' },
      },
    ],
  },
  {
    path: '/teacher',
    component: () => import('@/views/teacher/TeacherLayout.vue'),
    meta: {
      requiresAuth: true,
      permissionCode: 'teacher.course',
    },
    children: [
      {
        path: '',
        redirect: '/teacher/courses',
      },
      {
        path: 'courses',
        name: 'TeacherCourses',
        component: () => import('@/views/teacher/CourseListPage.vue'),
        meta: { title: '课程管理' },
      },
      {
        path: 'courses/create',
        name: 'TeacherCourseCreate',
        component: () => import('@/views/teacher/CourseFormPage.vue'),
        meta: { title: '创建课程' },
      },
      {
        path: 'courses/:courseId/edit',
        name: 'TeacherCourseEdit',
        component: () => import('@/views/teacher/CourseFormPage.vue'),
        meta: { title: '编辑课程' },
      },
    ],
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: {
      title: '后台管理',
      requiresAuth: true,
      permissionCode: 'admin',
    },
    children: [
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManagePage.vue'),
        meta: { title: '用户管理', permissionCode: 'admin.user' },
      },
      {
        path: 'teacher-audits',
        name: 'AdminTeacherAudits',
        component: () => import('@/views/admin/TeacherAuditPage.vue'),
        meta: { title: '讲师审核', permissionCode: 'admin.teacher_audit' },
      },
      {
        path: 'announcements',
        name: 'AdminAnnouncements',
        component: () => import('@/views/admin/AnnouncementPage.vue'),
        meta: { title: '公告管理', permissionCode: 'admin.announcement' },
      },
      {
        path: 'feedbacks',
        name: 'AdminFeedbacks',
        component: () => import('@/views/admin/FeedbackManagePage.vue'),
        meta: { title: '反馈管理', permissionCode: 'admin.feedback' },
      },
      {
        path: 'messages',
        name: 'AdminMessages',
        component: () => import('@/views/admin/AdminMessagePage.vue'),
        meta: { title: '系统消息', permissionCode: 'admin.message' },
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/CategoryManagePage.vue'),
        meta: { title: '分类管理', permissionCode: 'admin.category' },
      },
      {
        path: 'tags',
        name: 'AdminTags',
        component: () => import('@/views/admin/TagManagePage.vue'),
        meta: { title: '标签管理', permissionCode: 'admin.tag' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0 }
  },
})

function resolveAdminLandingPath(userStore: ReturnType<typeof useUserStore>) {
  return ADMIN_ROUTE_PERMISSIONS.find(item => userStore.hasPermission(item.permissionCode))?.path || null
}

// 路由守卫
router.beforeEach(async (to) => {
  const userStore = useUserStore()

  // 设置页面标题
  document.title = `${to.meta.title || '在线学习平台'} - 职业培训课堂`

  // 已登录用户访问登录/注册/找回密码页 → 重定向到首页
  if (userStore.isLoggedIn && ['Login', 'Register', 'ForgotPassword'].includes(to.name as string)) {
    return { name: 'Home' }
  }

  // 公开页面直接放行
  if (to.meta.public) {
    return true
  }

  // 需要登录但未登录 → 跳转登录页
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  const requiredPermissionCode = typeof to.meta.permissionCode === 'string' ? to.meta.permissionCode : ''
  if (requiredPermissionCode && !userStore.permissionsLoaded) {
    try {
      await userStore.loadMyPermissions()
    } catch {
      if (!userStore.permissionsLoaded) {
        return { name: 'Home' }
      }
    }
  }

  if (to.path === '/admin') {
    if (!userStore.canAccessAdminCenter) {
      return { name: 'Home' }
    }

    const landingPath = resolveAdminLandingPath(userStore)
    return landingPath || { name: 'Home' }
  }

  if (requiredPermissionCode && !userStore.hasPermission(requiredPermissionCode)) {
    return { name: 'Home' }
  }

  return true
})

export default router
