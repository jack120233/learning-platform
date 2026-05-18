<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bottom, Connection, Search, VideoPlay } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  archiveCourse,
  batchCourseAction,
  fetchManageCourses,
  type BatchCourseAction,
  type TeacherCourseItem,
  type TeacherCoursesParams,
} from '@/api/teacher'
import {
  fetchCourseStatisticsAuthorizationCandidates,
  fetchCourseStatisticsAuthorizations,
  grantCourseStatisticsAuthorizations,
  revokeCourseStatisticsAuthorization,
  type CourseStatisticsAuthorizationCandidate,
  type CourseStatisticsAuthorizationItem,
} from '@/api/admin'

const statusFilter = ref<'published'>('published')
const keyword = ref('')
const selectedRows = ref<TeacherCourseItem[]>([])
const showAuthorizationDrawer = ref(false)
const currentCourse = ref<TeacherCourseItem | null>(null)
const authorizations = ref<CourseStatisticsAuthorizationItem[]>([])
const candidates = ref<CourseStatisticsAuthorizationCandidate[]>([])
const candidateKeyword = ref('')
const selectedTeacherIds = ref<number[]>([])
const isLoadingAuthorizations = ref(false)
const isGranting = ref(false)

const availableStatusTabs = [{ label: '已发布', name: 'published' as const }]

async function fetchCourses(params: TeacherCoursesParams) {
  return fetchManageCourses({
    scope: 'published_all',
    status: statusFilter.value,
    keyword: keyword.value || undefined,
    ...params,
  })
}

const {
  items: courses,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  isEmpty,
  fetchData,
  goToPage,
} = usePagination<TeacherCourseItem, TeacherCoursesParams>(fetchCourses, 10)

const statusMap: Record<string, { text: string; type: 'info' | 'success' | 'danger' }> = {
  draft: { text: '草稿', type: 'info' },
  published: { text: '已发布', type: 'success' },
  archived: { text: '已下架', type: 'danger' },
}

const selectedCount = computed(() => selectedRows.value.length)
const canBatchArchive = computed(() => canBatchByAction('archive', selectedRows.value))
const availableCandidates = computed(() => candidates.value.filter(item => !item.authorized))
const activeAuthorizations = computed(() => authorizations.value.filter(item => item.is_active))

