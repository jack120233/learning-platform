import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

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
    name: 'Profile',
    component: () => import('@/views/profile/ProfilePage.vue'),
    meta: {
      title: '个人中心',
      requiresAuth: true,
    },
  },
  {
    path: '/teacher/courses',
    name: 'TeacherCourses',
    component: () => import('@/views/teacher/CoursesPage.vue'),
    meta: {
      title: '课程管理',
      requiresAuth: true,
      requiresTeacher: true,
    },
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
        component: () => import('@/views/admin/UsersPage.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'announcements',
        name: 'AdminAnnouncements',
        component: () => import('@/views/admin/AnnouncementsPage.vue'),
        meta: { title: '公告管理' },
      },
      {
        path: 'feedbacks',
        name: 'AdminFeedbacks',
        component: () => import('@/views/admin/FeedbacksPage.vue'),
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
  // 设置页面标题
  document.title = `${to.meta.title || '在线学习平台'} - 职业培训课堂`

  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }

  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 检查角色权限（简化处理，实际应该从store获取）
  const userInfoStr = localStorage.getItem('user_info')
  const userInfo = userInfoStr ? JSON.parse(userInfoStr) : null
  const role = userInfo?.role

  if (to.meta.requiresTeacher && role !== 'teacher' && role !== 'admin') {
    next({ name: 'Home' })
    return
  }

  if (to.meta.requiresAdmin && role !== 'admin') {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router