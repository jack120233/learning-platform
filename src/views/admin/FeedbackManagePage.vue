<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Search, ChatDotRound } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchFeedbacks,
  fetchFeedbackDetail,
  processFeedback,
  batchProcessFeedbacks,
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
function formatTime(time: string | null | undefined) {
  if (!time) return '-'
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

async function loadFeedbackDetail(feedbackId: number) {
  const detail = await fetchFeedbackDetail(feedbackId)
  currentFeedback.value = detail
  return detail
}

// 查看详情
async function handleViewDetail(feedback: AdminFeedbackItem) {
  isLoadingDetail.value = true
  showDetailDrawer.value = true
  try {
    await loadFeedbackDetail(feedback.feedback_id)
  } catch (error) {
    ElMessage.error('加载详情失败')
    showDetailDrawer.value = false
  } finally {
    isLoadingDetail.value = false
  }
}

function handleRowClick(row: AdminFeedbackItem, column?: { type?: string; property?: string }) {
  if (!column || column.type === 'selection' || column.property === '__actions') {
    return
  }
  handleViewDetail(row)
}

// 处理弹窗
const showProcessDialog = ref(false)
const processTarget = ref<AdminFeedbackItem | AdminFeedbackDetail | null>(null)
const processFormRef = ref<FormInstance>()
const processForm = ref({
  reply: '',
})
const isSubmitting = ref(false)

const processRules: FormRules = {
  reply: [
    { required: true, message: '请输入回复内容', trigger: 'blur' },
    { min: 2, max: 1000, message: '回复内容长度需在 2-1000 个字符之间', trigger: 'blur' },
  ],
}

function openProcessDialog(feedback: AdminFeedbackItem | AdminFeedbackDetail) {
  processTarget.value = feedback
  processForm.value.reply = feedback.reply || ''
  showProcessDialog.value = true
}

function resetProcessDialog() {
  processTarget.value = null
  processForm.value.reply = ''
  processFormRef.value?.clearValidate()
}

async function handleSubmitProcess() {
  if (!processTarget.value) return

  try {
    await processFormRef.value?.validate()
  } catch {
    return
  }

  isSubmitting.value = true
  try {
    const detail = await processFeedback(processTarget.value.feedback_id, {
      reply: processForm.value.reply.trim(),
    })

    if (currentFeedback.value?.feedback_id === detail.feedback_id) {
      currentFeedback.value = detail
    }

    showProcessDialog.value = false
    ElMessage.success('回复并处理成功')
    await fetchData()
  } catch (error) {
    ElMessage.error('处理失败')
  } finally {
    isSubmitting.value = false
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
    const processedIds = [...selectedIds.value]
    await batchProcessFeedbacks(processedIds)
    ElMessage.success('批量处理成功')
    selectedIds.value = []
    if (currentFeedback.value && processedIds.includes(currentFeedback.value.feedback_id)) {
      await loadFeedbackDetail(currentFeedback.value.feedback_id)
    }
    await fetchData()
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
      class="feedback-table"
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
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
              <el-badge :value="row.images.length" type="primary" @click.stop>
                <el-button size="small" text @click.stop>查看</el-button>
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
      <el-table-column label="回复状态" width="110" align="center">
        <template #default="{ row }">
          <span v-if="row.reply" class="reply-status">已回复</span>
          <span v-else class="text-muted">未回复</span>
        </template>
      </el-table-column>
      <el-table-column label="提交时间" width="150" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right" prop="__actions">
        <template #default="{ row }">
          <div class="action-buttons" @click.stop>
            <el-button
              v-if="row.status === 'pending'"
              text
              size="small"
              type="success"
              :icon="ChatDotRound"
              @click.stop="openProcessDialog(row)"
            >
              回复并处理
            </el-button>
            <span v-else class="text-muted">-</span>
          </div>
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
          <div class="detail-row" v-if="currentFeedback.replied_at">
            <span class="detail-label">回复时间</span>
            <span class="detail-value">{{ formatTime(currentFeedback.replied_at) }}</span>
          </div>
        </div>

        <el-divider>反馈内容</el-divider>
        <div class="feedback-content">
          {{ currentFeedback.content }}
        </div>

        <template v-if="currentFeedback.reply">
          <el-divider>管理员回复</el-divider>
          <div class="reply-content">
            {{ currentFeedback.reply }}
          </div>
        </template>

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
          <el-button type="primary" :icon="ChatDotRound" @click="openProcessDialog(currentFeedback)">
            回复并处理
          </el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog
      v-model="showProcessDialog"
      title="回复并处理"
      width="520px"
      @closed="resetProcessDialog"
    >
      <template v-if="processTarget">
        <div class="process-summary">
          <div class="process-summary__row">
            <span class="process-summary__label">反馈类型</span>
            <span>{{ typeMap[processTarget.feedback_type]?.text || processTarget.feedback_type }}</span>
          </div>
          <div class="process-summary__row" v-if="processTarget.course_title">
            <span class="process-summary__label">关联课程</span>
            <span>{{ processTarget.course_title }}</span>
          </div>
          <div class="process-summary__row process-summary__row--block">
            <span class="process-summary__label">反馈内容</span>
            <div class="process-summary__content">{{ processTarget.content }}</div>
          </div>
        </div>

        <el-form
          ref="processFormRef"
          :model="processForm"
          :rules="processRules"
          label-position="top"
        >
          <el-form-item label="回复内容" prop="reply">
            <el-input
              v-model="processForm.reply"
              type="textarea"
              :rows="5"
              maxlength="1000"
              show-word-limit
              placeholder="请输入给用户的处理回复"
            />
          </el-form-item>
        </el-form>
      </template>

      <template #footer>
        <el-button @click="showProcessDialog = false">取消</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="handleSubmitProcess">
          确认处理
        </el-button>
      </template>
    </el-dialog>
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

.feedback-table {
  :deep(.el-table__row) {
    cursor: pointer;
  }

  :deep(.el-table__cell:first-child),
  :deep(.el-table__cell:last-child) {
    cursor: default;
  }
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 24px;
}

.reply-status {
  color: $success-color;
  font-weight: 500;
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

.feedback-content,
.reply-content {
  padding: 16px;
  background: $bg-color;
  border-radius: $radius-sm;
  line-height: 1.6;
  color: $text-primary;
}

.process-summary {
  margin-bottom: 16px;
  padding: 16px;
  background: $bg-white;
  border-radius: $radius-sm;

  &__row {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
    color: $text-primary;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__row--block {
    flex-direction: column;
    gap: 8px;
  }

  &__label {
    color: $text-secondary;
    min-width: 72px;
    flex-shrink: 0;
  }

  &__content {
    padding: 12px;
    border-radius: $radius-sm;
    background: $bg-color;
    line-height: 1.6;
  }
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

@media (max-width: 768px) {
  .filter-bar {
    .filter-left,
    .filter-right {
      width: 100%;
      flex-wrap: wrap;
    }
  }

  .feedback-table {
    :deep(.el-button) {
      padding-left: 0;
      padding-right: 0;
    }
  }
}
</style>