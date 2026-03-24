<script setup lang="ts">
</script>

<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="220px">
        <el-menu
          router
          default-active="/admin/users"
          background-color="#333"
          text-color="#fff"
          active-text-color="#1890ff"
        >
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/announcements">
            <el-icon><Bell /></el-icon>
            <span>公告管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/feedbacks">
            <el-icon><ChatLineSquare /></el-icon>
            <span>反馈管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
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
  }

  .el-aside {
    background-color: #333;
    min-height: inherit;

    .el-menu {
      border-right: none;
      height: 100%;

      .el-menu-item {
        &:hover {
          background-color: #444;
        }

        &.is-active {
          background-color: #1890ff;
        }
      }
    }
  }

  .el-main {
    background-color: #f5f7fa;
    padding: 24px;
  }
}
</style>