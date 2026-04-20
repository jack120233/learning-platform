<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { usePagination } from '@/composables/usePagination'
import { useBreakpoint } from '@/composables/useBreakpoint'
import {
  fetchMessages,
  markAsRead,
  markAllRead,
  deleteMessage,
  fetchUnreadCount,
} from '@/api/profile'
import type { MessagesParams, MessageItem, MessageDetail } from '@/api/profile'
import { fetchMessageDetail } from '@/api/profile'
import UnreadLabelBadge from '@/components/common/UnreadLabelBadge.vue'

// 定义组件名称（用于 keep-alive）
defineOptions({
  name: 'ProfileMessages',
})

const userStore = useUserStore()
const { isMobile } = useBreakpoint()

// 筛选状态
const messageType = ref<'all' | 'announcement' | 'notification'>('all')
const isRead = ref<boolean | undefined>(undefined)

// 获取消息列表
async function fetchMessagesList(params: MessagesParams) {
  const response = await fetchMessages({
    message_type: messageType.value,
    is_read: isRead.value,
    ...params,
  })
  unreadCount.value = response.unread_count
  userStore.setUnreadCount(response.unread_count)
  return response
}

// 分页 Hook
const {
  items: messages,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  isEmpty,
  fetchData,
  goToPage,
  refresh,
} = usePagination<MessageItem, MessagesParams>(
  fetchMessagesList,
  10
)

// 未读消息数（从响应中获取）
const unreadCount = ref(0)

// 消息详情抽屉
const detailDrawer = ref(false)
const currentMessage = ref<MessageDetail | null>(null)
const detailLoading = ref(false)
const batchMode = ref(false)
const selectedIds = ref<number[]>([])

const selectedCount = computed(() => selectedIds.value.length)
const allSelectedOnPage = computed(() => {
  return messages.value.length > 0
    && messages.value.every((message) => selectedIds.value.includes(message.message_id))
})
const detailDialogWidth = computed(() => (isMobile.value ? '94%' : '760px'))
const detailDialogTop = computed(() => (isMobile.value ? '10vh' : '8vh'))

// 消息类型映射
const typeMap: Record<string, { text: string; type: 'primary' | 'success' }> = {
  announcement: { text: '公告', type: 'primary' },
  notification: { text: '通知', type: 'success' },
}

// 类型筛选选项
const typeOptions = [
  { label: '全部', value: 'all' as const },
  { label: '系统通知', value: 'notification' as const },
  { label: '公告', value: 'announcement' as const },
]

// 状态筛选选项
const statusOptions = [
  { label: '全部', value: undefined as boolean | undefined },
  { label: '未读', value: false as boolean | undefined },
  { label: '已读', value: true as boolean | undefined },
]

// 处理类型变化
function handleTypeChange() {
  fetchData(true)
}

// 处理状态变化
function handleStatusChange() {
  fetchData(true)
}

function isSelected(messageId: number) {
  return selectedIds.value.includes(messageId)
}

function toggleSelection(messageId: number) {
  if (isSelected(messageId)) {
    selectedIds.value = selectedIds.value.filter((id) => id !== messageId)
    return
  }
  selectedIds.value = [...selectedIds.value, messageId]
}

function enterBatchMode() {
  batchMode.value = true
  selectedIds.value = []
}

function exitBatchMode() {
  batchMode.value = false
  selectedIds.value = []
}

function handleToggleSelectAll() {
  if (allSelectedOnPage.value) {
    selectedIds.value = []
    return
  }
  selectedIds.value = messages.value.map((message) => message.message_id)
}

function handleCardClick(message: MessageItem) {
  if (batchMode.value) {
    toggleSelection(message.message_id)
    return
  }
  handleView(message)
}

// 查看消息详情
async function handleView(message: MessageItem) {
  detailLoading.value = true
  detailDrawer.value = true

  try {
    // 获取详情
    const detail = await fetchMessageDetail(message.message_id)
    currentMessage.value = detail

    // 如果是未读，标记为已读
    if (!message.is_read) {
      await markAsRead(message.message_id)
      message.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      userStore.setUnreadCount(unreadCount.value)
    }
  } catch (error) {
    detailDrawer.value = false
  } finally {
    detailLoading.value = false
  }
}

async function syncUnreadCount() {
  try {
    const response = await fetchUnreadCount()
    unreadCount.value = response.unread_count
    userStore.setUnreadCount(response.unread_count)
  } catch (error) {
    // 保持页面可用，忽略同步失败
  }
}

