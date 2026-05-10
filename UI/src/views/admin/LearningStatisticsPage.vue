<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Refresh, Search, TrendCharts } from '@element-plus/icons-vue'
import { fetchCategories, type CategoryItem } from '@/api/category'
import {
  fetchAdminLearningStatisticsOverview,
  fetchAdminLearningStatisticsTrend,
  fetchAdminLowCompletionCourses,
  fetchAdminPopularCourses,
  fetchUsers,
  type AdminCourseStatus,
  type AdminLearningStatisticsMetric,
  type AdminLearningStatisticsOverview,
  type AdminLearningStatisticsRange,
  type AdminLearningStatisticsTrend,
  type AdminLowCompletionCourseStatisticsItem,
  type AdminPopularCourseStatisticsItem,
  type AdminUserItem,
} from '@/api/admin'

const range = ref<AdminLearningStatisticsRange>('7d')
const metric = ref<AdminLearningStatisticsMetric>('duration')
const categoryId = ref<number | undefined>()
const teacherId = ref<number | undefined>()
const courseStatus = ref<AdminCourseStatus>('all')

const categories = ref<CategoryItem[]>([])
const teachers = ref<AdminUserItem[]>([])
const overview = ref<AdminLearningStatisticsOverview | null>(null)
const trend = ref<AdminLearningStatisticsTrend | null>(null)
const popularCourses = ref<AdminPopularCourseStatisticsItem[]>([])
const lowCompletionCourses = ref<AdminLowCompletionCourseStatisticsItem[]>([])
const isLoading = ref(false)

const trendRange = computed(() => range.value === 'all' ? '30d' : range.value)
const maxTrendValue = computed(() => Math.max(...(trend.value?.items.map(item => item.value) || [0]), 1))

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已下架', value: 'archived' },
]

const metricOptions: Array<{ label: string; value: AdminLearningStatisticsMetric }> = [
  { label: '学习时长', value: 'duration' },
  { label: '活跃学生', value: 'active_students' },
  { label: '完成课程', value: 'completed_courses' },
]

function buildFilters() {
  return {
    range: range.value,
    category_id: categoryId.value,
    teacher_id: teacherId.value,
    course_status: courseStatus.value,
  }
}

async function loadFilterOptions() {
  const [categoryList, teacherPage] = await Promise.all([
    fetchCategories(undefined, true),
    fetchUsers({ role: 'teacher', status: 'active', page: 1, page_size: 100 }),
  ])
  categories.value = categoryList
  teachers.value = teacherPage.items
}

async function loadStatistics() {
  isLoading.value = true
  try {
    const filters = buildFilters()
    const [overviewData, trendData, popularData, lowCompletionData] = await Promise.all([
      fetchAdminLearningStatisticsOverview(filters),
      fetchAdminLearningStatisticsTrend({ ...filters, range: trendRange.value, metric: metric.value }),
      fetchAdminPopularCourses({ ...filters, limit: 10 }),
      fetchAdminLowCompletionCourses({ ...filters, limit: 10 }),
    ])
    overview.value = overviewData
    trend.value = trendData
    popularCourses.value = popularData
    lowCompletionCourses.value = lowCompletionData
  } finally {
    isLoading.value = false
  }
}

function handleReset() {
  range.value = '7d'
  metric.value = 'duration'
  categoryId.value = undefined
  teacherId.value = undefined
  courseStatus.value = 'all'
  loadStatistics()
}

function formatDuration(seconds: number) {
  if (!seconds) return '0分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
}

function formatTrendValue(value: number) {
  return metric.value === 'duration' ? formatDuration(value) : value.toString()
}

