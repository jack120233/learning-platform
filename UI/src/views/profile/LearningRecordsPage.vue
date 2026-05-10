<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { usePagination } from '@/composables/usePagination'
import { deleteLearningRecords, fetchLearningRecords } from '@/api/profile'
import {
  fetchMyLearningCourseDistribution,
  fetchMyLearningStatisticsOverview,
  fetchMyLearningStatisticsTrend,
} from '@/api/learning'
import type { LearningRecordItem, LearningRecordsParams } from '@/api/profile'
import type {
  LearningCourseDistribution,
  LearningStatisticsOverview,
  LearningStatisticsTrendRange,
  LearningStatisticsTrendResponse,
} from '@/api/learning'

// 定义组件名称（用于 keep-alive）
defineOptions({
  name: 'ProfileRecords',
})

const router = useRouter()

const timeRange = ref<'recent_7' | 'recent_30' | 'all'>('all')
const trendRange = ref<LearningStatisticsTrendRange>('7d')
const selectedRecordIds = ref<number[]>([])
const isStatisticsLoading = ref(false)
const isDeleting = ref(false)
const overview = ref<LearningStatisticsOverview>({
  total_duration_seconds: 0,
  last_7_days_duration_seconds: 0,
  learning_course_count: 0,
  completed_course_count: 0,
  continuous_learning_days: 0,
  active_learning_days: 0,
})
const trend = ref<LearningStatisticsTrendResponse>({ range: '7d', items: [] })
const distribution = ref<LearningCourseDistribution>({
  learning_count: 0,
  completed_count: 0,
})

async function fetchRecords(params: LearningRecordsParams) {
  return fetchLearningRecords({
    ...params,
    time_range: timeRange.value,
  })
}

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
  refresh,
} = usePagination<LearningRecordItem, LearningRecordsParams>(fetchRecords, 10)

const timeOptions = [
  { label: '近 7 天', value: 'recent_7' as const },
  { label: '近 30 天', value: 'recent_30' as const },
  { label: '全部', value: 'all' as const },
]

const overviewCards = computed(() => [
  {
    label: '总学习时长',
    value: formatDuration(overview.value.total_duration_seconds),
    icon: 'Clock',
    tone: 'blue',
  },
  {
    label: '近 7 天学习时长',
    value: formatDuration(overview.value.last_7_days_duration_seconds),
    icon: 'TrendCharts',
    tone: 'green',
  },
  {
    label: '在学课程数',
    value: `${overview.value.learning_course_count} 门`,
    icon: 'Reading',
    tone: 'orange',
  },
  {
    label: '已完成课程数',
    value: `${overview.value.completed_course_count} 门`,
    icon: 'CircleCheck',
    tone: 'purple',
  },
])

const trendMaxDuration = computed(() => {
  const max = Math.max(...trend.value.items.map(item => item.duration_seconds), 0)
  return max || 1
})

const distributionTotal = computed(() => distribution.value.learning_count + distribution.value.completed_count)
const learningPercent = computed(() => {
  if (!distributionTotal.value) return 0
  return Math.round((distribution.value.learning_count / distributionTotal.value) * 100)
})
const completedPercent = computed(() => {
  if (!distributionTotal.value) return 0
  return 100 - learningPercent.value
})
const allSelected = computed(() => records.value.length > 0 && selectedRecordIds.value.length === records.value.length)

async function loadStatistics() {
  isStatisticsLoading.value = true
  try {
    const [overviewData, trendData, distributionData] = await Promise.all([
      fetchMyLearningStatisticsOverview(),
      fetchMyLearningStatisticsTrend(trendRange.value),
      fetchMyLearningCourseDistribution(),
    ])
    overview.value = overviewData
    trend.value = trendData
    distribution.value = distributionData
  } finally {
    isStatisticsLoading.value = false
  }
}

async function handleTrendRangeChange() {
  trend.value = await fetchMyLearningStatisticsTrend(trendRange.value)
}

function handleTimeRangeChange() {
  selectedRecordIds.value = []
  fetchData(true)
}

