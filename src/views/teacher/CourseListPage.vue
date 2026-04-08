<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, VideoPlay, Bottom, Delete, Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchMyCourses,
  publishCourse,
  archiveCourse,
  deleteCourse,
  type TeacherCourseItem,
  type TeacherCoursesParams,
} from '@/api/teacher'

const router = useRouter()

// 筛选状态
const statusFilter = ref<'all' | 'draft' | 'published' | 'archived'>('all')
const keyword = ref('')

// 获取课程列表
async function fetchCourses(params: TeacherCoursesParams) {
  return fetchMyCourses({
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

// 状态映射
const statusMap: Record<string, { text: string; type: 'info' | 'success' | 'danger' }> = {
  draft: { text: '草稿', type: 'info' },
  published: { text: '已发布', type: 'success' },
  archived: { text: '已下架', type: 'danger' },
}

// 格式化时间
function formatTime(time: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

// 格式化浏览量
function formatViewCount(count: number | undefined | null) {
  if (count == null) return '0'
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`
  }
  return count.toString()
}

// 创建课程
function handleCreate() {
  router.push('/teacher/courses/create')
}

// 编辑课程
function handleEdit(courseId: number) {
  router.push(`/teacher/courses/${courseId}/edit`)
}

// 发布课程
async function handlePublish(course: TeacherCourseItem) {
  try {
    await ElMessageBox.confirm(
      `确定要发布课程「${course.title}」吗？发布后将对所有学员可见。`,
      '发布确认',
      {
        confirmButtonText: '确定发布',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await publishCourse(course.course_id || course.id!)
    ElMessage.success('课程发布成功')
    fetchData()
  } catch (error) {
    // 用户取消或请求失败
  }
}

// 下架课程
async function handleArchive(course: TeacherCourseItem) {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      `确定要下架课程「${course.title}」吗？下架后学员将无法访问该课程。`,
      '下架原因',
      {
        confirmButtonText: '确定下架',
        cancelButtonText: '取消',
        inputType: 'textarea',
        inputPlaceholder: '请输入下架原因（10-200 字符）',
        inputValidator: (value) => {
          if (!value) return '请输入下架原因'
          if (value.length < 10) return '下架原因至少 10 个字符'
          if (value.length > 200) return '下架原因最多 200 个字符'
          return true
        },
      }
    )

    if (reason) {
      await archiveCourse(course.course_id || course.id!, { archive_reason: reason })
      ElMessage.success('课程已下架')
      fetchData()
    }
  } catch (error) {
    // 用户取消
  }
}

// 删除课程
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

    await deleteCourse(course.course_id || course.id!)
    ElMessage.success('课程已删除')
    fetchData()
  } catch (error) {
    // 用户取消
  }
}

// 搜索
function handleSearch() {
  page.value = 1
  fetchData()
}

// 重置筛选
function handleReset() {
  statusFilter.value = 'all'
  keyword.value = ''
  page.value = 1
  fetchData()
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="course-list-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">我的课程</h2>
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        创建课程
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-tabs v-model="statusFilter" @tab-change="() => fetchData()" class="status-tabs">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="草稿" name="draft" />
        <el-tab-pane label="已发布" name="published" />
        <el-tab-pane label="已下架" name="archived" />
      </el-tabs>

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

    <!-- 加载中 -->
    <div v-if="isLoading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="isEmpty" description="暂无课程，请先创建课程">
      <el-button type="primary" @click="handleCreate">创建课程</el-button>
    </el-empty>

    <!-- 课程列表 -->
    <template v-else>
      <el-table :data="courses" stripe border>
        <el-table-column label="封面" width="100" align="center">
          <template #default="{ row }">
            <el-image
              :src="row.cover_url"
              fit="cover"
              class="cover-image"
            >
              <template #error>
                <div class="cover-placeholder">
                  <el-icon><VideoPlay /></el-icon>
                </div>
              </template>
            </el-image>
          </template>
        </el-table-column>

        <el-table-column label="课程名称" min-width="200">
          <template #default="{ row }">
            <span class="course-title">{{ row.title }}</span>
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
            {{ formatTime(row.published_at || (row as any).publish_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" :icon="Edit" @click="handleEdit(row.course_id || row.id)">
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              text
              size="small"
              type="success"
              :icon="VideoPlay"
              @click="handlePublish(row)"
            >
              发布
            </el-button>
            <el-button
              v-if="row.status === 'published'"
              text
              size="small"
              type="warning"
              :icon="Bottom"
              @click="handleArchive(row)"
            >
              下架
            </el-button>
            <el-button
              v-if="row.status !== 'published'"
              text
              size="small"
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
            <el-tooltip v-if="row.status === 'published'" content="已发布课程需先下架" placement="top">
              <span>
                <el-button text size="small" type="danger" :icon="Delete" disabled>
                  删除
                </el-button>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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

.course-title {
  font-weight: 500;
  color: $text-primary;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>