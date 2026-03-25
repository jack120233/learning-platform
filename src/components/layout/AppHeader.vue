<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { useBreakpoint } from '@/composables/useBreakpoint'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
// 响应式断点检测（可用于 JS 级别的条件判断）
useBreakpoint()

// 移动端导航抽屉状态
const showMobileNav = ref(false)

// 导航菜单
const navItems = [
  { label: '首页', path: '/' },
  { label: '职业培训课堂', path: '/courses' },
  { label: '考培活动报名', path: '/activities' },
  { label: '职业技能竞赛', path: '/competitions' },
  { label: '师资培训', path: '/teacher-training' },
  { label: '考试考核中心', path: '/exams' },
]

// 搜索关键词
const searchKeyword = ref('')

// 搜索处理
const handleSearch = () => {
  if (!searchKeyword.value.trim()) return
  router.push({
    path: '/',
    query: { keyword: searchKeyword.value.trim() },
  })
}

// 用户下拉菜单
const userDropdownItems = computed(() => {
  const items = [
    { label: '个人中心', path: '/profile', icon: 'User' },
    { label: '我的学习', path: '/profile/records', icon: 'Reading' },
    { label: '消息中心', path: '/profile/messages', icon: 'Bell' },
  ]

  if (userStore.isTeacher) {
    items.push({ label: '课程管理', path: '/teacher/courses', icon: 'Notebook' })
  }

  if (userStore.isAdmin) {
    items.push({ label: '后台管理', path: '/admin', icon: 'Setting' })
  }

  return items
})

// 处理下拉菜单点击
const handleDropdownSelect = (path: string) => {
  router.push(path)
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
    showMobileNav.value = false
  } catch {
    // 取消操作
  }
}

// 移动端导航点击
const handleMobileNavClick = (path: string) => {
  router.push(path)
  showMobileNav.value = false
}
</script>

<template>
  <header class="app-header">
    <div class="header-content">
      <!-- 汉堡菜单按钮（移动端显示） -->
      <button class="hamburger-btn" @click="showMobileNav = true">
        <el-icon :size="24"><Menu /></el-icon>
      </button>

      <!-- Logo区域 -->
      <div class="logo-section" @click="router.push('/')">
        <el-icon :size="32" color="#1890ff"><School /></el-icon>
        <span class="logo-text">职业培训课堂</span>
      </div>

      <!-- 主导航菜单（PC端显示） -->
      <nav class="main-nav">
        <el-menu
          mode="horizontal"
          :ellipsis="false"
          :default-active="$route.path"
          router
        >
          <el-menu-item
            v-for="item in navItems"
            :key="item.path"
            :index="item.path"
          >
            {{ item.label }}
          </el-menu-item>
        </el-menu>
      </nav>

      <!-- 右侧区域 -->
      <div class="header-right">
        <!-- 搜索框 -->
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索课程、讲师"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #suffix>
              <el-icon class="search-icon" @click="handleSearch"><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <!-- 用户区域 -->
        <div class="user-area">
          <!-- 未登录 -->
          <template v-if="!userStore.isLoggedIn">
            <el-button type="primary" text @click="router.push('/login')">
              登录
            </el-button>
            <el-button type="primary" @click="router.push('/register')">
              注册
            </el-button>
          </template>

          <!-- 已登录 -->
          <template v-else>
            <el-dropdown trigger="click" @command="handleDropdownSelect">
              <div class="user-info">
                <el-avatar :size="36" :src="userStore.userInfo.avatarUrl">
                  <el-icon :size="20"><User /></el-icon>
                </el-avatar>
                <span class="username">{{ userStore.userInfo.nickname || userStore.userInfo.username }}</span>
                <el-badge
                  v-if="userStore.unreadMessageCount > 0"
                  :value="userStore.unreadMessageCount"
                  :max="99"
                  class="message-badge"
                />
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="item in userDropdownItems"
                    :key="item.path"
                    :command="item.path"
                  >
                    <el-icon><component :is="item.icon" /></el-icon>
                    {{ item.label }}
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </div>
    </div>

    <!-- 移动端导航抽屉 -->
    <el-drawer
      v-model="showMobileNav"
      direction="ltr"
      :size="280"
      :with-header="false"
      class="mobile-nav-drawer"
    >
      <div class="drawer-content">
        <!-- 抽屉头部 -->
        <div class="drawer-header">
          <div class="drawer-logo">
            <el-icon :size="28" color="#1890ff"><School /></el-icon>
            <span>职业培训课堂</span>
          </div>
          <el-button text circle @click="showMobileNav = false">
            <el-icon :size="20"><Close /></el-icon>
          </el-button>
        </div>

        <!-- 导航菜单 -->
        <nav class="drawer-nav">
          <div
            v-for="item in navItems"
            :key="item.path"
            class="nav-item"
            :class="{ active: route.path === item.path }"
            @click="handleMobileNavClick(item.path)"
          >
            {{ item.label }}
          </div>
        </nav>

        <!-- 用户操作区 -->
        <div class="drawer-footer">
          <!-- 未登录 -->
          <template v-if="!userStore.isLoggedIn">
            <el-button type="primary" block @click="handleMobileNavClick('/login')">
              登录
            </el-button>
            <el-button block @click="handleMobileNavClick('/register')">
              注册
            </el-button>
          </template>

          <!-- 已登录 -->
          <template v-else>
            <div class="user-profile" @click="handleMobileNavClick('/profile')">
              <el-avatar :size="40" :src="userStore.userInfo.avatarUrl">
                <el-icon :size="20"><User /></el-icon>
              </el-avatar>
              <div class="user-info-text">
                <div class="nickname">{{ userStore.userInfo.nickname || userStore.userInfo.username }}</div>
                <div class="role-tag">{{ userStore.isAdmin ? '管理员' : userStore.isTeacher ? '讲师' : '学员' }}</div>
              </div>
            </div>
            <div class="user-menu">
              <div class="menu-item" @click="handleMobileNavClick('/profile/records')">
                <el-icon><Reading /></el-icon>
                <span>我的学习</span>
              </div>
              <div class="menu-item" @click="handleMobileNavClick('/profile/messages')">
                <el-icon><Bell /></el-icon>
                <span>消息中心</span>
                <el-badge v-if="userStore.unreadMessageCount > 0" :value="userStore.unreadMessageCount" :max="99" />
              </div>
              <div v-if="userStore.isTeacher" class="menu-item" @click="handleMobileNavClick('/teacher/courses')">
                <el-icon><Notebook /></el-icon>
                <span>课程管理</span>
              </div>
              <div v-if="userStore.isAdmin" class="menu-item" @click="handleMobileNavClick('/admin')">
                <el-icon><Setting /></el-icon>
                <span>后台管理</span>
              </div>
            </div>
            <el-button type="danger" text @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-button>
          </template>
        </div>
      </div>
    </el-drawer>
  </header>
