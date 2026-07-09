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
    <section class="statistics-hero">
      <div class="hero-content">
        <el-button class="back-link" text :icon="Back" @click="router.push('/teacher/statistics')">
          返回课程统计
        </el-button>
        <h2 class="page-title">{{ overview?.course_title || '课程统计详情' }}</h2>
        <p class="page-desc">聚焦课程学习进度、活跃情况和完成表现，帮助老师快速识别需要跟进的学习状态。</p>
      </div>
      <div class="range-panel">
        <span class="range-label">统计范围</span>
        <el-segmented
          v-model="range"
          :options="[{ label: '近7天', value: '7d' }, { label: '近30天', value: '30d' }]"
          @change="loadOverview"
        />
      </div>
    </section>

    <div v-if="isLoadingOverview" class="state-card">
      <el-skeleton :rows="4" animated />
    </div>
    <div v-else-if="!overview" class="state-card state-card--empty">
      <el-empty description="无法加载课程统计，请确认你仍有访问权限" />
    </div>

    <template v-else>
      <div class="metric-grid">
        <div class="metric-card metric-card--blue">
          <span class="metric-icon">学</span>
          <span class="metric-label">开始学习</span>
          <strong>{{ overview.started_student_count }}</strong>
          <small>已产生学习记录的学生</small>
        </div>
        <div class="metric-card metric-card--cyan">
          <span class="metric-icon">活</span>
          <span class="metric-label">范围活跃</span>
          <strong>{{ overview.active_student_count }}</strong>
          <small>{{ range === '7d' ? '近7天' : '近30天' }}有学习行为</small>
        </div>
        <div class="metric-card metric-card--violet">
          <span class="metric-icon">进</span>
          <span class="metric-label">平均进度</span>
          <strong>{{ overview.avg_progress.toFixed(1) }}%</strong>
          <small>全体学习者平均完成度</small>
        </div>
        <div class="metric-card metric-card--green">
          <span class="metric-icon">完</span>
          <span class="metric-label">完成率</span>
          <strong>{{ overview.completion_rate.toFixed(1) }}%</strong>
          <small>已完成课程的学生占比</small>
        </div>
        <div class="metric-card metric-card--amber">
          <span class="metric-icon">均</span>
          <span class="metric-label">人均时长</span>
          <strong>{{ formatDuration(overview.avg_duration_seconds) }}</strong>
          <small>单个学生平均学习投入</small>
        </div>
        <div class="metric-card metric-card--slate">
          <span class="metric-icon">总</span>
          <span class="metric-label">累计时长</span>
          <strong>{{ formatDuration(overview.total_duration_seconds) }}</strong>
          <small>课程累计学习投入</small>
        </div>
      </div>

      <section class="detail-card">
        <div class="section-header">
          <div>
            <span class="section-eyebrow">Student Details</span>
            <h3>学生学习明细</h3>
            <p>默认按学习进度升序，便于优先关注低进度学生。</p>
          </div>
          <div class="soft-action-surface export-actions">
            <el-button
              class="soft-action-btn soft-action-btn--primary"
              type="primary"
              :icon="Download"
              :loading="isExporting"
              @click="handleExport"
            >
              导出CSV
            </el-button>
          </div>
        </div>

        <div class="filter-bar">
          <el-select v-model="statusFilter" placeholder="学生状态" class="status-select" @change="fetchData">
            <el-option label="全部学生" value="all" />
            <el-option label="7日未学习" value="inactive" />
            <el-option label="低进度" value="low_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
          <div class="filter-right">
            <el-input v-model="keyword" placeholder="搜索用户名" clearable class="keyword-input" @keyup.enter="handleSearch">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <div class="soft-action-surface filter-actions">
              <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleSearch">搜索</el-button>
              <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
            </div>
          </div>
        </div>

        <div class="table-scroll">
          <el-table :data="students" v-loading="isLoading" stripe border class="students-table">
            <el-table-column prop="student_id" label="学生ID" width="100" align="center" />
            <el-table-column prop="username" label="用户名" min-width="140" />
            <el-table-column label="进度" width="170" align="center">
              <template #default="{ row }">
                <el-progress :percentage="Number(row.progress.toFixed(1))" :stroke-width="9" />
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
                <el-tag :type="row.is_completed ? 'success' : 'info'" size="small" effect="light">
                  {{ row.is_completed ? '已完成' : '学习中' }}
                </el-tag>
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
      </section>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.course-statistics-detail-page {
  position: relative;
  min-height: calc(100vh - 96px);
  margin: -24px;
  padding: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at 8% 0%, rgba(24, 144, 255, 0.15), transparent 30%),
    radial-gradient(circle at 92% 8%, rgba(82, 196, 26, 0.12), transparent 28%),
    linear-gradient(180deg, #f4f8ff 0%, #ffffff 46%, #f8fbff 100%);

  &::before {
    content: '';
    position: absolute;
    top: 120px;
    right: -120px;
    width: 280px;
    height: 280px;
    border-radius: 50%;
    background: rgba(24, 144, 255, 0.08);
    filter: blur(8px);
    pointer-events: none;
  }
}

