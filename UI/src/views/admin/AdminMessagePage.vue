<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ChatDotRound, Delete, Message, Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import { useUserStore } from '@/store/user'
import {
  batchDeleteAdminFeedbacks,
  batchProcessFeedbacks,
  deleteAdminFeedback,
  fetchFeedbackDetail,
  fetchFeedbacks,
  fetchUsers,
  processFeedback,
  sendAdminMessage,
  type AdminFeedbackDetail,
  type AdminFeedbackItem,
  type AdminFeedbacksParams,
  type AdminMessageFormData,
  type AdminUserItem,
} from '@/api/admin'
import UserIdentity from '@/components/common/UserIdentity.vue'
import { formatUserIdentity } from '@/utils/format'

const userStore = useUserStore()

const typeFilter = ref<'all' | 'system' | 'course'>('system')
const statusFilter = ref<'all' | 'pending' | 'processed'>('all')
const keyword = ref('')
const platformPendingTotal = ref(0)
const courseFeedbackTotal = ref(0)

const canSendMessages = computed(() => userStore.hasPermission('admin.message'))
const showSendPanel = ref(false)

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
  isEmpty,
  fetchData,
  goToPage,
} = usePagination<AdminFeedbackItem, AdminFeedbacksParams>(fetchFeedbackList, 10)

const typeMap: Record<string, { text: string; type: 'primary' | 'success' }> = {
  system: { text: '平台反馈', type: 'primary' },
  course: { text: '课程反馈', type: 'success' },
}

const statusMap: Record<string, { text: string; type: 'warning' | 'success' }> = {
  pending: { text: '待处理', type: 'warning' },
  processed: { text: '已处理', type: 'success' },
}

const scopeText = computed(() => {
  if (typeFilter.value === 'system') return '默认展示平台/系统类用户反馈'
  if (typeFilter.value === 'course') return '当前筛选为课程反馈，用于兼容查看与升级处理'
  return '当前展示全部用户反馈'
})

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

function hasTargetIdentity(feedback: AdminFeedbackItem | AdminFeedbackDetail) {
  return Boolean(feedback.target_username || feedback.target_user_id)
}

async function loadSummaryStats() {
  try {
    const [pendingSystem, courseFeedbacks] = await Promise.all([
      fetchFeedbacks({ feedback_type: 'system', status: 'pending', page: 1, page_size: 1 }),
      fetchFeedbacks({ feedback_type: 'course', page: 1, page_size: 1 }),
    ])
    platformPendingTotal.value = pendingSystem.total
    courseFeedbackTotal.value = courseFeedbacks.total
  } catch {
    // 统计加载失败不影响主列表使用
  }
}

async function refreshFeedbacks(resetPage = false) {
  await fetchData(resetPage)
  await loadSummaryStats()
}

const showDetailDrawer = ref(false)
const currentFeedback = ref<AdminFeedbackDetail | null>(null)
const isLoadingDetail = ref(false)

async function loadFeedbackDetail(feedbackId: number) {
  const detail = await fetchFeedbackDetail(feedbackId)
  currentFeedback.value = detail
  return detail
}

