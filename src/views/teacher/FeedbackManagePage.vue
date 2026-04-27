<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ChatDotRound, Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchTeacherFeedbackDetail,
  fetchTeacherFeedbacks,
  processTeacherFeedback,
  type TeacherFeedbackDetail,
  type TeacherFeedbackItem,
  type TeacherFeedbacksParams,
} from '@/api/teacher'

const statusFilter = ref<'all' | 'pending' | 'processed'>('all')
const keyword = ref('')

async function fetchFeedbackList(params: TeacherFeedbacksParams) {
  return fetchTeacherFeedbacks({
    status: statusFilter.value,
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
} = usePagination<TeacherFeedbackItem, TeacherFeedbacksParams>(fetchFeedbackList, 10)

const statusMap: Record<string, { text: string; type: 'warning' | 'success' }> = {
  pending: { text: '待处理', type: 'warning' },
  processed: { text: '已处理', type: 'success' },
}

const showDetailDrawer = ref(false)
const currentFeedback = ref<TeacherFeedbackDetail | null>(null)
const isLoadingDetail = ref(false)

const showProcessDialog = ref(false)
const processTarget = ref<TeacherFeedbackItem | TeacherFeedbackDetail | null>(null)
const processFormRef = ref<FormInstance>()
const processForm = ref({ reply: '' })
const isSubmitting = ref(false)

const processRules: FormRules = {
  reply: [
    { required: true, message: '请输入回复内容', trigger: 'blur' },
    { min: 2, max: 1000, message: '回复内容长度需在 2-1000 个字符之间', trigger: 'blur' },
  ],
}

const pendingCount = computed(() => feedbacks.value.filter((item) => item.status === 'pending').length)

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

async function loadFeedbackDetail(feedbackId: number) {
  const detail = await fetchTeacherFeedbackDetail(feedbackId)
  currentFeedback.value = detail
  return detail
}

async function handleViewDetail(feedback: TeacherFeedbackItem) {
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

function handleRowClick(row: TeacherFeedbackItem, column?: { property?: string }) {
  if (column?.property === '__actions') return
  handleViewDetail(row)
}

function openProcessDialog(feedback: TeacherFeedbackItem | TeacherFeedbackDetail) {
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
    const detail = await processTeacherFeedback(processTarget.value.feedback_id, {
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

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="teacher-feedback-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">课程反馈</h2>
        <p class="page-desc">处理学生提交到你负责课程的视频、学习和课程问题。</p>
      </div>
      <el-tag v-if="pendingCount > 0" type="warning">{{ pendingCount }} 条待处理</el-tag>
    </div>

    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="状态" style="width: 120px" @change="fetchData">
        <el-option label="全部状态" value="all" />
        <el-option label="待处理" value="pending" />
        <el-option label="已处理" value="processed" />
      </el-select>
      <div class="filter-right">
        <el-input
          v-model="keyword"
          placeholder="搜索反馈内容/课程名/学生"
          clearable
          style="width: 240px"
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

    <el-table
      :data="feedbacks"
      v-loading="isLoading"
      stripe
      border
      class="feedback-table"
      @row-click="handleRowClick"
    >
      <el-table-column prop="username" label="学生" width="120">
        <template #default="{ row }">
          {{ row.username || `用户${row.user_id}` }}
        </template>
      </el-table-column>
      <el-table-column label="关联课程" min-width="160">
        <template #default="{ row }">
          {{ row.course_title || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="反馈给" width="120">
        <template #default="{ row }">
          {{ row.target_nickname || row.target_username || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="反馈内容" min-width="240" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.content }}
        </template>
      </el-table-column>
      <el-table-column label="截图" width="80" align="center">
        <template #default="{ row }">
          <el-popover v-if="row.images?.length" placement="right" :width="400" trigger="hover">
            <template #reference>
              <el-badge :value="row.images.length" type="primary" @click.stop>
                <el-button size="small" text @click.stop>查看</el-button>
              </el-badge>
            </template>
            <div class="image-preview-list">
              <el-image
                v-for="(img, index) in row.images"
                :key="index"
                :src="img"
                :preview-src-list="row.images"
                :initial-index="Number(index)"
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
      <el-table-column label="提交时间" width="160" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right" prop="__actions">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending'"
            text
            size="small"
            type="success"
            :icon="ChatDotRound"
            @click.stop="openProcessDialog(row)"
          >
            回复处理
          </el-button>
          <span v-else class="text-muted">-</span>
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

    <el-drawer v-model="showDetailDrawer" title="课程反馈详情" size="500px">
      <div v-if="isLoadingDetail" class="loading-container">
        <el-skeleton :rows="6" animated />
      </div>
      <template v-else-if="currentFeedback">
        <div class="detail-section">
          <div class="detail-row">
            <span class="detail-label">学生</span>
            <span class="detail-value">{{ currentFeedback.username || `用户${currentFeedback.user_id}` }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">关联课程</span>
            <span class="detail-value">{{ currentFeedback.course_title || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">反馈给</span>
            <span class="detail-value">{{ currentFeedback.target_nickname || currentFeedback.target_username || '-' }}</span>
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
        <div class="feedback-content">{{ currentFeedback.content }}</div>

        <template v-if="currentFeedback.reply">
          <el-divider>老师回复</el-divider>
          <div class="reply-content">{{ currentFeedback.reply }}</div>
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

    <el-dialog v-model="showProcessDialog" title="回复并处理" width="520px" @closed="resetProcessDialog">
      <template v-if="processTarget">
        <div class="process-summary">
          <div class="process-summary__row">
            <span class="process-summary__label">关联课程</span>
            <span>{{ processTarget.course_title || '-' }}</span>
          </div>
          <div class="process-summary__row process-summary__row--block">
            <span class="process-summary__label">反馈内容</span>
            <div class="process-summary__content">{{ processTarget.content }}</div>
          </div>
        </div>

        <el-form ref="processFormRef" :model="processForm" :rules="processRules" label-position="top">
          <el-form-item label="回复内容" prop="reply">
            <el-input
              v-model="processForm.reply"
              type="textarea"
              :rows="5"
              maxlength="1000"
              show-word-limit
              placeholder="请输入给学生的处理回复"
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
.teacher-feedback-page {
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
}

.filter-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feedback-table {
  :deep(.el-table__row) {
    cursor: pointer;
  }

  :deep(.el-table__cell:last-child) {
    cursor: default;
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

.feedback-content,
.reply-content {
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
  display: flex;
  justify-content: flex-end;
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
    min-width: 64px;
    color: $text-secondary;
  }

  &__content {
    padding: 12px;
    background: $bg-color;
    border-radius: $radius-sm;
    line-height: 1.6;
  }
}

@media (max-width: 768px) {
  .teacher-feedback-page .page-header,
  .filter-bar,
  .filter-right {
    align-items: stretch;
    flex-direction: column;
  }

  .filter-right :deep(.el-input) {
    width: 100% !important;
  }
}
</style>