function handleContinue(record: LearningRecordItem) {
  router.push(`/learn/${record.course_id}`)
}

function handleSelectionChange(recordId: number, checked: boolean) {
  if (checked) {
    selectedRecordIds.value = Array.from(new Set([...selectedRecordIds.value, recordId]))
  } else {
    selectedRecordIds.value = selectedRecordIds.value.filter(id => id !== recordId)
  }
}

function toggleSelectAll(checked: string | number | boolean) {
  selectedRecordIds.value = Boolean(checked) ? records.value.map(record => record.id) : []
}

async function handleDeleteRecords(recordIds: number[]) {
  if (!recordIds.length || isDeleting.value) return

  await ElMessageBox.confirm(
    `确认删除选中的 ${recordIds.length} 条学习记录吗？删除后不会影响学习进度和统计数据。`,
    '删除学习记录',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  )

  isDeleting.value = true
  try {
    await deleteLearningRecords(recordIds)
    ElMessage.success('删除成功')
    selectedRecordIds.value = selectedRecordIds.value.filter(id => !recordIds.includes(id))
    await refresh()
  } finally {
    isDeleting.value = false
  }
}

function formatDuration(seconds: number) {
  if (!seconds) return '0 分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return minutes > 0 ? `${hours} 小时 ${minutes} 分钟` : `${hours} 小时`
  return `${Math.max(minutes, 1)} 分钟`
}

function formatDateLabel(date: string) {
  const [, month, day] = date.split('-')
  return `${month}/${day}`
}

function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function progressText(record: LearningRecordItem) {
  return `${Math.round(record.progress || 0)}%`
}

onMounted(() => {
  void loadStatistics()
  void fetchData()
})
</script>

