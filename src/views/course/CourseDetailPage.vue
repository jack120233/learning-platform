<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="course-detail-page">
    <div class="page-container">
      <h1>课程详情</h1>
      <p>课程ID: {{ route.params.courseId }}</p>
      <p class="placeholder-text">课程详情页面开发中...</p>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.course-detail-page {
  padding: 24px 0;
  min-height: calc(100vh - 64px - 200px);
}

.page-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

.placeholder-text {
  color: #666;
  margin-top: 16px;
}
</style>