.statistics-hero,
.metric-grid,
.detail-card,
.state-card {
  position: relative;
  z-index: 1;
}

.statistics-hero {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
  padding: 28px;
  border: 1px solid rgba(219, 234, 254, 0.9);
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(239, 246, 255, 0.96) 100%),
    #fff;
  box-shadow: 0 20px 48px rgba(24, 144, 255, 0.12);
}

.hero-content {
  min-width: 0;
}

.back-link {
  margin: 0 0 18px -8px;
  color: #2563eb;
  font-weight: 600;
}

.section-eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.page-title {
  margin: 0;
  color: #0f172a;
  font-size: 28px;
  font-weight: 800;
  line-height: 1.3;
  overflow-wrap: anywhere;
}

.page-desc {
  max-width: 680px;
  margin: 10px 0 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.7;
}

.range-panel {
  display: flex;
  flex: 0 0 260px;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  padding: 18px;
  border: 1px solid #dbeafe;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.range-label {
  color: #475569;
  font-size: 13px;
  font-weight: 700;
}

.state-card {
  padding: 24px;
  border: 1px solid #dbeafe;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.state-card--empty {
  display: flex;
  justify-content: center;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 22px;
}

.metric-card {
  position: relative;
  min-height: 158px;
  padding: 20px;
  overflow: hidden;
  border: 1px solid #e0ecff;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.07);
  transition: transform $transition-base, box-shadow $transition-base;

  &::after {
    content: '';
    position: absolute;
    inset: auto -36px -46px auto;
    width: 112px;
    height: 112px;
    border-radius: 50%;
    background: var(--metric-glow, rgba(24, 144, 255, 0.12));
  }

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 18px 42px rgba(15, 23, 42, 0.1);
  }

  .metric-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    margin-bottom: 14px;
    border-radius: 12px;
    background: var(--metric-bg, #eff6ff);
    color: var(--metric-color, #2563eb);
    font-weight: 800;
  }

  .metric-label {
    display: block;
    color: #64748b;
    font-size: 13px;
    font-weight: 700;
  }

  strong {
    display: block;
    margin-top: 6px;
    color: #0f172a;
    font-size: 26px;
    font-weight: 800;
    line-height: 1.25;
    overflow-wrap: anywhere;
  }

  small {
    display: block;
    margin-top: 8px;
    color: #64748b;
    line-height: 1.5;
  }
}

.metric-card--blue {
  --metric-bg: #eff6ff;
  --metric-color: #2563eb;
  --metric-glow: rgba(37, 99, 235, 0.13);
}

.metric-card--cyan {
  --metric-bg: #ecfeff;
  --metric-color: #0891b2;
  --metric-glow: rgba(8, 145, 178, 0.13);
}

.metric-card--violet {
  --metric-bg: #f5f3ff;
  --metric-color: #7c3aed;
  --metric-glow: rgba(124, 58, 237, 0.12);
}

.metric-card--green {
  --metric-bg: #ecfdf5;
  --metric-color: #16a34a;
  --metric-glow: rgba(22, 163, 74, 0.13);
}

.metric-card--amber {
  --metric-bg: #fffbeb;
  --metric-color: #d97706;
  --metric-glow: rgba(217, 119, 6, 0.13);
}

.metric-card--slate {
  --metric-bg: #f1f5f9;
  --metric-color: #475569;
  --metric-glow: rgba(71, 85, 105, 0.12);
}

.detail-card {
  padding: 24px;
  border: 1px solid rgba(219, 234, 254, 0.95);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;

  h3 {
    margin: 4px 0 0;
    color: #0f172a;
    font-size: 20px;
    font-weight: 800;
  }

  p {
    margin: 6px 0 0;
    color: #64748b;
    font-size: 13px;
  }
}

.export-actions {
  flex-shrink: 0;
}

.filter-bar,
.filter-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-bar {
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 14px;
  border: 1px solid #e0ecff;
  border-radius: 18px;
  background: #f8fbff;
}

.status-select {
  width: 150px;
}

.keyword-input {
  width: 220px;
}

.table-scroll {
  overflow-x: auto;
  border: 1px solid #e0ecff;
  border-radius: 18px;
  background: #fff;

  :deep(.el-table) {
    border-radius: 18px;
  }

  :deep(.el-table__header th) {
    background: #f8fbff;
    color: #334155;
    font-weight: 700;
  }

  :deep(.el-table__row) {
    transition: background-color $transition-fast;
  }
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 1024px) {
  .statistics-hero {
    flex-direction: column;
  }

  .range-panel {
    flex-basis: auto;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .course-statistics-detail-page {
    min-height: calc(100vh - 72px);
    margin: -16px;
    padding: 16px;
  }

  .statistics-hero,
  .detail-card {
    padding: 18px;
    border-radius: 20px;
  }

  .page-title {
    font-size: 23px;
  }

  .section-header,
  .filter-bar,
  .filter-right {
    flex-direction: column;
    align-items: stretch;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .status-select,
  .keyword-input,
  .filter-actions,
  .export-actions {
    width: 100% !important;
  }
}
</style>