<template>
  <div class="learning-statistics-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">学习统计</h2>
        <p class="page-subtitle">查看你的学习投入、成长趋势和历史学习记录</p>
      </div>
    </div>

    <section class="overview-grid" v-loading="isStatisticsLoading">
      <div
        v-for="card in overviewCards"
        :key="card.label"
        class="overview-card"
        :class="`is-${card.tone}`"
      >
        <div class="card-icon">
          <el-icon><component :is="card.icon" /></el-icon>
        </div>
        <div>
          <p class="card-label">{{ card.label }}</p>
          <strong class="card-value">{{ card.value }}</strong>
        </div>
      </div>
    </section>

    <section class="stats-section growth-section">
      <div class="section-title-row">
        <div>
          <h3 class="section-title">成长反馈</h3>
          <p class="section-desc">保持节奏，持续学习会带来更稳定的进步</p>
        </div>
      </div>
      <div class="growth-grid">
        <div class="growth-item">
          <span class="growth-number">{{ overview.continuous_learning_days }}</span>
          <span class="growth-label">连续学习天数</span>
        </div>
        <div class="growth-item">
          <span class="growth-number">{{ overview.active_learning_days }}</span>
          <span class="growth-label">累计活跃天数</span>
        </div>
      </div>
    </section>

    <div class="statistics-panels">
      <section class="stats-section trend-section">
        <div class="section-title-row">
          <div>
            <h3 class="section-title">学习趋势</h3>
            <p class="section-desc">按自然日统计有效学习时长</p>
          </div>
          <el-radio-group v-model="trendRange" size="small" @change="handleTrendRangeChange">
            <el-radio-button value="7d">近 7 天</el-radio-button>
            <el-radio-button value="30d">近 30 天</el-radio-button>
          </el-radio-group>
        </div>
        <div class="trend-chart">
          <div v-for="item in trend.items" :key="item.date" class="trend-bar-item">
            <div class="trend-bar-track">
              <div
                class="trend-bar"
                :style="{ height: `${Math.max((item.duration_seconds / trendMaxDuration) * 100, item.duration_seconds ? 8 : 0)}%` }"
              />
            </div>
            <span class="trend-label">{{ formatDateLabel(item.date) }}</span>
            <span class="trend-duration">{{ formatDuration(item.duration_seconds) }}</span>
          </div>
        </div>
      </section>

      <section class="stats-section distribution-section">
        <div class="section-title-row">
          <div>
            <h3 class="section-title">课程分布</h3>
            <p class="section-desc">仅统计已开始学习的课程</p>
          </div>
        </div>
        <div class="distribution-bar" :class="{ 'is-empty': distributionTotal === 0 }">
          <div class="distribution-learning" :style="{ width: `${learningPercent}%` }" />
          <div class="distribution-completed" :style="{ width: `${completedPercent}%` }" />
        </div>
        <div class="distribution-list">
          <div class="distribution-item">
            <span class="dot learning" />
            <span>学习中</span>
            <strong>{{ distribution.learning_count }} 门</strong>
          </div>
          <div class="distribution-item">
            <span class="dot completed" />
            <span>已完成</span>
            <strong>{{ distribution.completed_count }} 门</strong>
          </div>
        </div>
      </section>
    </div>

    <section class="stats-section records-section">
      <div class="section-title-row records-title-row">
        <div>
          <h3 class="section-title">学习记录</h3>
          <p class="section-desc">记录删除后仅隐藏展示，不影响学习统计和继续学习</p>
        </div>
      </div>

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

      <div v-if="records.length > 0" class="batch-bar">
        <el-checkbox :model-value="allSelected" @change="toggleSelectAll">全选当前页</el-checkbox>
        <div class="batch-actions">
          <span>已选 {{ selectedRecordIds.length }} 条</span>
          <el-button
            type="danger"
            plain
            :disabled="selectedRecordIds.length === 0"
            :loading="isDeleting"
            @click="handleDeleteRecords(selectedRecordIds)"
          >
            批量删除
          </el-button>
        </div>
      </div>

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

      <el-empty v-else-if="isEmpty" description="暂无学习记录，快去学习课程吧">
        <el-button type="primary" @click="router.push('/')">浏览课程</el-button>
      </el-empty>

      <template v-else>
        <div class="record-list" v-loading="isLoading">
          <div v-for="record in records" :key="record.id" class="record-card">
            <el-checkbox
              class="record-checkbox"
              :model-value="selectedRecordIds.includes(record.id)"
              @change="checked => handleSelectionChange(record.id, Boolean(checked))"
            />

            <el-image :src="record.course_cover || ''" fit="cover" class="record-cover" lazy>
              <template #error>
                <div class="cover-placeholder">
                  <el-icon :size="32" color="#ccc"><Picture /></el-icon>
                </div>
              </template>
            </el-image>

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

              <div class="record-progress">
                <el-progress :percentage="Math.round(record.progress || 0)" :show-text="false" />
                <span>{{ progressText(record) }}</span>
              </div>
            </div>

            <div class="record-action">
              <el-button
                v-if="record.course_status === 'published'"
                type="primary"
                @click="handleContinue(record)"
              >
                继续学习
              </el-button>
              <el-button v-else disabled>课程已下架</el-button>
              <el-button
                type="danger"
                plain
                :loading="isDeleting"
                @click="handleDeleteRecords([record.id])"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>

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
    </section>
  </div>
</template>

<style lang="scss" scoped>
.learning-statistics-page {
  min-width: 0;

  .page-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }

  .page-subtitle {
    margin: 8px 0 0;
    color: #666;
    font-size: 14px;
  }
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
  min-width: 0;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  min-width: 0;
  border-radius: 12px;
  background: #f8fbff;
  border: 1px solid #edf3ff;

  .card-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    background: #e6f4ff;
    color: #1677ff;
    flex-shrink: 0;
  }

  &.is-green .card-icon {
    background: #e9f8f0;
    color: #2bb673;
  }

  &.is-orange .card-icon {
    background: #fff4e5;
    color: #f59a23;
  }

  &.is-purple .card-icon {
    background: #f4edff;
    color: #7c3aed;
  }
}

.card-label {
  margin: 0 0 6px;
  color: #666;
  font-size: 13px;
}

