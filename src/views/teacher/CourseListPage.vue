<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bottom, Delete, Edit, Plus, Search, Upload, VideoPlay } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import { useUserStore } from '@/store/user'
import {
  archiveCourse,
  batchCourseAction,
  fetchManageCourses,
  type BatchCourseAction,
  type CourseManageScope,
  type TeacherCourseItem,
  type TeacherCoursesParams,
} from '@/api/teacher'

const router = useRouter()
const userStore = useUserStore()

const isAdmin = computed(() => userStore.isAdmin)
const canCreateCourse = computed(() => !isAdmin.value)
const pageTitle = computed(() => isAdmin.value ? '课程管理' : '我的课程')

const manageScope = ref<CourseManageScope>('mine')
const statusFilter = ref<'all' | 'draft' | 'published' | 'archived'>('all')
const keyword = ref('')
const selectedRows = ref<TeacherCourseItem[]>([])

const availableStatusTabs = computed(() => {
  if (isAdmin.value && manageScope.value === 'published_all') {
    return [{ label: '已发布', name: 'published' as const }]
  }
  return [
    { label: '全部', name: 'all' as const },
    { label: '草稿', name: 'draft' as const },
    { label: '已发布', name: 'published' as const },
    { label: '已下架', name: 'archived' as const },
  ]
})

function getEffectiveStatus() {
  if (isAdmin.value && manageScope.value === 'published_all') {
    return 'published'
  }
  return statusFilter.value === 'all' ? undefined : statusFilter.value
}

