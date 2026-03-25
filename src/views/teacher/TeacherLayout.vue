<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VideoPlay, Notebook, Back } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/teacher/courses')) return '/teacher/courses'
  return path
})
</script>

<template>
  <div class="teacher-layout">
    <el-container>
      <!-- 侧边菜单 -->
      <el-aside width="220px" class="side-menu">
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

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

.teacher-layout {
  min-height: calc(100vh - 64px);

  .el-container {
    min-height: inherit;
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
}
</style>