.card-value {
  color: #222;
  font-size: 20px;
  line-height: 1.2;
}

.stats-section {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #eef0f4;
  background: #fff;
  margin-bottom: 16px;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
  min-width: 0;
}

.section-title {
  margin: 0;
  color: #222;
  font-size: 18px;
  font-weight: 600;
}

.section-desc {
  margin: 6px 0 0;
  color: #888;
  font-size: 13px;
}

.growth-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.growth-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f6fbff, #eef7ff);
}

.growth-number {
  font-size: 28px;
  line-height: 1;
  font-weight: 700;
  color: #1677ff;
}

.growth-label {
  color: #666;
  font-size: 14px;
}

.statistics-panels {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
  gap: 16px;
  min-width: 0;
  max-width: 100%;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  min-height: 220px;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.trend-bar-item {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.trend-bar-track {
  width: 100%;
  max-width: 26px;
  height: 140px;
  display: flex;
  align-items: flex-end;
  border-radius: 999px;
  background: #f1f4f8;
  overflow: hidden;
}

.trend-bar {
  width: 100%;
  min-height: 0;
  border-radius: 999px 999px 0 0;
  background: linear-gradient(180deg, #69b1ff, #1677ff);
}

.trend-label,
.trend-duration {
  max-width: 100%;
  color: #777;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.trend-duration {
  color: #999;
}

.distribution-bar {
  display: flex;
  width: 100%;
  max-width: 100%;
  height: 16px;
  border-radius: 999px;
  background: #eef2f7;
  overflow: hidden;
  margin: 12px 0 22px;
  box-sizing: border-box;

  &.is-empty::before {
    content: '';
    width: 100%;
    background: #eef2f7;
  }
}

.distribution-learning {
  background: #409eff;
}

.distribution-completed {
  background: #67c23a;
}

.distribution-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.distribution-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  color: #555;
  min-width: 0;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;

  &.learning {
    background: #409eff;
  }

  &.completed {
    background: #67c23a;
  }
}

.filter-bar,
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.total-count,
.batch-actions {
  font-size: 14px;
  color: #666;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.skeleton-list,
.record-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-card,
.record-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 10px;
}

.skeleton-cover,
.record-cover {
  width: 160px;
  height: 90px;
  border-radius: 8px;
  flex-shrink: 0;
  overflow: hidden;
}

.skeleton-info,
.record-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-checkbox {
  flex-shrink: 0;
  padding-top: 34px;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.record-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
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

.record-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 260px;

  .el-progress {
    flex: 1;
  }

  span {
    flex-shrink: 0;
    color: #666;
    font-size: 13px;
  }
}

.record-action {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 1024px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .statistics-panels {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 768px) {
  .learning-statistics-page {
    .page-title {
      font-size: 20px;
    }
  }

  .overview-grid,
  .growth-grid {
    grid-template-columns: 1fr;
  }

  .stats-section {
    padding: 16px;
  }

  .section-title-row,
  .filter-bar,
  .batch-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .trend-chart {
    gap: 4px;
    min-height: 190px;
    overflow-x: auto;
    overflow-y: hidden;
    padding-bottom: 4px;
  }

  .trend-bar-item {
    flex: 1 0 18px;
  }

  .trend-duration {
    display: none;
  }

  .record-card,
  .skeleton-card {
    flex-direction: column;
    gap: 12px;
  }

  .record-checkbox {
    padding-top: 0;
  }

  .record-cover,
  .skeleton-cover {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
  }

  .record-action {
    width: 100%;
    flex-direction: column;

    .el-button {
      width: 100%;
      margin-left: 0;
    }
  }

  .record-progress {
    max-width: none;
  }
}

@media (max-width: 480px) {
  .overview-card {
    padding: 14px;
  }

  .card-value {
    font-size: 18px;
  }

  .trend-label {
    font-size: 10px;
  }

  :deep(.el-radio-group) {
    display: flex;
    flex-wrap: wrap;
  }
}
</style>
