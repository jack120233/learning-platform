<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { CourseBaseItem } from '@/api/course'

interface Props {
  data: CourseBaseItem
}

const props = defineProps<Props>()
const router = useRouter()

// 点击卡片跳转课程详情
const handleClick = () => {
  const courseId = props.data.course_id || props.data.id
  if (courseId) {
    router.push(`/courses/${courseId}`)
  } else {
    console.warn('Course ID is missing', props.data)
  }
}
</script>

<template>
  <div class="course-card" @click="handleClick">
    <!-- 封面图 -->
    <div class="cover-wrapper">
      <el-image
        :src="data.cover_url"
        fit="cover"
        lazy
        class="cover-image"
      >
        <template #error>
          <div class="cover-placeholder">
            <el-icon :size="48" color="#ccc"><Picture /></el-icon>
          </div>
        </template>
      </el-image>
    </div>

    <!-- 课程信息 -->
    <div class="course-info">
      <h3 class="course-title" :title="data.title">{{ data.title }}</h3>
      <p class="course-summary" v-if="data.summary">{{ data.summary }}</p>
      <div class="course-meta">
        <span class="teacher-name">
          <el-icon><User /></el-icon>
          {{ data.teacher_name }}
        </span>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.course-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);

    .cover-image {
      transform: scale(1.05);
    }
  }
}

.cover-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%; // 16:9
  overflow: hidden;

  .cover-image {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    transition: transform 0.3s ease;
  }

  .cover-placeholder {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f7fa;
  }
}

.course-info {
  padding: 16px;
}

.course-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-summary {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;

  .teacher-name {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}
</style>