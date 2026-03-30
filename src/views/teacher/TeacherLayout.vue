<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VideoPlay, Notebook, Back, Menu, Close } from '@element-plus/icons-vue'
import { useBreakpoint } from '@/composables/useBreakpoint'

const route = useRoute()
const router = useRouter()
const { isMobile, isTablet } = useBreakpoint()

// 移动端抽屉状态
const showMobileMenu = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/teacher/courses')) return '/teacher/courses'
  return path
})

// 导航点击后关闭抽屉
const handleMenuClick = (path?: string) => {
  if (path) {
    router.push(path)
  }
  showMobileMenu.value = false
}
</script>

<template>
  <div class="teacher-layout">
    <el-container>
      <!-- 移动端顶部栏 -->
      <header v-if="isMobile || isTablet" class="mobile-header">
        <button class="hamburger-btn" @click="showMobileMenu = true">
          <el-icon :size="24"><Menu /></el-icon>
        </button>
        <div class="header-title">
          <el-icon :size="20" color="#1890ff"><VideoPlay /></el-icon>
          <span>讲师工作台</span>
        </div>
        <div class="header-placeholder"></div>
      </header>

      <!-- PC端侧边菜单 -->
      <el-aside v-if="!isMobile && !isTablet" width="220px" class="side-menu">
        <div class="menu-header">
          <el-icon :size="24" color="#1890ff"><VideoPlay /></el-icon>
          <span class="menu-title">讲师工作台</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          :router="true"
          class="teacher-menu"
        >
          <el-menu-item index="/teacher/courses">
            <el-icon><Notebook /></el-icon>
            <span>课程管理</span>
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
              <el-icon :size="24" color="#1890ff"><VideoPlay /></el-icon>
              <span>讲师工作台</span>
            </div>
            <el-button text circle @click="showMobileMenu = false">
              <el-icon :size="20"><Close /></el-icon>
            </el-button>
          </div>

          <nav class="drawer-nav">
            <div
              class="nav-item"
              :class="{ active: activeMenu === '/teacher/courses' }"
              @click="handleMenuClick('/teacher/courses')"
            >
              <el-icon><Notebook /></el-icon>
              <span>课程管理</span>
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

.teacher-layout {
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
  background: #fff;
  border-bottom: 1px solid $border-color-light;
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
    transition: background-color 0.2s;

    &:hover {
      background-color: #f5f7fa;
    }
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }

  .header-placeholder {
    width: 40px;
  }
}

.side-menu {
  background: #fff;
  border-right: 1px solid $border-color-light;
  min-height: inherit;
  display: flex;
  flex-direction: column;

  .menu-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 20px 16px;
    border-bottom: 1px solid $border-color-light;
  }

  .menu-title {
    font-size: 18px;
    font-weight: 600;
    color: $text-primary;
  }
}

.teacher-menu {
  flex: 1;
  border-right: none;
  padding: 8px 0;

  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin: 4px 12px;
    border-radius: $radius-sm;

    &:hover {
      background: #e6f7ff;
    }

    &.is-active {
      background: #e6f7ff;
      color: $primary-color;
      font-weight: 500;
    }
  }
}

.menu-footer {
  padding: 16px 20px;
  border-top: 1px solid $border-color-light;
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
  background-color: #fff;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid $border-color-light;

  .drawer-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
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
    color: $text-primary;
    cursor: pointer;
    transition: all 0.2s;
    border-left: 3px solid transparent;

    &:hover {
      background-color: #f5f7fa;
    }

    &.active {
      color: $primary-color;
      background-color: #e6f7ff;
      border-left-color: $primary-color;
    }
  }
}

.drawer-footer {
  padding: 16px 20px;
  border-top: 1px solid $border-color-light;
}
</style>