import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/store/user'

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
      requiresTeacher: true,
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
      requiresAdmin: true,
    },
    children: [
      {
        path: '',
        redirect: '/admin/users',
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManagePage.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'roles',
        name: 'AdminRoles',
        component: () => import('@/views/admin/RolePermissionPage.vue'),
        meta: { title: '角色权限' },
      },
      {
        path: 'announcements',
        name: 'AdminAnnouncements',
        component: () => import('@/views/admin/AnnouncementPage.vue'),
        meta: { title: '公告管理' },
      },
      {
        path: 'feedbacks',
        name: 'AdminFeedbacks',
        component: () => import('@/views/admin/FeedbackManagePage.vue'),
        meta: { title: '反馈管理' },
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

// 路由守卫
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  document.title = `${to.meta.title || '在线学习平台'} - 职业培训课堂`

  // 已登录用户访问登录/注册/找回密码页 → 重定向到首页
  if (userStore.isLoggedIn && ['Login', 'Register', 'ForgotPassword'].includes(to.name as string)) {
    next({ name: 'Home' })
    return
  }

  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }

  // 需要登录但未登录 → 跳转登录页
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 检查角色权限
  if (to.meta.requiresTeacher && !userStore.isTeacher && !userStore.isAdmin) {
    next({ name: 'Home' })
    return
  }

  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router