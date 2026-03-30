<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, View, Check } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchFeedbacks,
  fetchFeedbackDetail,
  processFeedback,
  type AdminFeedbackItem,
  type AdminFeedbackDetail,
  type AdminFeedbacksParams,
} from '@/api/admin'

// 筛选状态
const typeFilter = ref<'all' | 'system' | 'course'>('all')
const statusFilter = ref<'all' | 'pending' | 'processed'>('all')
const keyword = ref('')

// 获取反馈列表
async function fetchFeedbackList(params: AdminFeedbacksParams) {
  return fetchFeedbacks({
    feedback_type: typeFilter.value === 'all' ? undefined : typeFilter.value,
    status: statusFilter.value === 'all' ? undefined : statusFilter.value,
    keyword: keyword.value || undefined,
    ...params,
  })
}

const {
  items: feedbacks,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  fetchData,
  goToPage,
} = usePagination<AdminFeedbackItem, AdminFeedbacksParams>(fetchFeedbackList, 10)

// 类型映射
const typeMap: Record<string, { text: string; type: 'primary' | 'success' }> = {
  system: { text: '系统问题', type: 'primary' },
  course: { text: '课程问题', type: 'success' },
}

// 状态映射
const statusMap: Record<string, { text: string; type: 'warning' | 'success' }> = {
  pending: { text: '待处理', type: 'warning' },
  processed: { text: '已处理', type: 'success' },
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

// 详情抽屉
const showDetailDrawer = ref(false)
const currentFeedback = ref<AdminFeedbackDetail | null>(null)
const isLoadingDetail = ref(false)

// 查看详情
async function handleViewDetail(feedback: AdminFeedbackItem) {
  isLoadingDetail.value = true
  showDetailDrawer.value = true
  try {
    const detail = await fetchFeedbackDetail(feedback.feedback_id)
    currentFeedback.value = detail
  } catch (error) {
    ElMessage.error('加载详情失败')
    showDetailDrawer.value = false
  } finally {
    isLoadingDetail.value = false
  }
}

// 标记已处理
async function handleProcess(feedback: AdminFeedbackItem) {
  try {
    await processFeedback(feedback.feedback_id)
    ElMessage.success('已标记为已处理')
    fetchData()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 批量处理
const selectedIds = ref<number[]>([])

function handleSelectionChange(selection: AdminFeedbackItem[]) {
  selectedIds.value = selection.map(item => item.feedback_id)
}

async function handleBatchProcess() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要处理的反馈')
    return
  }

  try {
    await Promise.all(selectedIds.value.map(id => processFeedback(id)))
    ElMessage.success('批量处理成功')
    selectedIds.value = []
    fetchData()
  } catch (error) {
    ElMessage.error('批量处理失败')
  }
}

// 搜索
function handleSearch() {
  page.value = 1
  fetchData()
}

// 重置筛选
function handleReset() {
  typeFilter.value = 'all'
  statusFilter.value = 'all'
  keyword.value = ''
  page.value = 1
  fetchData()
}

// 计算选中项中待处理的数量
const pendingSelectedCount = computed(() => {
  return selectedIds.value.filter(id => {
    const feedback = feedbacks.value.find(f => f.feedback_id === id)
    return feedback?.status === 'pending'
  }).length
})

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="feedback-manage-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">反馈管理</h2>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="typeFilter" placeholder="类型" style="width: 120px" @change="fetchData">
          <el-option label="全部类型" value="all" />
          <el-option label="系统问题" value="system" />
          <el-option label="课程问题" value="course" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态" style="width: 120px" @change="fetchData">
          <el-option label="全部状态" value="all" />
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="processed" />
        </el-select>
      </div>
      <div class="filter-right">
        <el-input
          v-model="keyword"
          placeholder="搜索反馈内容/用户名"
          clearable
          style="width: 200px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button @click="handleSearch">搜索</el-button>
        <el-button text @click="handleReset">重置</el-button>
      </div>
    </div>

    <!-- 批量操作 -->
    <div class="batch-actions" v-if="pendingSelectedCount > 0">
      <span class="selected-count">已选择 {{ pendingSelectedCount }} 条待处理反馈</span>
      <el-button type="primary" size="small" @click="handleBatchProcess">
        批量标记已处理
      </el-button>
    </div>

    <!-- 反馈表格 -->
    <el-table
      :data="feedbacks"
      v-loading="isLoading"
      stripe
      border
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="50" />
      <el-table-column prop="username" label="用户名" width="100" />
      <el-table-column label="反馈类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="typeMap[row.feedback_type]?.type || 'info'" size="small">
            {{ typeMap[row.feedback_type]?.text || row.feedback_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联课程" min-width="150">
        <template #default="{ row }">
          <span v-if="row.course_title">{{ row.course_title }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="反馈内容" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.content }}
        </template>
      </el-table-column>
      <el-table-column label="截图" width="80" align="center">
        <template #default="{ row }">
          <el-popover
            v-if="row.images?.length"
            placement="right"
            :width="400"
            trigger="hover"
          >
            <template #reference>
              <el-badge :value="row.images.length" type="primary">
                <el-button size="small" text>查看</el-button>
              </el-badge>
            </template>
            <div class="image-preview-list">
              <el-image
                v-for="(img, imgIndex) in row.images"
                :key="imgIndex"
                :src="img"
                :preview-src-list="row.images"
                :initial-index="Number(imgIndex)"
                fit="cover"
                class="preview-image"
              />
            </div>
          </el-popover>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
            {{ statusMap[row.status]?.text || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="提交时间" width="150" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" :icon="View" @click="handleViewDetail(row)">
            详情
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            text
            size="small"
            type="success"
            :icon="Check"
            @click="handleProcess(row)"
          >
            处理
          </el-button>
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

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" title="反馈详情" size="500px">
      <div v-if="isLoadingDetail" class="loading-container">
        <el-skeleton :rows="6" animated />
      </div>
      <template v-else-if="currentFeedback">
        <div class="detail-section">
          <div class="detail-row">
            <span class="detail-label">用户名</span>
            <span class="detail-value">{{ currentFeedback.username }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">反馈类型</span>
            <el-tag :type="typeMap[currentFeedback.feedback_type]?.type || 'info'">
              {{ typeMap[currentFeedback.feedback_type]?.text || currentFeedback.feedback_type }}
            </el-tag>
          </div>
          <div class="detail-row" v-if="currentFeedback.course_title">
            <span class="detail-label">关联课程</span>
            <span class="detail-value">{{ currentFeedback.course_title }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">处理状态</span>
            <el-tag :type="statusMap[currentFeedback.status]?.type || 'info'">
              {{ statusMap[currentFeedback.status]?.text || currentFeedback.status }}
            </el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">提交时间</span>
            <span class="detail-value">{{ formatTime(currentFeedback.created_at) }}</span>
          </div>
        </div>

        <el-divider>反馈内容</el-divider>
        <div class="feedback-content">
          {{ currentFeedback.content }}
        </div>

        <template v-if="currentFeedback.images?.length">
          <el-divider>截图</el-divider>
          <div class="image-list">
            <el-image
              v-for="(img, index) in currentFeedback.images"
              :key="index"
              :src="img"
              :preview-src-list="currentFeedback.images"
              :initial-index="index"
              fit="cover"
              class="feedback-image"
            />
          </div>
        </template>

        <div class="action-area" v-if="currentFeedback.status === 'pending'">
          <el-button type="primary" @click="handleProcess(currentFeedback)">
            标记为已处理
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style lang="scss" scoped>

.feedback-manage-page {
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
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;

  .filter-left {
    display: flex;
    gap: 12px;
  }

  .filter-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #e6f7ff;
  border-radius: $radius-sm;

  .selected-count {
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

.text-muted {
  color: $text-tertiary;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.image-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  .preview-image {
    width: 100px;
    height: 100px;
    border-radius: $radius-sm;
  }
}

.loading-container {
  padding: 24px;
}

.detail-section {
  .detail-row {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid $border-color-light;

    &:last-child {
      border-bottom: none;
    }
  }

  .detail-label {
    width: 80px;
    color: $text-secondary;
    flex-shrink: 0;
  }

  .detail-value {
    color: $text-primary;
  }
}

.feedback-content {
  padding: 16px;
  background: $bg-color;
  border-radius: $radius-sm;
  line-height: 1.6;
  color: $text-primary;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  .feedback-image {
    width: 100px;
    height: 100px;
    border-radius: $radius-sm;
  }
}

.action-area {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid $border-color-light;
}
</style>