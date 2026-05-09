<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import { deleteMyFeedback, fetchMyFeedbacks } from '@/api/profile'
import type { FeedbackItem } from '@/api/profile'
import FeedbackForm from '@/components/feedback/FeedbackForm.vue'
import UserIdentity from '@/components/common/UserIdentity.vue'

const route = useRoute()
const showSubmitDialog = ref(false)
const batchMode = ref(false)
const selectedFeedbackIds = ref<number[]>([])

const {
  items: feedbacks,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  isEmpty,
  fetchData,
  goToPage,
} = usePagination<FeedbackItem>(fetchMyFeedbacks, 10)

// 反馈类型映射
const typeMap: Record<string, { text: string; type: 'primary' | 'success' }> = {
  system: { text: '系统问题', type: 'primary' },
  course: { text: '课程问题', type: 'success' },
}

// 状态映射
const statusMap: Record<string, { text: string; type: 'warning' | 'success' }> = {
  pending: { text: '处理中', type: 'warning' },
  processed: { text: '已处理', type: 'success' },
}

const selectedCount = computed(() => selectedFeedbackIds.value.length)
const allSelectedOnPage = computed(() => {
  return feedbacks.value.length > 0
    && feedbacks.value.every((feedback) => selectedFeedbackIds.value.includes(feedback.feedback_id))
})

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

function hasTargetIdentity(feedback: FeedbackItem) {
  return Boolean(feedback.target_username || feedback.target_user_id)
}

function handleSubmitSuccess() {
  showSubmitDialog.value = false
  page.value = 1
  fetchData()
}

function isFeedbackSelected(feedbackId: number) {
  return selectedFeedbackIds.value.includes(feedbackId)
}

function toggleFeedbackSelection(feedbackId: number) {
  if (isFeedbackSelected(feedbackId)) {
    selectedFeedbackIds.value = selectedFeedbackIds.value.filter((id) => id !== feedbackId)
    return
  }
  selectedFeedbackIds.value = [...selectedFeedbackIds.value, feedbackId]
}

function enterBatchMode() {
  batchMode.value = true
  selectedFeedbackIds.value = []
}

function exitBatchMode() {
  batchMode.value = false
  selectedFeedbackIds.value = []
}

function handleToggleSelectAll() {
  if (allSelectedOnPage.value) {
    selectedFeedbackIds.value = []
    return
  }
  selectedFeedbackIds.value = feedbacks.value.map((feedback) => feedback.feedback_id)
}

async function refreshAfterDelete() {
  await fetchData()
  if (feedbacks.value.length === 0 && page.value > 1) {
    goToPage(page.value - 1)
  }
}

