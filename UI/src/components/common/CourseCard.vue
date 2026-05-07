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
    <div class="cover-wrapper">
      <el-image
        :src="data.cover_url"
        fit="cover"
        lazy
        class="cover-image"
      >
        <template #error>
          <div class="cover-placeholder">
            <el-icon :size="48" color="#bfdbfe"><Picture /></el-icon>
          </div>
        </template>
      </el-image>
      <div class="cover-glow"></div>
    </div>

    <div class="course-info">
      <h3 class="course-title" :title="data.title">{{ data.title }}</h3>
      <p class="course-summary" v-if="data.summary">{{ data.summary }}</p>
      <div class="course-meta">
        <span class="teacher-name">
          <el-icon><User /></el-icon>
          {{ data.teacher_name || '课程老师' }}
        </span>
        <span class="course-entry">查看课程</span>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.course-card {
  position: relative;
  height: 100%;
  overflow: hidden;
  cursor: pointer;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid rgba(219, 234, 254, 0.9);
  border-radius: 18px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
  transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;

  &::after {
    content: '';
    position: absolute;
    inset: auto 18px 0;
    height: 3px;
    background: linear-gradient(90deg, rgba(24, 144, 255, 0), #1890ff 45%, rgba(37, 99, 235, 0));
    opacity: 0;
    transition: opacity 0.28s ease;
  }

  &:hover {
    transform: translateY(-5px);
    border-color: #bfdbfe;
    box-shadow: 0 18px 38px rgba(37, 99, 235, 0.16);

    &::after {
      opacity: 1;
    }

    .cover-image {
      transform: scale(1.06);
    }

    .cover-glow {
      opacity: 1;
    }

    .course-entry {
      opacity: 1;
      transform: translateX(0);
    }
  }
}

.cover-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  overflow: hidden;
  background: #eef6ff;

  .cover-image {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    transition: transform 0.32s ease;
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
    background: linear-gradient(135deg, #eff6ff 0%, #f8fbff 100%);
  }
}

.cover-glow {
  position: absolute;
  inset: auto 0 0;
  height: 42%;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(24, 144, 255, 0) 0%, rgba(24, 144, 255, 0.18) 100%);
  opacity: 0;
  transition: opacity 0.28s ease;
}

.course-info {
  position: relative;
  padding: 16px;
}

.course-title {
  margin: 0 0 8px;
  color: #1e293b;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-summary {
  min-height: 39px;
  margin: 0 0 14px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
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
  gap: 12px;
  font-size: 12px;
  color: #64748b;
}

.teacher-name {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 9px;
  color: #2563eb;
  background: #f4f8ff;
  border: 1px solid #dbeafe;
  border-radius: 999px;

  :deep(.el-icon) {
    flex-shrink: 0;
  }
}

.course-entry {
  flex-shrink: 0;
  color: #2563eb;
  font-weight: 600;
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.28s ease, transform 0.28s ease;
}

@media (max-width: 768px) {
  .course-card {
    border-radius: 16px;
  }

  .course-entry {
    display: none;
  }
}
</style>