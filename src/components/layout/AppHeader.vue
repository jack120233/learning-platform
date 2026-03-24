<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

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
  } catch {
    // 取消操作
  }
}
</script>

<template>
  <header class="app-header">
    <div class="header-content">
      <!-- Logo区域 -->
      <div class="logo-section" @click="router.push('/')">
        <el-icon :size="32" color="#1890ff"><School /></el-icon>
        <span class="logo-text">职业培训课堂</span>
      </div>

      <!-- 主导航菜单 -->
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

@media (max-width: 1280px) {
  .main-nav {
    display: none;
  }

  .search-box {
    width: 180px;
  }
}
</style>