async function handleDeleteFeedback(feedback: FeedbackItem) {
  try {
    await ElMessageBox.confirm('确定要删除这条反馈记录吗？删除后将从列表中隐藏。', '删除反馈', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMyFeedback(feedback.feedback_id)
    ElMessage.success('反馈已删除')
    selectedFeedbackIds.value = selectedFeedbackIds.value.filter((id) => id !== feedback.feedback_id)
    await refreshAfterDelete()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleBatchDeleteFeedbacks() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要删除的反馈')
    return
  }

  const selectedFeedbacks = feedbacks.value.filter((feedback) => isFeedbackSelected(feedback.feedback_id))

  try {
    await ElMessageBox.confirm(
      `确定要删除已选择的 ${selectedFeedbacks.length} 条反馈吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const results = await Promise.allSettled(
      selectedFeedbacks.map((feedback) => deleteMyFeedback(feedback.feedback_id))
    )
    const successIds = selectedFeedbacks
      .filter((_, index) => results[index].status === 'fulfilled')
      .map((feedback) => feedback.feedback_id)
    const failureCount = results.length - successIds.length

    if (successIds.length > 0) {
      selectedFeedbackIds.value = selectedFeedbackIds.value.filter((id) => !successIds.includes(id))
      await refreshAfterDelete()
    }

    if (failureCount > 0) {
      if (successIds.length > 0) {
        ElMessage.warning(`已删除 ${successIds.length} 条，${failureCount} 条删除失败`)
      } else {
        ElMessage.error('批量删除失败，请稍后重试')
      }
      return
    }

    ElMessage.success(`已删除 ${successIds.length} 条反馈`)
    exitBatchMode()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('批量删除失败')
    }
  }
}

watch(feedbacks, (currentFeedbacks) => {
  const currentIds = new Set(currentFeedbacks.map((feedback) => feedback.feedback_id))
  selectedFeedbackIds.value = selectedFeedbackIds.value.filter((id) => currentIds.has(id))
})

// 初始化加载
onMounted(() => {
  fetchData()
})

watch(() => route.query.refresh, () => {
  fetchData()
})
</script>

<template>
  <div class="my-feedbacks-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">我的反馈</h2>
        <p class="page-desc">提交平台/系统问题反馈，并查看管理员处理回复。</p>
      </div>
      <div class="header-actions">
        <span class="total-count">共 {{ total }} 条反馈</span>
        <template v-if="batchMode">
          <el-button
            class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
            @click="handleToggleSelectAll"
          >
            {{ allSelectedOnPage ? '取消全选' : '全选当前页' }}
          </el-button>
          <el-button
            class="soft-action-btn soft-action-btn--danger soft-action-btn--small"
            type="danger"
            :disabled="selectedCount === 0"
            @click="handleBatchDeleteFeedbacks"
          >
            批量删除
          </el-button>
          <el-button
            class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
            @click="exitBatchMode"
          >
            取消管理
          </el-button>
        </template>
        <template v-else>
          <el-button
            class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
            :disabled="total === 0"
            @click="enterBatchMode"
          >
            批量管理
          </el-button>
          <el-button
            class="soft-action-btn soft-action-btn--primary soft-action-btn--small"
            type="primary"
            @click="showSubmitDialog = true"
          >
            提交平台反馈
          </el-button>
        </template>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="isEmpty" description="暂无反馈记录">
      <template #image>
        <el-icon :size="64" color="#ccc"><ChatDotRound /></el-icon>
      </template>
    </el-empty>

    <!-- 反馈列表 -->
    <template v-else>
      <div v-if="batchMode" class="batch-toolbar">
        <span class="batch-toolbar__text">已选择 {{ selectedCount }} 条反馈</span>
        <span class="batch-toolbar__hint">选择反馈后可批量删除</span>
      </div>

      <div class="feedback-list" v-loading="isLoading">
        <div
          v-for="feedback in feedbacks"
          :key="feedback.feedback_id"
          class="feedback-card"
          :class="{ 'is-batch-mode': batchMode, 'is-selected': isFeedbackSelected(feedback.feedback_id) }"
        >
          <div v-if="batchMode" class="card-select">
            <el-checkbox
              :model-value="isFeedbackSelected(feedback.feedback_id)"
              @change="toggleFeedbackSelection(feedback.feedback_id)"
            />
          </div>
          <div class="card-body">
            <!-- 卡片头部 -->
            <div class="card-header">
              <div class="header-tags">
                <el-tag :type="typeMap[feedback.feedback_type]?.type || 'info'" size="small">
                  {{ typeMap[feedback.feedback_type]?.text || feedback.feedback_type }}
                </el-tag>
                <el-tag
                  :type="statusMap[feedback.status]?.type || 'info'"
                  size="small"
                >
                  {{ statusMap[feedback.status]?.text || feedback.status }}
                </el-tag>
              </div>
              <div class="card-header-right">
                <span class="feedback-time">{{ formatTime(feedback.created_at) }}</span>
                <el-button
                  v-if="!batchMode"
                  text
                  type="danger"
                  :icon="Delete"
                  @click="handleDeleteFeedback(feedback)"
                >
                  删除
                </el-button>
              </div>
            </div>

            <!-- 反馈内容 -->
            <p class="feedback-content">
              {{ feedback.content }}
            </p>

            <!-- 关联课程 -->
            <p class="feedback-course" v-if="feedback.course_title">
              <el-icon><Link /></el-icon>
              关联课程：{{ feedback.course_title }}
            </p>

            <p class="feedback-course" v-if="hasTargetIdentity(feedback)">
              <el-icon><User /></el-icon>
              <span>反馈给：</span>
              <UserIdentity
                :username="feedback.target_username"
                :user-id="feedback.target_user_id"
                fallback="用户"
                compact
              />
            </p>

            <div v-if="feedback.reply" class="feedback-reply">
              <div class="feedback-reply__header">
                <span class="feedback-reply__title">处理回复</span>
                <span v-if="feedback.replied_at" class="feedback-reply__time">
                  {{ formatTime(feedback.replied_at) }}
                </span>
              </div>
              <p class="feedback-reply__content">{{ feedback.reply }}</p>
            </div>

            <!-- 图片列表 -->
            <div class="feedback-images" v-if="feedback.images?.length">
              <el-image
                v-for="(img, index) in feedback.images.slice(0, 4)"
                :key="index"
                :src="img"
                :preview-src-list="feedback.images"
                :initial-index="index"
                fit="cover"
                class="feedback-image"
                lazy
              >
                <template #error>
                  <div class="image-placeholder">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div
                v-if="feedback.images.length > 4"
                class="more-images"
              >
                +{{ feedback.images.length - 4 }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="totalPages > 1"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper"
        class="pagination"
        @current-change="goToPage"
      />
    </template>

    <el-dialog
      v-model="showSubmitDialog"
      title="提交平台反馈"
      width="560px"
      :close-on-click-modal="false"
    >
      <FeedbackForm
        mode="dialog"
        default-type="system"
        type-locked
        @success="handleSubmitSuccess"
        @cancel="showSubmitDialog = false"
      />
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.my-feedbacks-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }

  .page-desc {
    margin: 8px 0 0;
    color: #666;
    font-size: 14px;
    line-height: 1.6;
  }

  .header-actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    padding: 4px;
    background: #f4f8ff;
    border: 1px solid #dbeafe;
    border-radius: 999px;
  }

  .soft-action-btn--danger {
    border-color: transparent !important;
    background: transparent !important;
    color: #dc2626 !important;

    &:hover,
    &:focus {
      border-color: #fecaca !important;
      background: #fff5f5 !important;
      color: #b91c1c !important;
    }
  }

  .total-count {
    padding: 0 8px;
    font-size: 14px;
    color: #666;
    white-space: nowrap;
  }
}

.feedback-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 12px 16px;
  background: #f5f9ff;
  border: 1px solid #d6e8ff;
  border-radius: 12px;
}

.batch-toolbar__text {
  color: #1d4f91;
  font-size: 14px;
  font-weight: 700;
}

.batch-toolbar__hint {
  color: #5f6f85;
  font-size: 13px;
}

.feedback-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fafafa;
  border: 1px solid transparent;
  border-radius: 8px;
  transition: all 0.2s ease;

  &:hover {
    background: #f0f7ff;
  }

  &.is-selected {
    border-color: #2563eb;
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
  }
}

.card-select {
  padding-top: 2px;
  flex-shrink: 0;
}

.card-body {
  min-width: 0;
  flex: 1;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.header-tags {
  display: flex;
  gap: 8px;
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.feedback-time {
  font-size: 12px;
  color: #999;
}

.feedback-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feedback-course {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.feedback-reply {
  margin: 0 0 12px;
  padding: 12px 14px;
  background: #f0f7ff;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}

.feedback-reply__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.feedback-reply__title {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
}

.feedback-reply__time {
  font-size: 12px;
  color: #999;
}

.feedback-reply__content {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}

.feedback-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.feedback-image {
  width: 80px;
  height: 80px;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #ccc;
}

.more-images {
  width: 80px;
  height: 80px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .my-feedbacks-page {
    .page-header {
      align-items: flex-start;
      flex-direction: column;
      gap: 12px;
    }

    .header-actions {
      width: 100%;
      justify-content: space-between;
      border-radius: 14px;
    }

    .header-actions :deep(.el-button) {
      margin-left: 0;
    }
  }

  .batch-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .feedback-card {
    padding: 14px;
  }

  .card-header-right {
    align-items: flex-start;
    flex-direction: column;
  }

  .feedback-card.is-batch-mode {
    position: relative;
    padding-right: 44px;
  }

  .card-select {
    position: absolute;
    top: 14px;
    right: 14px;
    padding-top: 0;
  }

  .card-header,
  .feedback-reply__header {
    align-items: flex-start;
    flex-direction: column;
  }

}
</style>