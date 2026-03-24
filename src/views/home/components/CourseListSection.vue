<script setup lang="ts">
import CourseCard from '@/components/common/CourseCard.vue'
import type { CourseBaseItem } from '@/api/course'

interface Props {
  courses: CourseBaseItem[]
  loading: boolean
  error: boolean
}

defineProps<Props>()

// 骨架屏数量
const skeletonCount = 8
</script>

<template>
  <div class="course-list-section">
    <!-- 加载中 -->
    <template v-if="loading">
      <div class="skeleton-grid">
        <div v-for="i in skeletonCount" :key="i" class="skeleton-card">
          <el-skeleton animated>
            <template #template>
              <el-skeleton-item variant="image" style="width: 100%; height: 160px" />
              <div style="padding: 14px">
                <el-skeleton-item variant="h3" style="width: 80%" />
                <el-skeleton-item variant="text" style="margin-top: 8px" />
                <el-skeleton-item variant="text" style="width: 60%; margin-top: 8px" />
              </div>
            </template>
          </el-skeleton>
        </div>
      </div>
    </template>

    <!-- 错误状态 -->
    <template v-else-if="error">
      <div class="error-state">
        <el-icon :size="64" color="#f5222d"><WarningFilled /></el-icon>
        <p class="error-text">加载失败，请稍后重试</p>
        <el-button type="primary" @click="$emit('retry')">
          重新加载
        </el-button>
      </div>
    </template>

    <!-- 空状态 -->
    <template v-else-if="courses.length === 0">
      <div class="empty-state">
        <el-icon :size="64" color="#ccc"><Document /></el-icon>
        <p class="empty-text">暂无课程，敬请期待</p>
      </div>
    </template>

    <!-- 课程列表 -->
    <template v-else>
      <div class="course-grid">
        <CourseCard
          v-for="course in courses"
          :key="course.course_id"
          :data="course"
        />
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.course-list-section {
  min-height: 400px;
}

.skeleton-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.skeleton-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.course-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(5, 1fr);

  @media (max-width: 1919px) {
    grid-template-columns: repeat(4, 1fr);
  }

  @media (max-width: 1439px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: 1279px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.error-text,
.empty-text {
  margin: 16px 0 24px;
  font-size: 16px;
  color: #666;
}
</style>