function formatTime(time?: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

function formatDetailTime(time?: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatViewCount(count: number | undefined | null) {
  if (count == null) return '0'
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`
  }
  return count.toString()
}

function canArchiveCourse(course: TeacherCourseItem) {
  return course.status === 'published'
}

function canBatchByAction(action: BatchCourseAction, rows: TeacherCourseItem[]) {
  if (!rows.length) return false
  if (action !== 'archive') return false
  return rows.every(row => canArchiveCourse(row))
}

function handleSelectionChange(selection: TeacherCourseItem[]) {
  selectedRows.value = selection
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function handleReset() {
  statusFilter.value = 'published'
  keyword.value = ''
  selectedRows.value = []
  page.value = 1
  fetchData()
}

async function reloadTable() {
  selectedRows.value = []
  await fetchData()
}

async function requestArchiveReason(title: string) {
  const { value } = await ElMessageBox.prompt(
    `确定要下架${title}吗？下架后学生将无法访问该课程。`,
    '下架原因',
    {
      confirmButtonText: '确定下架',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '请输入下架原因',
      inputValidator: (reason) => {
        if (reason && reason.length > 200) return '下架原因最多 200 个字符'
        return true
      },
    }
  )
  return value
}

async function handleArchive(course: TeacherCourseItem) {
  try {
    const reason = await requestArchiveReason(`课程「${course.title}」`)

    await archiveCourse(course.id, { archive_reason: reason })
    ElMessage.success('课程已下架')
    await reloadTable()
  } catch (error) {
    // 用户取消
  }
}

function showBatchResult(message: string, failedCount: number) {
  if (failedCount > 0) {
    ElMessage.warning(message)
    return
  }
  ElMessage.success(message)
}

async function handleBatchArchive() {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择课程')
    return
  }

  if (!canBatchArchive.value) {
    ElMessage.warning('当前选中的课程不满足批量下架条件')
    return
  }

  try {
    const archiveReason = await requestArchiveReason(`已选择的 ${selectedRows.value.length} 门课程`)
    const result = await batchCourseAction({
      action: 'archive',
      course_ids: selectedRows.value.map(item => item.id),
      archive_reason: archiveReason,
    })

    showBatchResult(`批量下架完成，成功 ${result.success_count} 门，失败 ${result.failed_count} 门`, result.failed_count)
    await reloadTable()
  } catch (error) {
    // 用户取消
  }
}

async function loadAuthorizationData() {
  if (!currentCourse.value) return
  isLoadingAuthorizations.value = true
  try {
    const [authorizationRows, candidateRows] = await Promise.all([
      fetchCourseStatisticsAuthorizations(currentCourse.value.id),
      fetchCourseStatisticsAuthorizationCandidates(currentCourse.value.id, candidateKeyword.value || undefined),
    ])
    authorizations.value = authorizationRows
    candidates.value = candidateRows
    selectedTeacherIds.value = []
  } finally {
    isLoadingAuthorizations.value = false
  }
}

async function openAuthorizationDrawer(course: TeacherCourseItem) {
  currentCourse.value = course
  candidateKeyword.value = ''
  showAuthorizationDrawer.value = true
  await loadAuthorizationData()
}

async function handleGrant() {
  if (!currentCourse.value || selectedTeacherIds.value.length === 0) {
    ElMessage.warning('请选择要授权的老师')
    return
  }

  isGranting.value = true
  try {
    await grantCourseStatisticsAuthorizations(currentCourse.value.id, selectedTeacherIds.value)
    ElMessage.success('统计授权已更新')
    await loadAuthorizationData()
  } finally {
    isGranting.value = false
  }
}

async function handleRevoke(item: CourseStatisticsAuthorizationItem) {
  if (!currentCourse.value) return
  try {
    await ElMessageBox.confirm(
      `确定撤销老师「${item.username}#${item.teacher_id}」对课程「${currentCourse.value.title}」的统计查看授权吗？`,
      '撤销统计授权',
      {
        confirmButtonText: '确定撤销',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await revokeCourseStatisticsAuthorization(currentCourse.value.id, item.teacher_id)
    ElMessage.success('已撤销统计授权')
    await loadAuthorizationData()
  } catch (error) {
    // 用户取消
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="course-list-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">课程管理</h2>
        <p class="page-desc">管理全站已发布课程，并在原课程管理操作中新增课程统计授权。</p>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-left">
        <el-tabs v-model="statusFilter" @tab-change="() => fetchData()" class="status-tabs">
          <el-tab-pane
            v-for="tab in availableStatusTabs"
            :key="tab.name"
            :label="tab.label"
            :name="tab.name"
          />
        </el-tabs>
      </div>

      <div class="search-area">
        <el-input
          v-model="keyword"
          placeholder="搜索课程名称"
          clearable
          @keyup.enter="handleSearch"
          style="width: 240px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="filter-actions soft-action-surface">
          <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleSearch">搜索</el-button>
          <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
        </div>
      </div>
    </div>

    <div v-if="selectedCount > 0" class="batch-actions soft-action-surface--card">
      <span class="selected-count">已选择 {{ selectedCount }} 门课程</span>
      <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" type="warning" size="small" :icon="Bottom" :disabled="!canBatchArchive" @click="handleBatchArchive">
        批量下架
      </el-button>
    </div>

    <div v-if="isLoading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <el-empty v-else-if="isEmpty" description="暂无符合条件的课程" />

    <template v-else>
      <el-table :data="courses" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />

        <el-table-column label="封面" width="100" align="center">
          <template #default="{ row }">
            <el-image :src="row.cover_url || ''" fit="cover" class="cover-image">
              <template #error>
                <div class="cover-placeholder">
                  <el-icon><VideoPlay /></el-icon>
                </div>
              </template>
            </el-image>
          </template>
        </el-table-column>

        <el-table-column label="课程名称" min-width="220">
          <template #default="{ row }">
            <div class="course-title-wrap">
              <span class="course-title">{{ row.title }}</span>
              <span v-if="row.teacher_name" class="teacher-name">老师：{{ row.teacher_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
              {{ statusMap[row.status]?.text || row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="浏览量" width="100" align="center">
          <template #default="{ row }">
            {{ formatViewCount(row.view_count) }}
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="120" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="发布时间" width="120" align="center">
          <template #default="{ row }">
            {{ formatTime(row.published_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="row-actions soft-action-surface">
              <el-button
                v-if="canArchiveCourse(row)"
                class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
                text
                size="small"
                type="warning"
                :icon="Bottom"
                @click="handleArchive(row)"
              >
                下架
              </el-button>
              <el-button
                class="soft-action-btn soft-action-btn--primary soft-action-btn--small"
                text
                size="small"
                type="primary"
                :icon="Connection"
                @click="openAuthorizationDrawer(row)"
              >
                授权
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

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

    <el-drawer v-model="showAuthorizationDrawer" title="课程统计授权" size="520px" class="authorization-drawer">
      <template v-if="currentCourse">
        <div class="drawer-course-card">
          <strong>{{ currentCourse.title }}</strong>
          <span>课程负责人默认可查看统计，无需授权。被授权老师仅可查看统计、学生明细和导出 CSV。</span>
        </div>

        <el-alert
          title="统计授权不会授予课程编辑、发布、下架、删除、内容编辑或资源管理权限。授权列表和候选老师仅显示老师ID与用户名。"
          type="info"
          :closable="false"
          show-icon
          class="privacy-alert"
        />

        <section class="drawer-section">
          <div class="drawer-section-header">
            <h3>当前授权老师</h3>
            <span>{{ activeAuthorizations.length }} 人</span>
          </div>
          <el-table :data="activeAuthorizations" v-loading="isLoadingAuthorizations" stripe border>
            <el-table-column label="老师" min-width="160">
              <template #default="{ row }">{{ row.username }}#{{ row.teacher_id }}</template>
            </el-table-column>
            <el-table-column label="授权时间" width="170" align="center">
              <template #default="{ row }">{{ formatDetailTime(row.assigned_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="90" align="center">
              <template #default="{ row }">
                <el-button text type="danger" size="small" @click="handleRevoke(row)">撤销</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="drawer-section">
          <div class="drawer-section-header">
            <h3>添加授权</h3>
            <span>候选老师不展示邮箱、手机号、昵称等隐私字段</span>
          </div>
          <div class="candidate-search">
            <el-input v-model="candidateKeyword" placeholder="搜索用户名" clearable @keyup.enter="loadAuthorizationData">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button :loading="isLoadingAuthorizations" @click="loadAuthorizationData">搜索</el-button>
          </div>
          <el-select v-model="selectedTeacherIds" multiple filterable placeholder="选择老师" style="width: 100%">
            <el-option
              v-for="candidate in availableCandidates"
              :key="candidate.teacher_id"
              :label="`${candidate.username}#${candidate.teacher_id}`"
              :value="candidate.teacher_id"
            />
          </el-select>
          <div class="drawer-actions soft-action-surface">
            <el-button class="soft-action-btn soft-action-btn--primary" type="primary" :loading="isGranting" @click="handleGrant">授予统计授权</el-button>
            <el-button class="soft-action-btn soft-action-btn--secondary" @click="selectedTeacherIds = []">清空选择</el-button>
          </div>
        </section>
      </template>
    </el-drawer>
  </div>
</template>

<style lang="scss" scoped>
.course-list-page {
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
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }

  .page-desc {
    margin: 8px 0 0;
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;

  .filter-left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .status-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 0;
    }

    :deep(.el-tabs__nav-wrap::after) {
      height: 1px;
      background-color: $border-color-light;
    }
  }

  .search-area {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: $radius-sm;

  .selected-count {
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.loading-container {
  padding: 40px 0;
}

.cover-image,
.cover-placeholder {
  width: 60px;
  height: 40px;
  border-radius: $radius-sm;
  overflow: hidden;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-color;
  color: $text-tertiary;
}

.course-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.course-title {
  font-weight: 500;
  color: $text-primary;
}

.teacher-name {
  font-size: $font-size-sm;
  color: $text-secondary;
}

.row-actions {
  width: fit-content;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.drawer-course-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  margin-bottom: 14px;
  background: #f4f8ff;
  border: 1px solid #dbeafe;
  border-radius: $radius-lg;

  strong {
    color: $text-primary;
  }

  span {
    color: $text-secondary;
    font-size: $font-size-sm;
    line-height: 1.6;
  }
}

.privacy-alert {
  margin-bottom: 18px;
}

.drawer-section {
  margin-bottom: 24px;
}

.drawer-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;

  h3 {
    margin: 0;
    color: $text-primary;
    font-size: $font-size-lg;
  }

  span {
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.candidate-search {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.drawer-actions {
  width: fit-content;
  margin-top: 14px;
}

@media (max-width: 768px) {
  .course-list-page .page-header,
  .filter-bar,
  .filter-bar .filter-left,
  .filter-bar .search-area,
  .filter-actions,
  .batch-actions,
  .row-actions,
  .drawer-section-header,
  .candidate-search,
  .drawer-actions {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
  }

  .filter-bar .search-area :deep(.el-input) {
    width: 100% !important;
  }
}
</style>
