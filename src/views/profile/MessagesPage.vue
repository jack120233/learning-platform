<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import { usePagination } from '@/composables/usePagination'
import {
  fetchMessages,
  markAsRead,
  markAllRead,
  deleteMessage,
} from '@/api/profile'
import type { MessagesParams, MessageItem, MessageDetail } from '@/api/profile'
import { fetchMessageDetail } from '@/api/profile'

// 定义组件名称（用于 keep-alive）
defineOptions({
  name: 'ProfileMessages',
})

const userStore = useUserStore()

// 筛选状态
const messageType = ref<'all' | 'announcement' | 'notification'>('all')
const isRead = ref<boolean | undefined>(undefined)

// 获取消息列表
async function fetchMessagesList(params: MessagesParams) {
  return fetchMessages({
    message_type: messageType.value,
    is_read: isRead.value,
    ...params,
  })
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
    await refresh()
  } catch (error) {
    // 用户取消或请求失败
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
  await fetchData()
  // 获取未读数（从响应中获取或单独请求）
  if (messages.value.length > 0) {
    // 已从列表响应中获取
  }
})
</script>

<template>
  <div class="messages-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">消息中心</h2>
        <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="title-badge" />
      </div>
      <el-button
        type="primary"
        plain
        :disabled="unreadCount === 0"
        @click="handleMarkAllRead"
      >
        全部标为已读
      </el-button>
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
      <div class="message-list" v-loading="isLoading">
        <div
          v-for="message in messages"
          :key="message.message_id"
          class="message-card"
          :class="{ unread: !message.is_read }"
        >
          <!-- 未读标记 -->
          <div class="unread-dot" v-show="!message.is_read" />

          <!-- 消息类型标签 -->
          <el-tag
            :type="typeMap[message.message_type]?.type || 'info'"
            size="small"
          >
            {{ typeMap[message.message_type]?.text || message.message_type }}
          </el-tag>

          <!-- 消息标题 -->
          <h4 class="message-title" :class="{ 'is-unread': !message.is_read }">
            {{ message.title }}
          </h4>

          <!-- 消息摘要 -->
          <p class="message-summary">{{ message.content }}</p>

          <!-- 时间 -->
          <span class="message-time">{{ formatTime(message.created_at) }}</span>

          <!-- 操作按钮 -->
          <div class="message-actions">
            <el-button type="primary" link @click="handleView(message)">
              查看
            </el-button>
            <el-button type="danger" link @click="handleDelete(message)">
              删除
            </el-button>
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

    <!-- 消息详情抽屉 -->
    <el-drawer
      v-model="detailDrawer"
      title="消息详情"
      direction="rtl"
      size="480px"
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
    </el-drawer>
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
    gap: 8px;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }

  .title-badge {
    :deep(.el-badge__content) {
      transform: translateY(-2px);
    }
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

.message-card {
  position: relative;
  display: grid;
  grid-template-columns: auto auto 1fr auto auto;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  transition: all 0.2s ease;

  &:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
  }

  &.unread {
    background: #f6ffed;
  }
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1890ff;
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

.message-summary {
  font-size: 14px;
  color: #666;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.message-time {
  font-size: 12px;
  color: #999;
}

.message-actions {
  display: flex;
  gap: 8px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

// 消息详情抽屉
.message-detail {
  padding: 0 16px;
}

.detail-header {
  display: flex;
  align-items: center;
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
  margin: 0 0 16px;
}

.detail-content {
  font-size: 15px;
  color: #666;
  line-height: 1.8;
  white-space: pre-wrap;
}

// 响应式
@media (max-width: 768px) {
  .message-card {
    grid-template-columns: 1fr;
    gap: 8px;

    .unread-dot {
      position: absolute;
      top: 16px;
      right: 16px;
    }
  }

  .message-summary {
    max-width: 100%;
  }

  .message-actions {
    justify-content: flex-end;
  }
}
</style>