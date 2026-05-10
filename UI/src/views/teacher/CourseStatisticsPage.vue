<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, TrendCharts, VideoPlay } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchTeacherStatisticsCourses,
  type TeacherCourseStatisticsItem,
  type TeacherStatisticsCoursesParams,
  type TeacherStatisticsPermissionType,
} from '@/api/teacher'

const router = useRouter()
const keyword = ref('')
const permissionType = ref<TeacherStatisticsPermissionType>('all')
const statusFilter = ref<'all' | 'draft' | 'published' | 'archived'>('all')

async function fetchStatisticsCourses(params: TeacherStatisticsCoursesParams) {
  return fetchTeacherStatisticsCourses({
    keyword: keyword.value || undefined,
    permission_type: permissionType.value,
    status: statusFilter.value,
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
} = usePagination<TeacherCourseStatisticsItem, TeacherStatisticsCoursesParams>(fetchStatisticsCourses, 10)

const statusMap: Record<string, { text: string; type: 'info' | 'success' | 'danger' }> = {
  draft: { text: '草稿', type: 'info' },
  published: { text: '已发布', type: 'success' },
  archived: { text: '已下架', type: 'danger' },
}

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
  keyword.value = ''
  permissionType.value = 'all'
  statusFilter.value = 'all'
  page.value = 1
  fetchData()
}

function openDetail(course: TeacherCourseStatisticsItem) {
  router.push(`/teacher/statistics/courses/${course.course_id}`)
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="teacher-statistics-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">课程统计</h2>
        <p class="page-desc">查看你负责或被授权课程的学习数据，授权仅包含统计查看、明细和导出。</p>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="permissionType" placeholder="权限来源" style="width: 140px" @change="fetchData">
          <el-option label="全部课程" value="all" />
          <el-option label="我负责的" value="owner" />
          <el-option label="被授权的" value="authorized" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="课程状态" style="width: 140px" @change="fetchData">
          <el-option label="全部状态" value="all" />
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="已下架" value="archived" />
        </el-select>
      </div>
      <div class="filter-right">
        <el-input v-model="keyword" placeholder="搜索课程名称" clearable style="width: 240px" @keyup.enter="handleSearch">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="soft-action-surface filter-actions">
          <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleSearch">搜索</el-button>
          <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
        </div>
      </div>
    </div>

    <el-empty v-if="!isLoading && isEmpty" description="暂无可查看统计的课程" />

    <div v-else class="table-scroll">
      <el-table :data="courses" v-loading="isLoading" stripe border @row-click="openDetail">
        <el-table-column label="课程" min-width="260">
          <template #default="{ row }">
            <div class="course-cell">
              <el-image :src="row.course_cover || ''" fit="cover" class="cover-image">
                <template #error>
                  <div class="cover-placeholder"><el-icon><VideoPlay /></el-icon></div>
                </template>
              </el-image>
              <div class="course-info">
                <span class="course-title">{{ row.course_title }}</span>
                <div class="course-tags">
                  <el-tag :type="row.permission_type === 'owner' ? 'success' : 'warning'" size="small">
                    {{ row.permission_type === 'owner' ? '负责人' : '被授权' }}
                  </el-tag>
                  <el-tag :type="statusMap[row.course_status]?.type || 'info'" size="small">
                    {{ statusMap[row.course_status]?.text || row.course_status }}
                  </el-tag>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="开始学习" width="110" align="center" prop="started_student_count" />
        <el-table-column label="7日活跃" width="110" align="center" prop="active_student_count_7d" />
        <el-table-column label="平均进度" width="110" align="center">
          <template #default="{ row }">{{ row.avg_progress.toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="完成率" width="110" align="center">
          <template #default="{ row }">{{ row.completion_rate.toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="累计时长" width="130" align="center">
          <template #default="{ row }">{{ formatDuration(row.total_duration_seconds) }}</template>
        </el-table-column>
        <el-table-column label="最近学习" width="170" align="center">
          <template #default="{ row }">{{ formatTime(row.recent_learn_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" :icon="TrendCharts" @click.stop="openDetail(row)">详情</el-button>
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
  </div>
</template>

<style lang="scss" scoped>
.teacher-statistics-page {
  .page-header {
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
  gap: 16px;
  flex-wrap: wrap;
}

.filter-left,
.filter-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
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
  gap: 6px;
}

.course-title {
  font-weight: 500;
  color: $text-primary;
}

.course-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .filter-left,
  .filter-right,
  .filter-actions {
    width: 100%;
  }

  .filter-right :deep(.el-input) {
    width: 100% !important;
  }
}
</style>
