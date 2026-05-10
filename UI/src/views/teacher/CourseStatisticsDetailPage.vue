<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Download, Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  exportTeacherStatisticsCourseStudents,
  fetchTeacherStatisticsCourseOverview,
  fetchTeacherStatisticsCourseStudents,
  type TeacherCourseStatisticsOverview,
  type TeacherCourseStatisticsStudentsParams,
  type TeacherCourseStudentStatisticsItem,
  type TeacherStatisticsStudentStatus,
} from '@/api/teacher'

const route = useRoute()
const router = useRouter()
const courseId = computed(() => Number(route.params.courseId))
const range = ref<'7d' | '30d'>('7d')
const statusFilter = ref<TeacherStatisticsStudentStatus>('all')
const keyword = ref('')
const overview = ref<TeacherCourseStatisticsOverview | null>(null)
const isLoadingOverview = ref(false)
const isExporting = ref(false)

async function loadOverview() {
  if (!courseId.value) return
  isLoadingOverview.value = true
  try {
    overview.value = await fetchTeacherStatisticsCourseOverview(courseId.value, range.value)
  } catch (error) {
    ElMessage.error('加载课程统计失败，可能无权查看或授权已被撤销')
    overview.value = null
  } finally {
    isLoadingOverview.value = false
  }
}

async function fetchStudents(params: TeacherCourseStatisticsStudentsParams) {
  return fetchTeacherStatisticsCourseStudents(courseId.value, {
    status: statusFilter.value,
    keyword: keyword.value || undefined,
    ...params,
  })
}

const {
  items: students,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  fetchData,
  goToPage,
} = usePagination<TeacherCourseStudentStatisticsItem, TeacherCourseStatisticsStudentsParams>(fetchStudents, 10)

function formatDuration(seconds: number) {
  if (!seconds) return '0分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
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

function handleSearch() {
  page.value = 1
  fetchData()
}

function handleReset() {
  statusFilter.value = 'all'
  keyword.value = ''
  page.value = 1
  fetchData()
}

async function handleExport() {
  if (!courseId.value) return
  isExporting.value = true
  try {
    const blob = await exportTeacherStatisticsCourseStudents(courseId.value, {
      status: statusFilter.value,
      keyword: keyword.value || undefined,
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `course-${courseId.value}-students.csv`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('导出失败，可能无权查看或授权已被撤销')
  } finally {
    isExporting.value = false
  }
}

async function reloadAll() {
  await Promise.all([loadOverview(), fetchData()])
}

onMounted(() => {
  reloadAll()
})
</script>

<template>
  <div class="course-statistics-detail-page">
    <div class="page-header">
      <div>
        <el-button text :icon="Back" @click="router.push('/teacher/statistics')">返回课程统计</el-button>
        <h2 class="page-title">{{ overview?.course_title || '课程统计详情' }}</h2>
        <p class="page-desc">学生明细仅显示学生ID、用户名和学习行为指标，不展示邮箱、手机号、昵称等隐私字段。</p>
      </div>
      <el-segmented v-model="range" :options="[{ label: '近7天', value: '7d' }, { label: '近30天', value: '30d' }]" @change="loadOverview" />
    </div>

    <el-skeleton v-if="isLoadingOverview" :rows="3" animated />
    <el-empty v-else-if="!overview" description="无法加载课程统计，请确认你仍有访问权限" />

    <template v-else>
      <div class="metric-grid">
        <div class="metric-card">
          <span class="metric-label">开始学习</span>
          <strong>{{ overview.started_student_count }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">范围活跃</span>
          <strong>{{ overview.active_student_count }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">平均进度</span>
          <strong>{{ overview.avg_progress.toFixed(1) }}%</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">完成率</span>
          <strong>{{ overview.completion_rate.toFixed(1) }}%</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">人均时长</span>
          <strong>{{ formatDuration(overview.avg_duration_seconds) }}</strong>
        </div>
        <div class="metric-card">
          <span class="metric-label">累计时长</span>
          <strong>{{ formatDuration(overview.total_duration_seconds) }}</strong>
        </div>
      </div>

      <div class="section-header">
        <div>
          <h3>学生学习明细</h3>
          <p>默认按学习进度升序，便于优先关注低进度学生。</p>
        </div>
        <el-button type="primary" :icon="Download" :loading="isExporting" @click="handleExport">导出CSV</el-button>
      </div>

      <div class="filter-bar">
        <el-select v-model="statusFilter" placeholder="学生状态" style="width: 150px" @change="fetchData">
          <el-option label="全部学生" value="all" />
          <el-option label="7日未学习" value="inactive" />
          <el-option label="低进度" value="low_progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
        <div class="filter-right">
          <el-input v-model="keyword" placeholder="搜索用户名" clearable style="width: 220px" @keyup.enter="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <div class="soft-action-surface filter-actions">
            <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleSearch">搜索</el-button>
            <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
          </div>
        </div>
      </div>

      <div class="table-scroll">
        <el-table :data="students" v-loading="isLoading" stripe border>
          <el-table-column prop="student_id" label="学生ID" width="100" align="center" />
          <el-table-column prop="username" label="用户名" min-width="140" />
          <el-table-column label="进度" width="160" align="center">
            <template #default="{ row }">
              <el-progress :percentage="Number(row.progress.toFixed(1))" :stroke-width="8" />
            </template>
          </el-table-column>
          <el-table-column label="累计时长" width="140" align="center">
            <template #default="{ row }">{{ formatDuration(row.total_duration_seconds) }}</template>
          </el-table-column>
          <el-table-column label="最近学习" width="170" align="center">
            <template #default="{ row }">{{ formatTime(row.last_learn_at) }}</template>
          </el-table-column>
          <el-table-column label="完成状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_completed ? 'success' : 'info'" size="small">{{ row.is_completed ? '已完成' : '学习中' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="完成时间" width="170" align="center">
            <template #default="{ row }">{{ formatTime(row.completed_at) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <el-pagination
        v-if="totalPages > 1"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next, jumper"
        class="pagination"
        @current-change="goToPage"
      />
    </template>
  </div>
</template>

<style lang="scss" scoped>
.course-statistics-detail-page {
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
    margin: 8px 0 0;
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

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.metric-card {
  padding: 18px;
  background: #fff;
  border: 1px solid $border-color-light;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;

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

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;

  h3 {
    margin: 0;
    color: $text-primary;
  }

  p {
    margin: 6px 0 0;
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.filter-bar,
.filter-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-bar {
  justify-content: space-between;
  margin-bottom: 16px;
}

.table-scroll {
  overflow-x: auto;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .course-statistics-detail-page .page-header,
  .section-header,
  .filter-bar,
  .filter-right {
    flex-direction: column;
    align-items: stretch;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .filter-right :deep(.el-input),
  .filter-actions {
    width: 100% !important;
  }
}
</style>