</template>

<style lang="scss" scoped>
.app-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex-shrink: 0;

  .logo-text {
    font-size: 18px;
    font-weight: 600;
    color: #333;
  }
}

.main-nav {
  flex: 1;

  :deep(.el-menu) {
    background-color: transparent;

    .el-menu-item {
      font-size: 14px;

      &:hover {
        background-color: #f5f7fa;
      }

      &.is-active {
        color: #1890ff;
        border-bottom-color: #1890ff;
      }
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.search-box {
  width: 240px;

  .search-icon {
    cursor: pointer;
    color: #999;

    &:hover {
      color: #1890ff;
    }
  }
}

.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background-color 0.2s;

  &:hover {
    background-color: #f5f7fa;
  }

  .username {
    font-size: 14px;
    color: #333;
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.message-badge {
  position: absolute;
  top: -4px;
  right: -4px;
}

// 汉堡菜单按钮（移动端）
.hamburger-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 8px;
  transition: background-color 0.2s;
  flex-shrink: 0;

  &:hover {
    background-color: #f5f7fa;
  }

  &:active {
    background-color: #e8e8e8;
  }
}

// 移动端导航抽屉样式
.mobile-nav-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
  }
}

.drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;

  .drawer-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 16px;
    font-weight: 600;
    color: #333;
  }
}

.drawer-nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;

  .nav-item {
    padding: 14px 20px;
    font-size: 15px;
    color: #333;
    cursor: pointer;
    transition: all 0.2s;
    border-left: 3px solid transparent;

    &:hover {
      background-color: #f5f7fa;
    }

    &.active {
      color: #1890ff;
      background-color: #e6f7ff;
      border-left-color: #1890ff;
    }
  }
}

.drawer-footer {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  gap: 12px;

  // 按钮样式统一
  .el-button {
    width: 100%;
    height: 40px;
    font-size: 14px;
  }

  .user-profile {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background-color: #f5f7fa;
    border-radius: 8px;
    cursor: pointer;

    .user-info-text {
      .nickname {
        font-size: 15px;
        font-weight: 500;
        color: #333;
      }

      .role-tag {
        font-size: 12px;
        color: #999;
        margin-top: 2px;
      }
    }
  }

  .user-menu {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .menu-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px;
      font-size: 14px;
      color: #666;
      cursor: pointer;
      border-radius: 6px;
      transition: all 0.2s;

      &:hover {
        background-color: #f5f7fa;
        color: #1890ff;
      }

      .el-badge {
        margin-left: auto;
      }
    }
  }
}

@media (max-width: 1280px) {
  .main-nav {
    display: none;
  }

  .hamburger-btn {
    display: flex;
  }

  .search-box {
    width: 180px;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
    gap: 12px;
  }

  .logo-section .logo-text {
    display: none;
  }

  .search-box {
    width: 140px;
  }

  .user-info {
    padding: 2px 4px;
    
    .username {
      display: none;
    }
  }
}
</style>