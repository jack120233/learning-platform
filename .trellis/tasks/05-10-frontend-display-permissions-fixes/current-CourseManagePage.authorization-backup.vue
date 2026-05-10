<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Connection, Refresh, Search, VideoPlay } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchManageCourses,
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

const keyword = ref('')
const statusFilter = ref<'all' | 'draft' | 'published' | 'archived'>('published')
const showAuthorizationDrawer = ref(false)
const currentCourse = ref<TeacherCourseItem | null>(null)
const authorizations = ref<CourseStatisticsAuthorizationItem[]>([])
const candidates = ref<CourseStatisticsAuthorizationCandidate[]>([])
const candidateKeyword = ref('')
const selectedTeacherIds = ref<number[]>([])
const isLoadingAuthorizations = ref(false)
const isGranting = ref(false)

async function fetchCourses(params: TeacherCoursesParams) {
  return fetchManageCourses({
    scope: 'published_all',
    status: statusFilter.value === 'all' ? undefined : statusFilter.value,
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

const availableCandidates = computed(() => candidates.value.filter(item => !item.authorized))
const activeAuthorizations = computed(() => authorizations.value.filter(item => item.is_active))

function handleSearch() {
  page.value = 1
  fetchData()
}

function handleReset() {
  keyword.value = ''
  statusFilter.value = 'published'
  page.value = 1
  fetchData()
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
  <div class="admin-course-manage-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">课程管理</h2>
        <p class="page-desc">管理课程统计授权。授权仅允许老师查看、明细和导出课程学习统计，不授予编辑、发布、下架、删除、内容或资源管理权限。</p>
      </div>
      <el-button :icon="Refresh" :loading="isLoading" @click="() => fetchData()">刷新</el-button>
    </div>

    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="statusFilter" placeholder="课程状态" style="width: 140px" @change="fetchData">
          <el-option label="全部状态" value="all" />
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="已下架" value="archived" />
        </el-select>
      </div>
      <div class="filter-right">
        <el-input v-model="keyword" placeholder="搜索课程名称" clearable style="width: 240px" @keyup.enter="handleSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <div class="soft-action-surface filter-actions">
          <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleSearch">搜索</el-button>
          <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
        </div>
      </div>
    </div>

    <el-empty v-if="!isLoading && isEmpty" description="暂无符合条件的课程" />

    <template v-else>
      <div class="table-scroll">
        <el-table :data="courses" v-loading="isLoading" stripe border>
          <el-table-column label="课程" min-width="260">
            <template #default="{ row }">
              <div class="course-cell">
                <el-image :src="row.cover_url || ''" fit="cover" class="cover-image">
                  <template #error>
                    <div class="cover-placeholder"><el-icon><VideoPlay /></el-icon></div>
                  </template>
                </el-image>
                <div class="course-info">
                  <span class="course-title">{{ row.title }}</span>
                  <span class="teacher-name">负责人：{{ row.teacher_name || row.author || `老师#${row.teacher_id}` }}</span>
                </div>
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
          <el-table-column label="学习人数" width="100" align="center" prop="student_count" />
          <el-table-column label="创建时间" width="170" align="center">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="发布时间" width="170" align="center">
            <template #default="{ row }">{{ formatTime(row.published_at) }}</template>
          </el-table-column>
          <el-table-column label="统计授权" width="130" fixed="right" align="center">
            <template #default="{ row }">
              <el-button text type="primary" :icon="Connection" @click="openAuthorizationDrawer(row)">授权</el-button>
            </template>
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
              <template #default="{ row }">{{ formatTime(row.assigned_at) }}</template>
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
.admin-course-manage-page {
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
    max-width: 860px;
    margin: 8px 0 0;
    color: $text-secondary;
    font-size: $font-size-sm;
    line-height: 1.7;
  }
}

.filter-bar,
.filter-left,
.filter-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-bar {
  justify-content: space-between;
  margin-bottom: 20px;
}

.table-scroll {
  overflow-x: auto;
}

.course-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cover-image,
.cover-placeholder {
  width: 72px;
  height: 48px;
  border-radius: $radius-sm;
  overflow: hidden;
  flex-shrink: 0;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-color;
  color: $text-tertiary;
}

.course-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
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
  .admin-course-manage-page .page-header,
  .filter-bar,
  .filter-left,
  .filter-right,
  .filter-actions,
  .drawer-section-header,
  .candidate-search,
  .drawer-actions {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
  }

  .filter-right :deep(.el-input) {
    width: 100% !important;
  }
}
</style>
