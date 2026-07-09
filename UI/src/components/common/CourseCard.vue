<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { CourseBaseItem } from '@/api/course'
import { DEFAULT_COURSE_COVER, resolveCourseCoverUrl } from '@/utils/course'

interface Props {
  data: CourseBaseItem
}

const props = defineProps<Props>()
const router = useRouter()
const resolvedCoverUrl = computed(() => resolveCourseCoverUrl(props.data.cover_url))

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
        :src="resolvedCoverUrl"
        fit="cover"
        lazy
        class="cover-image"
      >
        <template #error>
          <img :src="DEFAULT_COURSE_COVER" alt="" class="cover-image cover-image--fallback" />
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
  min-width: 0;
  overflow: hidden;
  cursor: pointer;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid rgba(219, 234, 254, 0.9);
  border-radius: 16px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
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
    transform: translateY(-4px);
    border-color: #bfdbfe;
    box-shadow: 0 14px 30px rgba(37, 99, 235, 0.14);

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
  padding-top: 58%;
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
}

.cover-image--fallback {
  display: block;
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
  padding: 14px 14px 12px;
}

.course-title {
  margin: 0 0 6px;
  color: #1e293b;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-summary {
  min-height: 36px;
  margin: 0 0 12px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
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
  gap: 8px;
  font-size: 12px;
  color: #64748b;
}

.teacher-name {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  color: #2563eb;
  background: #f4f8ff;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  font-size: 12px;

  :deep(.el-icon) {
    flex-shrink: 0;
  }
}

.course-entry {
  flex-shrink: 0;
  color: #2563eb;
  font-weight: 600;
  font-size: 12px;
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