async function handleViewDetail(feedback: AdminFeedbackItem) {
  isLoadingDetail.value = true
  showDetailDrawer.value = true
  currentFeedback.value = null

  try {
    await loadFeedbackDetail(feedback.feedback_id)
  } catch {
    ElMessage.error('加载反馈详情失败')
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

const showProcessDialog = ref(false)
const processTarget = ref<AdminFeedbackItem | AdminFeedbackDetail | null>(null)
const processFormRef = ref<FormInstance>()
const processForm = ref({ reply: '' })
const isSubmittingProcess = ref(false)

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

  isSubmittingProcess.value = true
  try {
    const detail = await processFeedback(processTarget.value.feedback_id, {
      reply: processForm.value.reply.trim(),
    })

    if (currentFeedback.value?.feedback_id === detail.feedback_id) {
      currentFeedback.value = detail
    }

    showProcessDialog.value = false
    ElMessage.success('回复并处理成功')
    await refreshFeedbacks()
  } catch {
    ElMessage.error('处理失败')
  } finally {
    isSubmittingProcess.value = false
  }
}

const selectedIds = ref<number[]>([])

const selectedCount = computed(() => selectedIds.value.length)

const pendingSelectedCount = computed(() => {
  return selectedIds.value.filter((id) => {
    const feedback = feedbacks.value.find((item) => item.feedback_id === id)
    return feedback?.status === 'pending'
  }).length
})

function handleSelectionChange(selection: AdminFeedbackItem[]) {
  selectedIds.value = selection.map((item) => item.feedback_id)
}

async function handleBatchProcess() {
  if (pendingSelectedCount.value === 0) {
    ElMessage.warning('请选择待处理反馈')
    return
  }

  const pendingIds = selectedIds.value.filter((id) => {
    const feedback = feedbacks.value.find((item) => item.feedback_id === id)
    return feedback?.status === 'pending'
  })

  try {
    await batchProcessFeedbacks(pendingIds)
    ElMessage.success('批量处理成功')
    selectedIds.value = []
    if (currentFeedback.value && pendingIds.includes(currentFeedback.value.feedback_id)) {
      await loadFeedbackDetail(currentFeedback.value.feedback_id)
    }
    await refreshFeedbacks()
  } catch {
    ElMessage.error('批量处理失败')
  }
}

async function refreshFeedbacksAfterDelete() {
  await refreshFeedbacks()
  if (feedbacks.value.length === 0 && page.value > 1) {
    await goToPage(page.value - 1)
  }
}

async function handleDeleteFeedback(feedback: AdminFeedbackItem | AdminFeedbackDetail) {
  try {
    await ElMessageBox.confirm('确定要删除这条用户反馈吗？删除后将从列表中隐藏。', '删除反馈', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteAdminFeedback(feedback.feedback_id)
    ElMessage.success('反馈已删除')
    selectedIds.value = selectedIds.value.filter((id) => id !== feedback.feedback_id)
    if (currentFeedback.value?.feedback_id === feedback.feedback_id) {
      showDetailDrawer.value = false
      currentFeedback.value = null
    }
    await refreshFeedbacksAfterDelete()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleBatchDeleteFeedbacks() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请选择要删除的反馈')
    return
  }

  const selectedFeedbacks = feedbacks.value.filter((feedback) => selectedIds.value.includes(feedback.feedback_id))

  try {
    await ElMessageBox.confirm(
      `确定要删除已选择的 ${selectedFeedbacks.length} 条用户反馈吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const selectedFeedbackIds = selectedFeedbacks.map((feedback) => feedback.feedback_id)
    const result = await batchDeleteAdminFeedbacks(selectedFeedbackIds)
    ElMessage.success(`已删除 ${result.count} 条用户反馈`)
    if (currentFeedback.value && selectedFeedbackIds.includes(currentFeedback.value.feedback_id)) {
      showDetailDrawer.value = false
      currentFeedback.value = null
    }
    selectedIds.value = []
    await refreshFeedbacksAfterDelete()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('批量删除失败')
    }
  }
}

function handleSearch() {
  void refreshFeedbacks(true)
}

function handleFilterChange() {
  void refreshFeedbacks(true)
}

function handleReset() {
  typeFilter.value = 'system'
  statusFilter.value = 'all'
  keyword.value = ''
  void refreshFeedbacks(true)
}

const messageFormRef = ref<FormInstance>()
const isSubmittingMessage = ref(false)
const recipientOptions = ref<AdminUserItem[]>([])
const isLoadingRecipients = ref(false)
const messageForm = ref<AdminMessageFormData>({
  user_id: null,
  type: 'system',
  title: '',
  content: '',
})

const messageRules: FormRules = {
  user_id: [{ required: true, type: 'number', message: '请选择接收用户', trigger: 'change' }],
  type: [{ required: true, message: '请选择消息类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入消息标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入消息内容', trigger: 'blur' }],
}

function formatRecipientOption(user: AdminUserItem) {
  return `${formatUserIdentity(user.username, user.user_id)}（${user.role}）`
}

async function searchRecipients(keyword = '') {
  const trimmedKeyword = keyword.trim()
  if (!trimmedKeyword) {
    recipientOptions.value = []
    return
  }

  isLoadingRecipients.value = true
  try {
    const response = await fetchUsers({
      keyword: trimmedKeyword,
      page: 1,
      page_size: 20,
    })
    recipientOptions.value = response.items
  } catch {
    ElMessage.error('加载用户列表失败')
  } finally {
    isLoadingRecipients.value = false
  }
}

function resetMessageForm() {
  messageForm.value = {
    user_id: null,
    type: 'system',
    title: '',
    content: '',
  }
  messageFormRef.value?.clearValidate()
}

async function handleSubmitMessage() {
  try {
    await messageFormRef.value?.validate()
  } catch {
    return
  }

  isSubmittingMessage.value = true
  try {
    if (!messageForm.value.user_id) return

    await sendAdminMessage({
      user_id: messageForm.value.user_id,
      type: messageForm.value.type,
      title: messageForm.value.title.trim(),
      content: messageForm.value.content.trim(),
    })
    ElMessage.success('站内消息发送成功')
    resetMessageForm()
    showSendPanel.value = false
  } catch {
    ElMessage.error('发送失败')
  } finally {
    isSubmittingMessage.value = false
  }
}

onMounted(() => {
  void refreshFeedbacks()
})
</script>

<template>
  <div class="admin-message-page">
    <div class="message-hero">
      <div class="hero-copy">
        <p class="eyebrow">Admin Message Center</p>
        <h2 class="page-title">消息中心</h2>
        <p class="page-desc">
          聚合学生和老师提交的平台类用户反馈，默认优先处理系统问题、账号权限、页面异常、使用体验和功能建议。
        </p>
      </div>
      <div class="stat-grid">
        <div class="stat-card stat-card--warning">
          <span class="stat-label">平台待处理</span>
          <strong>{{ platformPendingTotal }}</strong>
        </div>
        <div class="stat-card stat-card--primary">
          <span class="stat-label">课程反馈可查</span>
          <strong>{{ courseFeedbackTotal }}</strong>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="feedback-panel">
      <div class="panel-header">
        <div>
          <h3 class="panel-title">用户反馈处理台</h3>
          <p class="panel-desc">{{ scopeText }}</p>
        </div>
        <div v-if="canSendMessages" class="soft-action-surface header-actions">
          <el-button
            class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
            @click="showSendPanel = !showSendPanel"
          >
            {{ showSendPanel ? '收起发送' : '发送站内消息' }}
          </el-button>
        </div>
      </div>

      <div class="filter-bar">
        <div class="filter-left">
          <el-select v-model="typeFilter" placeholder="反馈类型" class="filter-select" @change="handleFilterChange">
            <el-option label="平台反馈" value="system" />
            <el-option label="课程反馈" value="course" />
            <el-option label="全部反馈" value="all" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="处理状态" class="filter-select" @change="handleFilterChange">
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
            class="search-input"
            @keyup.enter="handleSearch"
          >
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

      <div v-if="selectedCount > 0" class="batch-actions">
        <span>已选择 {{ selectedCount }} 条反馈，其中 {{ pendingSelectedCount }} 条待处理</span>
        <div class="batch-action-buttons">
          <el-button
            class="soft-action-btn soft-action-btn--primary soft-action-btn--small"
            type="primary"
            size="small"
            :disabled="pendingSelectedCount === 0"
            @click="handleBatchProcess"
          >
            批量标记已处理
          </el-button>
          <el-button
            class="soft-action-btn soft-action-btn--danger soft-action-btn--small"
            type="danger"
            size="small"
            :disabled="selectedCount === 0"
            @click="handleBatchDeleteFeedbacks"
          >
            批量删除
          </el-button>
        </div>
      </div>

      <el-empty v-if="isEmpty" description="暂无符合条件的反馈" />

      <el-table
        v-else
        :data="feedbacks"
        v-loading="isLoading"
        stripe
        border
        class="feedback-table"
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="提交用户" min-width="140">
          <template #default="{ row }">
            <div class="submitter-cell">
              <strong>
                <UserIdentity :username="row.username" :user-id="row.user_id" fallback="用户" compact />
              </strong>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="反馈类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="typeMap[row.feedback_type]?.type || 'info'" size="small">
              {{ typeMap[row.feedback_type]?.text || row.feedback_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联信息" min-width="180">
          <template #default="{ row }">
            <div class="relation-cell">
              <span v-if="row.course_title">课程：{{ row.course_title }}</span>
              <span v-if="hasTargetIdentity(row)" class="relation-identity">
                <span>反馈给：</span>
                <UserIdentity :username="row.target_username" :user-id="row.target_user_id" fallback="用户" compact />
              </span>
              <span v-if="!row.course_title && !hasTargetIdentity(row)" class="text-muted">平台问题</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="反馈内容" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.content }}
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
        <el-table-column label="操作" width="190" fixed="right" prop="__actions" align="center">
          <template #default="{ row }">
            <div class="row-action-surface" @click.stop>
              <el-button class="row-action-btn row-action-btn--secondary" text size="small" @click="handleViewDetail(row)">
                详情
              </el-button>
              <el-button
                v-if="row.status === 'pending'"
                class="row-action-btn row-action-btn--primary"
                text
                size="small"
                type="success"
                :icon="ChatDotRound"
                @click="openProcessDialog(row)"
              >
                处理
              </el-button>
              <el-button
                class="row-action-btn row-action-btn--danger"
                text
                size="small"
                type="danger"
                :icon="Delete"
                @click="handleDeleteFeedback(row)"
              >
                删除
              </el-button>
            </div>
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
    </el-card>

    <el-card v-if="canSendMessages && showSendPanel" shadow="never" class="send-panel">
      <div class="send-panel__header">
        <div>
          <h3 class="panel-title">发送站内消息</h3>
          <p class="panel-desc">保留原系统消息发送能力；此处仅用于主动通知用户，不作为管理员收件箱。</p>
        </div>
        <el-icon class="send-panel__icon"><Message /></el-icon>
      </div>

      <el-form ref="messageFormRef" :model="messageForm" :rules="messageRules" label-width="96px">
        <el-form-item label="接收用户" prop="user_id">
          <el-select
            v-model="messageForm.user_id"
            class="recipient-select"
            filterable
            remote
            clearable
            reserve-keyword
            placeholder="输入用户名或用户 ID 后搜索"
            no-data-text="请输入用户名或用户 ID 搜索用户"
            :remote-method="searchRecipients"
            :loading="isLoadingRecipients"
          >
            <el-option
              v-for="user in recipientOptions"
              :key="user.user_id"
              :label="formatRecipientOption(user)"
              :value="user.user_id"
            >
              <div class="recipient-option">
                <strong>
                  <UserIdentity :username="user.username" :user-id="user.user_id" fallback="用户" compact />
                </strong>
                <span>{{ user.role }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="消息类型" prop="type">
          <el-select v-model="messageForm.type" class="compact-control">
            <el-option label="系统消息" value="system" />
            <el-option label="通知" value="notification" />
            <el-option label="公告" value="announcement" />
            <el-option label="课程消息" value="course" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息标题" prop="title">
          <el-input v-model="messageForm.title" maxlength="200" show-word-limit placeholder="请输入消息标题" />
        </el-form-item>
        <el-form-item label="消息内容" prop="content">
          <el-input
            v-model="messageForm.content"
            type="textarea"
            :rows="5"
            maxlength="1000"
            show-word-limit
            placeholder="请输入消息内容"
          />
        </el-form-item>
        <el-form-item>
          <div class="soft-action-surface dialog-action-surface">
            <el-button class="soft-action-btn soft-action-btn--secondary" @click="resetMessageForm">重置</el-button>
            <el-button
              class="soft-action-btn soft-action-btn--primary"
              type="primary"
              :loading="isSubmittingMessage"
              @click="handleSubmitMessage"
            >
              发送消息
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-drawer v-model="showDetailDrawer" title="用户反馈详情" size="min(560px, 92vw)" class="feedback-detail-drawer">
      <div v-if="isLoadingDetail" class="loading-container">
        <el-skeleton :rows="7" animated />
      </div>
      <template v-else-if="currentFeedback">
        <div class="feedback-detail-shell">
          <section class="detail-hero">
            <div class="detail-hero__main">
              <span class="detail-eyebrow">用户反馈</span>
              <h3>{{ typeMap[currentFeedback.feedback_type]?.text || currentFeedback.feedback_type }}</h3>
              <p v-if="currentFeedback.course_title">关联课程：{{ currentFeedback.course_title }}</p>
            </div>
            <el-tag class="detail-status" :type="statusMap[currentFeedback.status]?.type || 'info'" effect="light">
              {{ statusMap[currentFeedback.status]?.text || currentFeedback.status }}
            </el-tag>
          </section>

          <section class="detail-meta-grid">
            <div class="detail-meta-item">
              <span class="detail-meta-label">提交人</span>
              <strong>
                <UserIdentity :username="currentFeedback.username" :user-id="currentFeedback.user_id" fallback="用户" />
              </strong>
              <small v-if="currentFeedback.user_email || currentFeedback.user_phone">
                {{ currentFeedback.user_email || currentFeedback.user_phone }}
              </small>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">反馈对象</span>
              <strong>
                <UserIdentity
                  v-if="hasTargetIdentity(currentFeedback)"
                  :username="currentFeedback.target_username"
                  :user-id="currentFeedback.target_user_id"
                  fallback="用户"
                />
                <template v-else>{{ currentFeedback.course_title || '平台/系统' }}</template>
              </strong>
              <small v-if="currentFeedback.course_title && hasTargetIdentity(currentFeedback)">
                关联课程：{{ currentFeedback.course_title }}
              </small>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">反馈编号</span>
              <strong>#{{ currentFeedback.feedback_id }}</strong>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">提交时间</span>
              <strong>{{ formatTime(currentFeedback.created_at) }}</strong>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">处理回复</span>
              <strong>{{ currentFeedback.reply ? '已回复' : '未回复' }}</strong>
              <small v-if="currentFeedback.replied_at || currentFeedback.processed_at">
                {{ formatTime(currentFeedback.replied_at || currentFeedback.processed_at) }}
              </small>
            </div>
          </section>

          <section class="feedback-thread" aria-label="反馈处理对话">
            <div class="thread-item thread-item--submitter">
              <div class="thread-avatar">提</div>
              <div class="thread-body">
                <div class="thread-meta">
                  <span class="thread-identity">
                    <UserIdentity :username="currentFeedback.username" :user-id="currentFeedback.user_id" fallback="用户" compact />
                    <span>提交反馈</span>
                  </span>
                  <time>{{ formatTime(currentFeedback.created_at) }}</time>
                </div>
                <div class="message-bubble message-bubble--submitter">
                  <p>{{ currentFeedback.content }}</p>
                  <div v-if="currentFeedback.images?.length" class="image-list message-images">
                    <el-image
                      v-for="(img, index) in currentFeedback.images"
                      :key="img"
                      :src="img"
                      :preview-src-list="currentFeedback.images"
                      :initial-index="Number(index)"
                      fit="cover"
                      class="feedback-image"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div class="thread-item thread-item--handler">
              <div class="thread-avatar">处</div>
              <div class="thread-body">
                <div class="thread-meta">
                  <span>处理回复</span>
                  <time v-if="currentFeedback.replied_at || currentFeedback.processed_at">
                    {{ formatTime(currentFeedback.replied_at || currentFeedback.processed_at) }}
                  </time>
                </div>
                <div
                  class="message-bubble message-bubble--handler"
                  :class="{ 'message-bubble--empty': !currentFeedback.reply }"
                >
                  <p>{{ currentFeedback.reply || '暂未填写处理回复，可点击下方“回复并处理”完成处理。' }}</p>
                </div>
              </div>
            </div>
          </section>

          <div v-if="currentFeedback.status === 'pending'" class="drawer-action-area">
            <div class="soft-action-surface">
              <el-button
                class="soft-action-btn soft-action-btn--primary"
                type="primary"
                :icon="ChatDotRound"
                @click="openProcessDialog(currentFeedback)"
              >
                回复并处理
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="showProcessDialog" title="回复并处理反馈" width="520px" @closed="resetProcessDialog">
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

        <el-form ref="processFormRef" :model="processForm" :rules="processRules" label-position="top">
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
        <div class="dialog-action-surface soft-action-surface">
          <el-button class="soft-action-btn soft-action-btn--secondary" @click="showProcessDialog = false">取消</el-button>
          <el-button
            class="soft-action-btn soft-action-btn--primary"
            type="primary"
            :loading="isSubmittingProcess"
            @click="handleSubmitProcess"
          >
            确认处理
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.admin-message-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

.message-hero {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 24px;
  min-width: 0;
  padding: 24px;
  border: 1px solid rgba(191, 219, 254, 0.9);
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(24, 144, 255, 0.16), transparent 36%),
    linear-gradient(135deg, #f8fbff 0%, #ffffff 100%);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.hero-copy {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-title {
  margin: 0;
  color: $text-primary;
  font-size: 24px;
  font-weight: 700;
}

.page-desc {
  max-width: 720px;
  margin: 10px 0 0;
  color: $text-secondary;
  line-height: 1.7;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(140px, 1fr));
  gap: 12px;
  min-width: 320px;
}

.stat-card {
  padding: 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);

  .stat-label {
    display: block;
    margin-bottom: 8px;
    color: $text-secondary;
    font-size: 13px;
  }

  strong {
    color: $text-primary;
    font-size: 22px;
  }
}

.stat-card--warning {
  border-color: rgba(251, 191, 36, 0.5);
}

.stat-card--primary {
  border-color: rgba(96, 165, 250, 0.55);
}

.feedback-panel,
.send-panel {
  min-width: 0;
  border-radius: 16px;

  :deep(.el-card__body) {
    min-width: 0;
  }
}

.panel-header,
.send-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.panel-title {
  margin: 0;
  color: $text-primary;
  font-size: 18px;
  font-weight: 700;
}

.panel-desc {
  margin: 8px 0 0;
  color: $text-secondary;
  font-size: $font-size-sm;
  line-height: 1.6;
}

.header-actions,
.filter-actions,
.dialog-action-surface {
  width: fit-content;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.filter-left,
.filter-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-select {
  width: 132px;
}

.search-input {
  width: 260px;
}

.batch-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px 16px;
  border: 1px solid #d6e8ff;
  border-radius: 12px;
  background: #f5f9ff;
  color: #1d4f91;
  font-size: $font-size-sm;
  font-weight: 600;
}

.batch-action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  :deep(.el-button) {
    margin-left: 0;
  }
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

.feedback-table {
  width: 100%;

  :deep(.el-table__row) {
    cursor: pointer;
  }

  :deep(.el-table__cell:first-child),
  :deep(.el-table__cell:last-child) {
    cursor: default;
  }
}

.submitter-cell,
.relation-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;

  strong {
    color: $text-primary;
  }

  span {
    color: $text-secondary;
    font-size: 13px;
  }
}

.relation-identity {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  min-width: 0;
}

.text-muted {
  color: $text-tertiary !important;
}

.row-action-surface {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 3px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #f4f8ff;
}

.row-action-btn {
  height: 26px;
  min-width: 42px;
  margin-left: 0 !important;
  padding: 0 9px !important;
  border-radius: 999px !important;
  font-size: 12px;
  font-weight: 600;
}

.row-action-btn--secondary {
  color: #2563eb !important;

  &:hover,
  &:focus {
    background: #fff !important;
    color: #1d4ed8 !important;
  }
}

.row-action-btn--primary {
  color: #16a34a !important;

  &:hover,
  &:focus {
    background: #ecfdf5 !important;
    color: #15803d !important;
  }
}

.row-action-btn--danger {
  color: #dc2626 !important;

  &:hover,
  &:focus {
    background: #fff5f5 !important;
    color: #b91c1c !important;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.send-panel__icon {
  padding: 10px;
  border-radius: 999px;
  background: #e8f3ff;
  color: #2563eb;
  font-size: 20px;
}

.compact-control {
  width: 220px;
}

.recipient-select {
  width: min(100%, 420px);
}

.recipient-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.4;

  strong {
    color: $text-primary;
    font-size: 14px;
  }

  span {
    color: $text-secondary;
    font-size: 12px;
  }
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feedback-image {
  width: 104px;
  height: 104px;
  border: 1px solid $border-color-light;
  border-radius: 12px;
  overflow: hidden;
}

.loading-container {
  padding: 24px;
}

:deep(.feedback-detail-drawer) {
  .el-drawer__body {
    padding: 0;
    background: linear-gradient(180deg, #f8fbff 0%, #ffffff 42%);
  }
}

.feedback-detail-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px;
}

.detail-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
  box-shadow: 0 12px 28px rgba(24, 144, 255, 0.08);

  &__main {
    min-width: 0;
  }

  h3 {
    margin: 6px 0;
    color: $text-primary;
    font-size: 20px;
    font-weight: 700;
    overflow-wrap: anywhere;
  }

  p {
    margin: 0;
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.detail-eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.detail-status {
  flex-shrink: 0;
}

.detail-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-meta-item {
  min-width: 0;
  padding: 14px;
  border: 1px solid $border-color-light;
  border-radius: 14px;
  background: $bg-white;

  strong,
  small {
    display: block;
    overflow-wrap: anywhere;
  }

  strong {
    margin-top: 6px;
    color: $text-primary;
    font-size: 15px;
    line-height: 1.45;
  }

  small {
    margin-top: 4px;
    color: $text-tertiary;
    line-height: 1.4;
  }
}

.detail-meta-label {
  color: $text-secondary;
  font-size: 12px;
  font-weight: 600;
}

.feedback-thread {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.thread-item {
  display: flex;
  gap: 12px;
  min-width: 0;
}

.thread-item--handler {
  flex-direction: row-reverse;

  .thread-meta {
    justify-content: flex-end;
    text-align: right;
  }
}

.thread-avatar {
  display: flex;
  flex: 0 0 36px;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e0f2fe;
  color: #2563eb;
  font-weight: 700;
}

.thread-item--handler .thread-avatar {
  background: #ecfdf5;
  color: $success-color;
}

.thread-body {
  min-width: 0;
  max-width: calc(100% - 48px);
  flex: 1;
}

.thread-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: $text-secondary;
  font-size: 12px;

  span,
  time {
    overflow-wrap: anywhere;
  }
}

.thread-identity {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.message-bubble {
  padding: 16px;
  border-radius: 16px;
  line-height: 1.7;
  color: $text-primary;
  overflow-wrap: anywhere;
  word-break: break-word;

  p {
    margin: 0;
    white-space: pre-wrap;
  }
}

.message-bubble--submitter {
  border: 1px solid #dbeafe;
  border-top-left-radius: 4px;
  background: $bg-white;
}

.message-bubble--handler {
  border-top-right-radius: 4px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.message-bubble--empty {
  color: $text-secondary;
  background: #f5f7fa;
  border: 1px dashed $border-color;
}

.message-images {
  margin-top: 14px;
}

.drawer-action-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 2px;
  padding-top: 18px;
  border-top: 1px solid $border-color-light;
}

.process-summary {
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid $border-color-light;
  border-radius: 12px;
  background: $bg-white;

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
    border-radius: 8px;
    background: $bg-color;
    line-height: 1.6;
  }
}

@media (max-width: 960px) {
  .message-hero {
    flex-direction: column;
  }

  .stat-grid {
    min-width: 0;
  }

  .filter-left,
  .filter-right {
    width: 100%;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .panel-header,
  .send-panel__header {
    flex-direction: column;
  }

  .message-hero {
    padding: 18px;
  }

  .stat-grid {
    grid-template-columns: 1fr;
    min-width: 0;
  }

  .filter-bar,
  .filter-left,
  .filter-right,
  .batch-actions {
    align-items: stretch;
    flex-direction: column;
    width: 100%;
  }

  .batch-action-buttons {
    flex-direction: column;
  }

  .feedback-detail-shell {
    gap: 14px;
    padding: 14px;
  }

  .detail-meta-grid {
    grid-template-columns: 1fr;
  }

  .detail-hero {
    flex-direction: column;
    padding: 16px;
  }

  .thread-item,
  .thread-item--handler {
    flex-direction: column;
  }

  .thread-item--handler .thread-meta {
    justify-content: flex-start;
    text-align: left;
  }

  .thread-body {
    max-width: 100%;
    width: 100%;
  }

  .message-bubble,
  .message-bubble--submitter,
  .message-bubble--handler {
    border-radius: 14px;
  }

  .image-list .feedback-image {
    width: 88px;
    height: 88px;
  }

  .filter-select,
  .search-input,
  .header-actions,
  .filter-actions,
  .dialog-action-surface,
  .compact-control,
  .recipient-select {
    width: 100% !important;
  }

  .drawer-action-area {
    justify-content: stretch;
  }
}
</style>