function formatTime(time?: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(async () => {
  await loadFilterOptions()
  await loadStatistics()
})
</script>

<template>
  <div class="admin-learning-statistics-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">学习统计</h2>
        <p class="page-desc">查看平台学生学习行为趋势、热门课程和低完成率课程，统计口径仅包含学生学习数据。</p>
      </div>
      <el-button :icon="Refresh" :loading="isLoading" @click="loadStatistics">刷新</el-button>
    </div>

    <div class="filter-bar">
      <div class="filter-left">
        <el-segmented v-model="range" :options="[{ label: '近7天', value: '7d' }, { label: '近30天', value: '30d' }, { label: '全部', value: 'all' }]" @change="loadStatistics" />
        <el-select v-model="categoryId" placeholder="课程分类" clearable style="width: 160px" @change="loadStatistics">
          <el-option v-for="category in categories" :key="category.category_id" :label="category.name" :value="category.category_id" />
        </el-select>
        <el-select v-model="teacherId" placeholder="课程老师" clearable filterable style="width: 180px" @change="loadStatistics">
          <el-option v-for="teacher in teachers" :key="teacher.user_id" :label="`${teacher.username}#${teacher.user_id}`" :value="teacher.user_id" />
        </el-select>
        <el-select v-model="courseStatus" placeholder="课程状态" style="width: 140px" @change="loadStatistics">
          <el-option v-for="option in statusOptions" :key="option.value" :label="option.label" :value="option.value" />
        </el-select>
      </div>
      <div class="soft-action-surface filter-actions">
        <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" :icon="Search" :loading="isLoading" @click="loadStatistics">查询</el-button>
        <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
      </div>
    </div>

    <el-skeleton v-if="isLoading && !overview" :rows="6" animated />

    <template v-else>
      <div class="metric-grid">
        <div class="metric-card">
          <span class="metric-label">开始学习学生</span>
          <strong>{{ overview?.total_student_count || 0 }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">范围活跃学生</span>
          <strong>{{ overview?.active_student_count || 0 }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">有效学习时长</span>
          <strong>{{ formatDuration(overview?.total_duration_seconds || 0) }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">活跃课程</span>
          <strong>{{ overview?.active_course_count || 0 }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">新开始人课</span>
          <strong>{{ overview?.new_started_course_count || 0 }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">新完成人课</span>
          <strong>{{ overview?.new_completed_course_count || 0 }}</strong>
        </div>
      </div>

      <div class="panel-card trend-card">
        <div class="section-header">
          <div>
            <h3><el-icon><TrendCharts /></el-icon> 学习趋势</h3>
            <p>趋势仅支持近 7 天或近 30 天；选择“全部”时按近 30 天展示趋势。</p>
          </div>
          <el-segmented v-model="metric" :options="metricOptions" @change="loadStatistics" />
        </div>
        <div v-if="trend?.items.length" class="trend-list">
          <div v-for="item in trend.items" :key="item.date" class="trend-row">
            <span class="trend-date">{{ item.date.slice(5) }}</span>
            <div class="trend-bar-track">
              <span class="trend-bar" :style="{ width: `${Math.max((item.value / maxTrendValue) * 100, item.value ? 6 : 0)}%` }"></span>
            </div>
            <span class="trend-value">{{ formatTrendValue(item.value) }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无趋势数据" />
      </div>

      <div class="table-panels">
        <div class="panel-card">
          <div class="section-header compact">
            <div>
              <h3>热门课程</h3>
              <p>按活跃学生数、学习时长排序。</p>
            </div>
          </div>
          <div class="table-scroll">
            <el-table :data="popularCourses" stripe border>
              <el-table-column prop="course_title" label="课程" min-width="180" />
              <el-table-column label="老师" width="120">
                <template #default="{ row }">{{ row.teacher_username }}#{{ row.teacher_id }}</template>
              </el-table-column>
              <el-table-column prop="category_name" label="分类" width="120" />
              <el-table-column prop="active_student_count" label="活跃学生" width="100" align="center" />
              <el-table-column label="学习时长" width="130" align="center">
                <template #default="{ row }">{{ formatDuration(row.total_duration_seconds) }}</template>
              </el-table-column>
              <el-table-column label="完成率" width="100" align="center">
                <template #default="{ row }">{{ row.completion_rate.toFixed(1) }}%</template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div class="panel-card">
          <div class="section-header compact">
            <div>
              <h3>低完成率课程</h3>
              <p>开始学习人数不少于 5 且完成率低于 30%。</p>
            </div>
          </div>
          <div class="table-scroll">
            <el-table :data="lowCompletionCourses" stripe border>
              <el-table-column prop="course_title" label="课程" min-width="180" />
              <el-table-column label="老师" width="120">
                <template #default="{ row }">{{ row.teacher_username }}#{{ row.teacher_id }}</template>
              </el-table-column>
              <el-table-column prop="started_student_count" label="开始学习" width="100" align="center" />
              <el-table-column prop="completed_student_count" label="已完成" width="90" align="center" />
              <el-table-column label="完成率" width="100" align="center">
                <template #default="{ row }">{{ row.completion_rate.toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column label="平均进度" width="110" align="center">
                <template #default="{ row }">{{ row.avg_progress.toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column label="最近学习" width="160" align="center">
                <template #default="{ row }">{{ formatTime(row.recent_learn_at) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.admin-learning-statistics-page {
  .page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid $border-color-light;
  }

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
  }

  .page-desc {
    margin: 8px 0 0;
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.filter-bar,
.filter-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-bar {
  justify-content: space-between;
  margin-bottom: 20px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card,
.panel-card {
  background: #fff;
  border: 1px solid $border-color-light;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
}

.metric-card {
  padding: 18px;

  .metric-label {
    display: block;
    color: $text-secondary;
    font-size: $font-size-sm;
    margin-bottom: 8px;
  }

  strong {
    font-size: 22px;
    color: $text-primary;
  }
}

.panel-card {
  padding: 18px;
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;

  &.compact {
    align-items: flex-start;
  }

  h3 {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    color: $text-primary;
  }

  p {
    margin: 6px 0 0;
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-row {
  display: grid;
  grid-template-columns: 56px 1fr 120px;
  align-items: center;
  gap: 12px;
  font-size: $font-size-sm;
}

.trend-date,
.trend-value {
  color: $text-secondary;
}

.trend-value {
  text-align: right;
}

.trend-bar-track {
  height: 10px;
  background: #eef5ff;
  border-radius: 999px;
  overflow: hidden;
}

.trend-bar {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #1890ff 0%, #40a9ff 100%);
}

.table-panels {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.table-scroll {
  overflow-x: auto;
}

@media (max-width: 768px) {
  .admin-learning-statistics-page .page-header,
  .filter-bar,
  .filter-left,
  .section-header,
  .filter-actions {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .trend-row {
    grid-template-columns: 50px 1fr;

    .trend-value {
      grid-column: 2;
      text-align: left;
    }
  }
}
</style>