// 批量标记已读
async function handleMarkAllRead() {
  try {
    await markAllRead()
    ElMessage.success('已全部标为已读')

    // 刷新列表
    await refresh()

    // 更新未读数
    unreadCount.value = 0
    userStore.setUnreadCount(0)
  } catch (error) {
    // 错误已处理
  }
}

// 删除消息
async function handleDelete(message: MessageItem) {
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await deleteMessage(message.message_id)
    ElMessage.success('删除成功')

    // 如果是未读消息，更新未读数
    if (!message.is_read) {
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      userStore.setUnreadCount(unreadCount.value)
    }

    // 刷新列表
    await refreshAfterMutation()
  } catch (error) {
    // 用户取消或请求失败
  }
}

async function handleBatchDelete() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要删除的消息')
    return
  }

  const selectedMessages = messages.value.filter((message) => isSelected(message.message_id))

  try {
    await ElMessageBox.confirm(
      `确定要删除已选择的 ${selectedMessages.length} 条消息吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await Promise.all(
      selectedMessages.map((message) => deleteMessage(message.message_id))
    )

    const unreadDeletedCount = selectedMessages.filter((message) => !message.is_read).length
    if (unreadDeletedCount > 0) {
      unreadCount.value = Math.max(0, unreadCount.value - unreadDeletedCount)
      userStore.setUnreadCount(unreadCount.value)
    }

    ElMessage.success(`已删除 ${selectedMessages.length} 条消息`)
    selectedIds.value = []
    await refreshAfterMutation()
  } catch (error) {
    // 用户取消或请求失败
  }
}

async function refreshAfterMutation() {
  await refresh()
  if (messages.value.length === 0 && page.value > 1) {
    await goToPage(page.value - 1)
  }
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

// 初始化加载
onMounted(async () => {
  await syncUnreadCount()
  await fetchData()
})

watch(messages, (currentMessages) => {
  const currentIds = new Set(currentMessages.map((message) => message.message_id))
  selectedIds.value = selectedIds.value.filter((id) => currentIds.has(id))
})
</script>

<template>
  <div class="messages-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <UnreadLabelBadge label="消息中心" :count="unreadCount" />
        </h2>
      </div>
      <div class="header-actions">
        <template v-if="batchMode">
          <el-button @click="handleToggleSelectAll">
            {{ allSelectedOnPage ? '取消全选' : '全选当前页' }}
          </el-button>
          <el-button
            type="danger"
            plain
            :disabled="selectedCount === 0"
            @click="handleBatchDelete"
          >
            批量删除
          </el-button>
          <el-button @click="exitBatchMode">
            取消管理
          </el-button>
        </template>
        <template v-else>
          <el-button
            type="primary"
            plain
            :disabled="unreadCount === 0"
            @click="handleMarkAllRead"
          >
            全部标为已读
          </el-button>
          <el-button plain @click="enterBatchMode">
            批量管理
          </el-button>
        </template>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <span class="filter-label">类型：</span>
        <el-radio-group v-model="messageType" @change="handleTypeChange" size="small">
          <el-radio-button
            v-for="option in typeOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </el-radio-button>
        </el-radio-group>
      </div>

      <div class="filter-group">
        <span class="filter-label">状态：</span>
        <el-radio-group v-model="isRead" @change="handleStatusChange" size="small">
          <el-radio-button
            v-for="option in statusOptions"
            :key="String(option.value)"
            :value="option.value"
          >
            {{ option.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="isEmpty" description="暂无消息" />

    <!-- 消息列表 -->
    <template v-else>
      <div v-if="batchMode" class="batch-toolbar">
        <span class="batch-toolbar__text">
          已选择 {{ selectedCount }} 条消息
        </span>
        <span class="batch-toolbar__hint">
          选择消息后可批量删除，点击卡片可直接勾选
        </span>
      </div>

      <div class="message-list" v-loading="isLoading">
        <div
          v-for="message in messages"
          :key="message.message_id"
          class="message-card"
          :class="{ unread: !message.is_read }"
          @click="handleCardClick(message)"
        >
          <div v-if="batchMode" class="message-select" @click.stop>
            <el-checkbox
              :model-value="isSelected(message.message_id)"
              @change="toggleSelection(message.message_id)"
            />
          </div>

          <div class="message-main">
            <div class="message-header-row">
              <div class="message-heading">
                <el-tag
                  :type="typeMap[message.message_type]?.type || 'info'"
                  size="small"
                >
                  {{ typeMap[message.message_type]?.text || message.message_type }}
                </el-tag>
                <h4 class="message-title" :class="{ 'is-unread': !message.is_read }">
                  {{ message.title }}
                </h4>
                <span v-if="!message.is_read" class="message-read-status">未读</span>
              </div>
              <span class="message-time">{{ formatTime(message.created_at) }}</span>
            </div>

            <p class="message-summary">{{ message.content }}</p>
          </div>

          <div class="message-actions">
            <el-button
              class="delete-button"
              type="danger"
              text
              circle
              :icon="Delete"
              @click.stop="handleDelete(message)"
            />
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

    <!-- 消息详情 -->
    <el-dialog
      v-model="detailDrawer"
      class="message-detail-dialog"
      :class="{ 'mobile-message-detail-dialog': isMobile }"
      title="消息详情"
      :width="detailDialogWidth"
      :top="detailDialogTop"
      append-to-body
    >
      <div class="message-detail" v-loading="detailLoading">
        <template v-if="currentMessage">
          <div class="detail-header">
            <el-tag
              :type="typeMap[currentMessage.message_type]?.type || 'info'"
              size="small"
            >
              {{ typeMap[currentMessage.message_type]?.text }}
            </el-tag>
            <span class="detail-time">
              {{ formatTime(currentMessage.created_at) }}
            </span>
          </div>

          <h3 class="detail-title">{{ currentMessage.title }}</h3>

          <div class="detail-content">
            {{ currentMessage.content }}
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.messages-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .header-left {
    display: flex;
    align-items: center;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }
}

.filter-bar {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #666;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f9ff;
  border: 1px solid #d6e8ff;
  border-radius: 8px;
}

.batch-toolbar__text {
  font-size: 14px;
  font-weight: 600;
  color: #1d4f91;
}

.batch-toolbar__hint {
  font-size: 13px;
  color: #5f6f85;
}

.message-card {
  position: relative;
  display: flex;
  align-items: stretch;
  gap: 14px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
  }

  &.unread {
    background: #f6ffed;
    border-left: 3px solid #1890ff;
  }
}

.message-select {
  display: flex;
  align-items: center;
  padding-top: 2px;
}

.message-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.message-heading {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.message-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin: 0;

  &.is-unread {
    font-weight: 600;
  }
}

.message-read-status {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: #e8f3ff;
  color: #1677ff;
  font-size: 12px;
  font-weight: 500;
}

.message-summary {
  font-size: 14px;
  color: #666;
  margin: 0;
  line-height: 1.7;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  max-width: none;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.message-time {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  padding-top: 2px;
}

.message-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: stretch;
}

.delete-button {
  color: #f56c6c;

  &:hover {
    background: rgba(245, 108, 108, 0.12);
  }
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

// 消息详情抽屉
.message-detail {
  padding: 0 16px;
  max-height: min(72vh, 720px);
  overflow-y: auto;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-time {
  font-size: 14px;
  color: #999;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  line-height: 1.6;
  white-space: normal;
  overflow-wrap: anywhere;
  margin: 0 0 16px;
}

.detail-content {
  font-size: 15px;
  color: #666;
  line-height: 1.8;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

:deep(.message-detail-dialog) {
  --el-dialog-border-radius: 18px;
}

:deep(.message-detail-dialog .el-dialog) {
  max-width: min(94vw, 760px);
  margin-left: auto;
  margin-right: auto;
}

:deep(.message-detail-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 18px 20px 10px;
}

:deep(.message-detail-dialog .el-dialog__body) {
  padding: 0 0 20px;
}

:deep(.mobile-message-detail-dialog) {
  --el-dialog-border-radius: 18px;
}

:deep(.mobile-message-detail-dialog .el-dialog) {
  max-width: 420px;
}

:deep(.mobile-message-detail-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 16px 18px 8px;
}

:deep(.mobile-message-detail-dialog .el-dialog__body) {
  padding: 0 0 18px;
}

// 响应式
@media (max-width: 768px) {
  .page-header {
    align-items: flex-start;
    gap: 12px;
  }

  .batch-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .message-card {
    gap: 12px;
    padding: 14px;
  }

  .message-header-row {
    flex-direction: column;
    gap: 8px;
  }

  .message-heading {
    gap: 8px;
  }

  .message-summary {
    max-width: 100%;
  }

  .message-actions {
    align-self: flex-start;
  }
}
</style>
