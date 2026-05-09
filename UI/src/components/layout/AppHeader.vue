<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { fetchUnreadCount } from '@/api/profile'
import UnreadLabelBadge from '@/components/common/UnreadLabelBadge.vue'
import UserIdentity from '@/components/common/UserIdentity.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
// 响应式断点检测（可用于 JS 级别的条件判断）
useBreakpoint()

// 移动端导航抽屉状态
const showMobileNav = ref(false)

const navItems = [
  { label: '职业培训课堂', path: '/' },
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
const messageCenterPath = computed(() => '/profile/messages')

const userDropdownItems = computed(() => {
  const items = [
    { label: '个人中心', path: '/profile', icon: 'User' },
    { label: '我的学习', path: '/profile/records', icon: 'Reading' },
    { label: '消息中心', path: messageCenterPath.value, icon: 'Bell' },
  ]

  if (userStore.canAccessTeacherCenter) {
    items.push({ label: '课程管理', path: '/teacher/courses', icon: 'Notebook' })
  }

  if (userStore.canAccessAdminCenter) {
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

async function syncUnreadCount() {
  if (!userStore.isLoggedIn) {
    userStore.setUnreadCount(0)
    return
  }

  try {
    const response = await fetchUnreadCount()
    userStore.setUnreadCount(response.unread_count)
  } catch (error) {
    // 头部角标同步失败时不阻断页面使用
  }
}

onMounted(() => {
  void syncUnreadCount()
})

watch(() => route.fullPath, () => {
  void syncUnreadCount()
})
</script>

<template>
  <header class="app-header">
    <div class="header-content">
      <!-- 汉堡菜单按钮（移动端显示） -->
      <button class="hamburger-btn" @click="showMobileNav = true">
        <el-icon :size="24"><Menu /></el-icon>
      </button>

      <!-- Logo区域 -->
      <router-link to="/" class="logo-section" custom v-slot="{ navigate }">
        <div class="logo-section" @click="navigate">
          <el-icon :size="32" color="#1890ff"><School /></el-icon>
          <span class="logo-text">职业培训课堂</span>
        </div>
      </router-link>

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
            placeholder="搜索课程"
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
            <div class="auth-actions">
              <el-button class="auth-btn auth-btn--login" @click="router.push('/login')">
                登录
              </el-button>
              <el-button class="auth-btn auth-btn--register" type="primary" @click="router.push('/register')">
                注册
              </el-button>
            </div>
          </template>

          <!-- 已登录 -->
          <template v-else>
            <el-dropdown trigger="click" @command="handleDropdownSelect">
              <div class="user-info">
                <div class="user-avatar-wrap">
                  <el-avatar :size="36" :src="userStore.userInfo.avatarUrl">
                    <el-icon :size="20"><User /></el-icon>
                  </el-avatar>
                  <span
                    v-if="userStore.unreadMessageCount > 0"
                    class="avatar-unread-badge"
                  >
                    {{ userStore.unreadMessageCount > 99 ? '99+' : userStore.unreadMessageCount }}
                  </span>
                </div>
                <UserIdentity
                  class="username"
                  :username="userStore.userInfo.username"
                  :user-id="userStore.userInfo.userId"
                  fallback="用户"
                  compact
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
                    <UnreadLabelBadge
                      v-if="item.path === messageCenterPath"
                      :label="item.label"
                      :count="userStore.unreadMessageCount"
                      tone="light"
                      class="dropdown-message-badge"
                    />
                    <span v-else>{{ item.label }}</span>
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
            <div class="drawer-auth-actions">
              <el-button class="drawer-auth-btn drawer-auth-btn--login" @click="handleMobileNavClick('/login')">
                登录
              </el-button>
              <el-button class="drawer-auth-btn drawer-auth-btn--register" type="primary" @click="handleMobileNavClick('/register')">
                注册
              </el-button>
            </div>
          </template>

          <!-- 已登录 -->
          <template v-else>
            <div class="user-profile" @click="handleMobileNavClick('/profile')">
              <el-avatar :size="40" :src="userStore.userInfo.avatarUrl">
                <el-icon :size="20"><User /></el-icon>
              </el-avatar>
              <div class="user-info-text">
                <UserIdentity
                  class="nickname"
                  :username="userStore.userInfo.username"
                  :user-id="userStore.userInfo.userId"
                  fallback="用户"
                />
                <div class="role-tag">{{ userStore.isTeacher || userStore.isAdmin ? '讲师' : '学生' }}</div>
              </div>
            </div>
            <div class="user-menu">
              <div class="menu-item" @click="handleMobileNavClick('/profile/records')">
                <el-icon><Reading /></el-icon>
                <span>我的学习</span>
              </div>
              <div class="menu-item" @click="handleMobileNavClick(messageCenterPath)">
                <el-icon><Bell /></el-icon>
                <UnreadLabelBadge
                  label="消息中心"
                  :count="userStore.unreadMessageCount"
                  tone="light"
                  class="mobile-message-badge"
                />
              </div>
              <div v-if="userStore.canAccessTeacherCenter" class="menu-item" @click="handleMobileNavClick('/teacher/courses')">
                <el-icon><Notebook /></el-icon>
                <span>课程管理</span>
              </div>
              <div v-if="userStore.canAccessAdminCenter" class="menu-item" @click="handleMobileNavClick('/admin')">
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
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid rgba(219, 234, 254, 0.8);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(12px);
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
    position: relative;
    font-size: 19px;
    font-weight: 800;
    line-height: 1;
    letter-spacing: 0.4px;
    color: #1e293b;

    &::after {
      content: '';
      position: absolute;
      left: 0;
      right: 0;
      bottom: -7px;
      height: 3px;
      border-radius: 999px;
      background: linear-gradient(90deg, #1890ff 0%, rgba(37, 99, 235, 0) 100%);
      opacity: 0.7;
    }
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

.auth-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px;
  background: #f4f8ff;
  border: 1px solid #dbeafe;
  border-radius: 999px;
}

.auth-btn {
  min-width: 68px;
  height: 34px;
  margin-left: 0 !important;
  border-radius: 999px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.auth-btn--login {
  border-color: transparent;
  background: transparent;
  color: #2563eb;

  &:hover,
  &:focus {
    border-color: #bfdbfe;
    background: #fff;
    color: #1d4ed8;
  }
}

.auth-btn--register {
  border: none;
  background: linear-gradient(135deg, #1890ff 0%, #2563eb 100%);
  box-shadow: 0 8px 18px rgba(24, 144, 255, 0.25);

  &:hover,
  &:focus {
    background: linear-gradient(135deg, #40a9ff 0%, #1d4ed8 100%);
    box-shadow: 0 10px 22px rgba(24, 144, 255, 0.32);
  }
}

.user-info {
  position: relative;
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
    max-width: 150px;
    color: #333;
    font-size: 14px;
  }
  .user-avatar-wrap {
    position: relative;
    display: inline-flex;
    flex-shrink: 0;
  }

  .avatar-unread-badge {
    position: absolute;
    top: -6px;
    right: -8px;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    background: linear-gradient(135deg, #ff5a5f 0%, #f5222d 100%);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    line-height: 1;
    border: 2px solid #fff;
    box-shadow: 0 6px 14px rgba(245, 34, 45, 0.2);
  }
}

.dropdown-message-badge,
.mobile-message-badge {
  margin-left: 0;
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
    color: #1e293b;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.3px;
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

  .drawer-auth-actions {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
    background: #f4f8ff;
    border: 1px solid #dbeafe;
    border-radius: 14px;
  }

  .drawer-auth-btn {
    width: 100%;
    height: 40px;
    margin-left: 0 !important;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 600;
  }

  .drawer-auth-btn--login {
    border-color: #bfdbfe;
    background: #fff;
    color: #2563eb;
  }

  .drawer-auth-btn--register {
    border: none;
    background: linear-gradient(135deg, #1890ff 0%, #2563eb 100%);
    box-shadow: 0 8px 18px rgba(24, 144, 255, 0.22);
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
        max-width: 180px;
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

      .mobile-message-badge {
        margin-left: 0;
        font-size: inherit;
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

@media (max-width: 480px) {
  .search-box {
    display: none;
  }
}
</style>