async function fetchCourses(params: TeacherCoursesParams) {
  return fetchManageCourses({
    scope: manageScope.value,
    status: getEffectiveStatus(),
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

function formatTime(time: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

function formatViewCount(count: number | undefined | null) {
  if (count == null) return '0'
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`
  }
  return count.toString()
}

function isOwnCourse(course: TeacherCourseItem) {
  return course.teacher_id === userStore.userInfo.userId
}

function canEditCourse(course: TeacherCourseItem) {
  return isOwnCourse(course)
}

function canPublishCourse(course: TeacherCourseItem) {
  return isOwnCourse(course) && course.status !== 'published'
}

function canArchiveCourse(course: TeacherCourseItem) {
  if (course.status !== 'published') return false
  if (isAdmin.value && manageScope.value === 'published_all') return true
  return isOwnCourse(course)
}

function canDeleteCourse(course: TeacherCourseItem) {
  return isOwnCourse(course) && course.status !== 'published'
}

const selectedCount = computed(() => selectedRows.value.length)
const canBatchPublish = computed(() => canBatchByAction('publish', selectedRows.value))
const canBatchArchive = computed(() => canBatchByAction('archive', selectedRows.value))
const canBatchDelete = computed(() => canBatchByAction('delete', selectedRows.value))

function canBatchByAction(action: BatchCourseAction, rows: TeacherCourseItem[]) {
  if (!rows.length) return false
  return rows.every((row) => {
    if (action === 'publish') return canPublishCourse(row)
    if (action === 'archive') return canArchiveCourse(row)
    return canDeleteCourse(row)
  })
}

function handleCreate() {
  router.push('/teacher/courses/create')
}

function handleEdit(courseId: number) {
  router.push(`/teacher/courses/${courseId}/edit`)
}

async function handlePublish(course: TeacherCourseItem) {
  try {
    await ElMessageBox.confirm(
      `确定要上架课程「${course.title}」吗？上架后将对所有学员可见。`,
      '上架确认',
      {
        confirmButtonText: '确定上架',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await batchCourseAction({ action: 'publish', course_ids: [course.id] })
    ElMessage.success('课程上架成功')
    await reloadTable()
  } catch (error) {
    // 用户取消
  }
}

async function requestArchiveReason(title: string) {
  const { value } = await ElMessageBox.prompt(
    `确定要下架${title}吗？下架后学员将无法访问该课程。`,
    '下架原因',
    {
      confirmButtonText: '确定下架',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '请输入下架原因（10-200 字符）',
      inputValidator: (reason) => {
        if (!reason) return '请输入下架原因'
        if (reason.length < 10) return '下架原因至少 10 个字符'
        if (reason.length > 200) return '下架原因最多 200 个字符'
        return true
      },
    }
  )
  return value
}

async function handleArchive(course: TeacherCourseItem) {
  try {
    const reason = await requestArchiveReason(`课程「${course.title}」`)
    if (!reason) return

    await archiveCourse(course.id, { archive_reason: reason })
    ElMessage.success('课程已下架')
    await reloadTable()
  } catch (error) {
    // 用户取消
  }
}

async function handleDelete(course: TeacherCourseItem) {
  if (course.status === 'published') {
    ElMessage.warning('已发布课程需先下架后才能删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除课程「${course.title}」吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    )

    await batchCourseAction({ action: 'delete', course_ids: [course.id] })
    ElMessage.success('课程已删除')
    await reloadTable()
  } catch (error) {
    // 用户取消
  }
}

function handleSelectionChange(selection: TeacherCourseItem[]) {
  selectedRows.value = selection
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function handleReset() {
  manageScope.value = 'mine'
  statusFilter.value = 'all'
  keyword.value = ''
  selectedRows.value = []
  page.value = 1
  fetchData()
}

function handleScopeChange() {
  selectedRows.value = []
  if (isAdmin.value && manageScope.value === 'published_all') {
    statusFilter.value = 'published'
  } else {
    statusFilter.value = 'all'
  }
  page.value = 1
  fetchData()
}

async function reloadTable() {
  selectedRows.value = []
  await fetchData()
}

function showBatchResult(message: string, failedCount: number) {
  if (failedCount > 0) {
    ElMessage.warning(message)
    return
  }
  ElMessage.success(message)
}

async function handleBatchAction(action: BatchCourseAction) {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择课程')
    return
  }

  if (!canBatchByAction(action, selectedRows.value)) {
    ElMessage.warning('当前选中的课程不满足批量操作条件')
    return
  }

  try {
    let archiveReason: string | undefined
    if (action === 'archive') {
      archiveReason = await requestArchiveReason(`已选择的 ${selectedRows.value.length} 门课程`)
      if (!archiveReason) return
    }

    if (action === 'delete') {
      await ElMessageBox.confirm(
        `确定要批量删除已选择的 ${selectedRows.value.length} 门课程吗？删除后无法恢复。`,
        '批量删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger',
        }
      )
    }

    if (action === 'publish') {
      await ElMessageBox.confirm(
        `确定要批量上架已选择的 ${selectedRows.value.length} 门课程吗？`,
        '批量上架确认',
        {
          confirmButtonText: '确定上架',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
    }

    const result = await batchCourseAction({
      action,
      course_ids: selectedRows.value.map(item => item.id),
      archive_reason: archiveReason,
    })

    const actionTextMap: Record<BatchCourseAction, string> = {
      publish: '上架',
      archive: '下架',
      delete: '删除',
    }
    showBatchResult(`批量${actionTextMap[action]}完成，成功 ${result.success_count} 门，失败 ${result.failed_count} 门`, result.failed_count)
    await reloadTable()
  } catch (error) {
    // 用户取消
  }
}

onMounted(() => {
  if (isAdmin.value) {
    manageScope.value = 'published_all'
    statusFilter.value = 'published'
  }
  fetchData()
})
</script>

<template>
  <div class="course-list-page">
    <div class="page-header">
      <h2 class="page-title">{{ pageTitle }}</h2>
      <el-button v-if="canCreateCourse" type="primary" :icon="Plus" @click="handleCreate">
        创建课程
      </el-button>
    </div>

    <div class="filter-bar">
      <div class="filter-left">
        <el-segmented
          v-if="isAdmin"
          v-model="manageScope"
          :options="[
            { label: '全站已发布', value: 'published_all' },
            { label: '我的课程', value: 'mine' },
          ]"
          @change="handleScopeChange"
        />
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
        <el-button @click="handleSearch">搜索</el-button>
        <el-button text @click="handleReset">重置</el-button>
      </div>
    </div>

    <div v-if="selectedCount > 0" class="batch-actions">
      <span class="selected-count">已选择 {{ selectedCount }} 门课程</span>
      <el-button v-if="!isAdmin || manageScope === 'mine'" type="success" size="small" :icon="Upload" :disabled="!canBatchPublish" @click="handleBatchAction('publish')">
        批量上架
      </el-button>
      <el-button type="warning" size="small" :icon="Bottom" :disabled="!canBatchArchive" @click="handleBatchAction('archive')">
        批量下架
      </el-button>
      <el-button v-if="!isAdmin || manageScope === 'mine'" type="danger" size="small" :icon="Delete" :disabled="!canBatchDelete" @click="handleBatchAction('delete')">
        批量删除
      </el-button>
    </div>

    <div v-if="isLoading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <el-empty v-else-if="isEmpty" :description="canCreateCourse ? '暂无课程，请先创建课程' : '暂无符合条件的课程'">
      <el-button v-if="canCreateCourse" type="primary" @click="handleCreate">创建课程</el-button>
    </el-empty>

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
              <span v-if="isAdmin && row.teacher_name" class="teacher-name">讲师：{{ row.teacher_name }}</span>
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

        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canEditCourse(row)" text size="small" :icon="Edit" @click="handleEdit(row.id)">
              编辑
            </el-button>
            <el-button v-if="canPublishCourse(row)" text size="small" type="success" :icon="Upload" @click="handlePublish(row)">
              上架
            </el-button>
            <el-button v-if="canArchiveCourse(row)" text size="small" type="warning" :icon="Bottom" @click="handleArchive(row)">
              下架
            </el-button>
            <el-button v-if="canDeleteCourse(row)" text size="small" type="danger" :icon="Delete" @click="handleDelete(row)">
              删除
            </el-button>
            <el-tooltip v-if="!canDeleteCourse(row) && row.status === 'published' && isOwnCourse(row)" content="已发布课程需先下架" placement="top">
              <span>
                <el-button text size="small" type="danger" :icon="Delete" disabled>
                  删除
                </el-button>
              </span>
            </el-tooltip>
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
  </div>
</template>

<style lang="scss" scoped>
.course-list-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
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

.cover-image {
  width: 60px;
  height: 40px;
  border-radius: $radius-sm;
  overflow: hidden;
}

.cover-placeholder {
  width: 60px;
  height: 40px;
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

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .filter-bar {
    .search-area {
      width: 100%;
      flex-wrap: wrap;
    }
  }

  .batch-actions {
    flex-wrap: wrap;
  }
}
</style>
