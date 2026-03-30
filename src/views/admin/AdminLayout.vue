<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, Key, Bell, ChatDotRound, Back, Menu, Close } from '@element-plus/icons-vue'
import { useBreakpoint } from '@/composables/useBreakpoint'

const route = useRoute()
const router = useRouter()
const { isMobile, isTablet } = useBreakpoint()

// 移动端抽屉状态
const showMobileMenu = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 菜单项配置
const menuItems = [
  { index: '/admin/users', title: '用户管理', icon: User },
  { index: '/admin/roles', title: '角色权限', icon: Key },
  { index: '/admin/announcements', title: '公告管理', icon: Bell },
  { index: '/admin/feedbacks', title: '反馈管理', icon: ChatDotRound },
]

// 导航点击后关闭抽屉
const handleMenuClick = (path?: string) => {
  if (path) {
    router.push(path)
  }
  showMobileMenu.value = false
}
</script>

<template>
  <div class="admin-layout">
    <el-container>
      <!-- 移动端顶部栏 -->
      <header v-if="isMobile || isTablet" class="mobile-header">
        <button class="hamburger-btn" @click="showMobileMenu = true">
          <el-icon :size="24"><Menu /></el-icon>
        </button>
        <div class="header-title">
          <el-icon :size="20" color="#1890ff"><Key /></el-icon>
          <span>管理后台</span>
        </div>
        <div class="header-placeholder"></div>
      </header>

      <!-- PC端侧边菜单 -->
      <el-aside v-if="!isMobile && !isTablet" width="220px" class="side-menu">
        <div class="menu-header">
          <el-icon :size="24" color="#1890ff"><Key /></el-icon>
          <span class="menu-title">管理后台</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          :router="true"
          class="admin-menu"
        >
          <el-menu-item
            v-for="item in menuItems"
            :key="item.index"
            :index="item.index"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </el-menu>

        <div class="menu-footer">
          <el-button text @click="router.push('/')">
            <el-icon><Back /></el-icon>
            返回前台
          </el-button>
        </div>
      </el-aside>

      <!-- 移动端抽屉菜单 -->
      <el-drawer
        v-model="showMobileMenu"
        direction="ltr"
        :size="280"
        :with-header="false"
        class="mobile-menu-drawer"
      >
        <div class="drawer-content">
          <div class="drawer-header">
            <div class="drawer-logo">
              <el-icon :size="24" color="#1890ff"><Key /></el-icon>
              <span>管理后台</span>
            </div>
            <el-button text circle @click="showMobileMenu = false">
              <el-icon :size="20"><Close /></el-icon>
            </el-button>
          </div>

          <nav class="drawer-nav">
            <div
              v-for="item in menuItems"
              :key="item.index"
              class="nav-item"
              :class="{ active: activeMenu === item.index }"
              @click="handleMenuClick(item.index)"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </div>
          </nav>

          <div class="drawer-footer">
            <el-button text @click="handleMenuClick('/')">
              <el-icon><Back /></el-icon>
              返回前台
            </el-button>
          </div>
        </div>
      </el-drawer>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<style lang="scss" scoped>

.admin-layout {
  min-height: calc(100vh - 64px);

  .el-container {
    min-height: inherit;
    flex-direction: column;

    @media (min-width: $breakpoint-lg) {
      flex-direction: row;
    }
  }
}

// 移动端顶部栏
.mobile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 56px;
  background: #333;
  position: sticky;
  top: 64px;
  z-index: 10;

  .hamburger-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border: none;
    background: transparent;
    cursor: pointer;
    border-radius: 8px;
    color: #fff;
    transition: background-color 0.2s;

    &:hover {
      background-color: #444;
    }
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
  }

  .header-placeholder {
    width: 40px;
  }
}

.side-menu {
  background: #333;
  min-height: inherit;
  display: flex;
  flex-direction: column;

  .menu-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 20px 16px;
    border-bottom: 1px solid #444;
  }

  .menu-title {
    font-size: 18px;
    font-weight: 600;
    color: #fff;
  }
}

.admin-menu {
  flex: 1;
  border-right: none;
  background: transparent;

  :deep(.el-menu-item) {
    color: #fff;
    height: 48px;
    line-height: 48px;
    margin: 4px 12px;
    border-radius: $radius-sm;

    &:hover {
      background: #444;
    }

    &.is-active {
      background: $primary-color;
    }
  }
}

.menu-footer {
  padding: 16px 20px;
  border-top: 1px solid #444;

  .el-button {
    color: #fff;

    &:hover {
      color: $primary-color;
    }
  }
}

.main-content {
  background: $bg-color;
  padding: 24px;
  flex: 1;

  @media (max-width: $breakpoint-lg) {
    padding: 16px;
  }
}

// 移动端抽屉样式
.mobile-menu-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
  }
}

.drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #333;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #444;

  .drawer-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
  }

  .el-button {
    color: #fff;

    &:hover {
      color: $primary-color;
    }
  }
}

.drawer-nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;

  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 20px;
    font-size: 15px;
    color: #fff;
    cursor: pointer;
    transition: all 0.2s;
    border-left: 3px solid transparent;

    &:hover {
      background-color: #444;
    }

    &.active {
      background-color: $primary-color;
      border-left-color: $primary-color;
    }
  }
}

.drawer-footer {
  padding: 16px 20px;
  border-top: 1px solid #444;

  .el-button {
    color: #fff;

    &:hover {
      color: $primary-color;
    }
  }
}
</style>