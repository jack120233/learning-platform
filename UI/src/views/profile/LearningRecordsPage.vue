<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePagination } from '@/composables/usePagination'
import { fetchLearningRecords } from '@/api/profile'
import type { LearningRecordItem, LearningRecordsParams } from '@/api/profile'

// 定义组件名称（用于 keep-alive）
defineOptions({
  name: 'ProfileRecords',
})

const router = useRouter()

// 时间范围筛选
const timeRange = ref<'recent_7' | 'recent_30' | 'all'>('all')

// 获取学习记录
async function fetchRecords(params: LearningRecordsParams) {
  return fetchLearningRecords({
    ...params,
    time_range: timeRange.value,
  })
}

// 分页 Hook
const {
  items: records,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  isEmpty,
  fetchData,
  goToPage,
} = usePagination<LearningRecordItem, LearningRecordsParams>(
  fetchRecords,
  10
)

// 时间范围选项
const timeOptions = [
  { label: '近 7 天', value: 'recent_7' as const },
  { label: '近 30 天', value: 'recent_30' as const },
  { label: '全部', value: 'all' as const },
]

// 处理时间范围变化
function handleTimeRangeChange() {
  fetchData(true)
}

// 继续学习
function handleContinue(record: LearningRecordItem) {
  router.push(`/learn/${record.course_id}`)
}

// 格式化时间
function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 初始化加载
onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="learning-records-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">学习记录</h2>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-radio-group v-model="timeRange" @change="handleTimeRangeChange">
        <el-radio-button
          v-for="option in timeOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </el-radio-button>
      </el-radio-group>

      <span class="total-count">共 {{ total }} 条记录</span>
    </div>

    <!-- 加载中骨架屏 -->
    <div class="skeleton-list" v-if="isLoading && records.length === 0">
      <el-skeleton v-for="i in 3" :key="i" animated>
        <template #template>
          <div class="skeleton-card">
            <el-skeleton-item variant="image" class="skeleton-cover" />
            <div class="skeleton-info">
              <el-skeleton-item variant="h3" style="width: 60%" />
              <el-skeleton-item variant="text" style="width: 40%" />
              <el-skeleton-item variant="text" style="width: 30%" />
            </div>
          </div>
        </template>
      </el-skeleton>
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="isEmpty" description="暂无学习记录，快去学习课程吧">
      <el-button type="primary" @click="router.push('/')">浏览课程</el-button>
    </el-empty>

    <!-- 记录列表 -->
    <template v-else>
      <div class="record-list" v-loading="isLoading">
        <div
          v-for="record in records"
          :key="record.course_id"
          class="record-card"
        >
          <!-- 课程封面 -->
          <el-image
            :src="record.course_cover"
            fit="cover"
            class="record-cover"
            lazy
          >
            <template #error>
              <div class="cover-placeholder">
                <el-icon :size="32" color="#ccc"><Picture /></el-icon>
              </div>
            </template>
          </el-image>

          <!-- 课程信息 -->
          <div class="record-info">
            <div class="record-title-row">
              <h3 class="record-title">{{ record.course_title }}</h3>
              <el-tag v-if="record.course_status === 'archived'" type="danger" size="small">
                已下架
              </el-tag>
            </div>

            <p class="record-section">
              <el-icon><VideoPlay /></el-icon>
              上次学习：{{ record.last_section_title || '章节资源' }}
            </p>

            <p class="record-time">
              <el-icon><Clock /></el-icon>
              {{ formatTime(record.last_learn_at) }}
            </p>
          </div>

          <!-- 操作按钮 -->
          <div class="record-action">
            <el-button
              v-if="record.course_status === 'published'"
              type="primary"
              @click="handleContinue(record)"
            >
              继续学习
            </el-button>
            <el-button v-else disabled>课程已下架</el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="totalPages > 1"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper"
        class="pagination"
        @current-change="goToPage"
      />
    </template>
  </div>
</template>

<style lang="scss" scoped>
.learning-records-page {
  .page-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.total-count {
  font-size: 14px;
  color: #666;
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.skeleton-cover {
  width: 160px;
  height: 90px;
  flex-shrink: 0;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-card {
  display: flex;
  gap: 20px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.3s ease;

  &:hover {
    background: #f0f7ff;
  }
}

.record-cover {
  width: 160px;
  height: 90px;
  border-radius: 6px;
  flex-shrink: 0;
  overflow: hidden;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.record-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-section,
.record-time {
  font-size: 14px;
  color: #666;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.record-action {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

// 响应式
@media (max-width: 768px) {
  .record-card {
    flex-direction: column;
    gap: 12px;
  }

  .record-cover {
    width: 100%;
    height: auto;
    aspect-ratio: 16/9;
  }

  .record-action {
    width: 100%;

    .el-button {
      width: 100%;
    }
  }
}
</style>
