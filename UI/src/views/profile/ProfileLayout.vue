<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { fetchUnreadCount } from '@/api/profile'
import UnreadLabelBadge from '@/components/common/UnreadLabelBadge.vue'

const route = useRoute()
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
const menuItems = computed(() => {
  const items = [
    { index: '/profile', title: '个人信息', icon: 'User' },
    { index: '/profile/password', title: '修改密码', icon: 'Lock' },
    { index: '/profile/records', title: '学习统计', icon: 'Reading' },
    { index: '/profile/messages', title: '消息中心', icon: 'Bell', badge: true },
  ]

  if (!userStore.isAdmin) {
    items.push({ index: '/profile/feedbacks', title: '我的反馈', icon: 'ChatDotRound' })
  }

  return items
})

// 需要缓存的页面
const cachedPages = ['ProfileRecords', 'ProfileMessages']

async function syncUnreadCount() {
  if (!userStore.isLoggedIn) {
    userStore.setUnreadCount(0)
    return
  }

  try {
    const response = await fetchUnreadCount()
    userStore.setUnreadCount(response.unread_count)
  } catch (error) {
    // 保持布局正常，忽略角标同步失败
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
            <UnreadLabelBadge
              v-if="item.badge"
              :label="item.title"
              :count="unreadCount"
              tone="light"
              class="menu-item-badge"
            />
            <span v-else>{{ item.title }}</span>
          </el-menu-item>
        </el-menu>

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

.menu-item-badge {
  margin-left: 2px;
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

      .menu-item-badge {
        margin-left: 0;
      }
    }
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
