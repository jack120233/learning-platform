<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  if (path === '/profile') return '/profile'
  return path
})

const useCompactMainContent = computed(() => route.path === '/profile/messages')

// 未读消息数
const unreadCount = computed(() => userStore.unreadMessageCount)

// 菜单项配置
const menuItems = [
  { index: '/profile', title: '个人信息', icon: 'User' },
  { index: '/profile/password', title: '修改密码', icon: 'Lock' },
  { index: '/profile/records', title: '学习记录', icon: 'Reading' },
  { index: '/profile/messages', title: '消息中心', icon: 'Bell', badge: true },
  { index: '/profile/feedbacks', title: '我的反馈', icon: 'ChatDotRound' },
]

// 需要缓存的页面
const cachedPages = ['ProfileRecords', 'ProfileMessages']
</script>

<template>
  <div class="profile-layout">
    <div class="layout-container">
      <!-- 左侧菜单 -->
      <el-aside class="side-menu" width="220px">
        <div class="menu-header">
          <el-icon :size="24" color="#1890ff"><User /></el-icon>
          <span class="menu-title">个人中心</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          :router="true"
          class="profile-menu"
        >
          <el-menu-item
            v-for="item in menuItems"
            :key="item.index"
            :index="item.index"
          >
            <el-icon>
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.title }}</span>
            <el-badge
              v-if="item.badge && unreadCount > 0"
              :value="unreadCount > 99 ? '99+' : unreadCount"
              class="menu-badge"
            />
          </el-menu-item>
        </el-menu>

        <!-- 反馈入口 -->
        <div class="feedback-entry">
          <el-button type="primary" @click="router.push('/profile/feedbacks')">
            <el-icon><Edit /></el-icon>
            提交反馈
          </el-button>
        </div>
      </el-aside>

      <!-- 右侧内容区 -->
      <el-main class="main-content" :class="{ 'is-compact': useCompactMainContent }">
        <router-view v-slot="{ Component, route: currentRoute }">
          <keep-alive :include="cachedPages">
            <component :is="Component" :key="currentRoute.fullPath" />
          </keep-alive>
        </router-view>
      </el-main>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.profile-layout {
  min-height: calc(100vh - 64px - 200px);
  background: #f5f7fa;
  padding: 24px 0;
}

.layout-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  gap: 24px;
}

.side-menu {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  height: fit-content;
  position: sticky;
  top: 88px;
}

.menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.menu-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.profile-menu {
  border-right: none;
  padding: 8px 0;

  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin: 4px 12px;
    border-radius: 6px;

    &:hover {
      background: #e6f7ff;
    }

    &.is-active {
      background: #e6f7ff;
      color: #1890ff;
      font-weight: 500;
    }
  }
}

.menu-badge {
  margin-left: auto;
  margin-right: 8px;
}

.feedback-entry {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;

  .el-button {
    width: 100%;
  }
}

.main-content {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-height: 600px;
  padding: 24px;
  overflow: visible;

  &.is-compact {
    min-height: auto;
  }
}

// 响应式：平板端以下转为抽屉模式
@media (max-width: 768px) {
  .profile-layout {
    padding: 16px 0;
  }

  .layout-container {
    flex-direction: column;
    padding: 0 16px;
    gap: 16px;
  }

  .side-menu {
    width: 100% !important;
    position: static;
  }

  .menu-header {
    padding: 16px;
  }

  .menu-title {
    font-size: 16px;
  }

  .profile-menu {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    padding: 12px;

    :deep(.el-menu-item) {
      flex: 0 0 auto;
      margin: 0;
      padding: 0 16px;
      height: 40px;
      line-height: 40px;
      font-size: 13px;
    }
  }

  .feedback-entry {
    display: none;
  }

  .main-content {
    min-height: auto;
    padding: 16px;
  }
}

// 小屏幕手机适配
@media (max-width: 480px) {
  .profile-menu {
    justify-content: flex-start;

    :deep(.el-menu-item) {
      flex: 1 1 calc(50% - 4px);
      min-width: calc(50% - 4px);
      max-width: calc(50% - 4px);
      justify-content: center;
      padding: 0 8px;

      span {
        font-size: 12px;
      }
    }
  }
}
</style>
