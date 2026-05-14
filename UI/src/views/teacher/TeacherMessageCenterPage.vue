<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Bell, ChatDotRound, Delete, RefreshRight, Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import { useUserStore } from '@/store/user'
import {
  deleteMessage,
  fetchMessageDetail,
  fetchMessages,
  fetchUnreadCount,
  markAllRead,
  markAsRead,
  type MessageDetail,
  type MessageItem,
  type MessagesParams,
} from '@/api/profile'
import {
  batchDeleteTeacherFeedbacks,
  deleteTeacherFeedback,
  fetchTeacherFeedbackDetail,
  fetchTeacherFeedbacks,
  fetchTeacherUsers,
  grantUsernameChangeOpportunity,
  processTeacherFeedback,
  type TeacherFeedbackDetail,
  type TeacherFeedbackItem,
  type TeacherFeedbacksParams,
  type TeacherUserSearchItem,
} from '@/api/teacher'
import UserIdentity from '@/components/common/UserIdentity.vue'

const userStore = useUserStore()
const activeTab = ref<'feedbacks' | 'notices' | 'usernameGrant'>('feedbacks')

const feedbackStatus = ref<'all' | 'pending' | 'processed'>('all')
const feedbackKeyword = ref('')
const pendingFeedbackTotal = ref(0)

const noticeType = ref<'all' | 'announcement' | 'notification'>('all')
const noticeReadStatus = ref<'all' | 'unread' | 'read'>('all')
const unreadNoticeTotal = ref(0)

const userSearchKeyword = ref('')
const selectedGrantUser = ref<TeacherUserSearchItem | null>(null)
const isGrantingUsernameChange = ref(false)
const grantUserRoleMap: Record<TeacherUserSearchItem['role'], string> = {
  student: '学生',
  teacher: '老师',
  admin: '管理员',
}

const grantUserStatusMap: Record<TeacherUserSearchItem['status'], string> = {
  active: '正常',
  disabled: '已禁用',
  pending: '待审核',
}

async function fetchFeedbackList(params: TeacherFeedbacksParams) {
  return fetchTeacherFeedbacks({
    status: feedbackStatus.value,
    keyword: feedbackKeyword.value || undefined,
    ...params,
  })
}

async function fetchNoticeList(params: MessagesParams) {
  return fetchMessages({
    message_type: noticeType.value,
    is_read: noticeReadStatus.value === 'all' ? undefined : noticeReadStatus.value === 'read',
    ...params,
  })
}

const {
  items: feedbacks,
  total: feedbackTotal,
  page: feedbackPage,
  pageSize: feedbackPageSize,
  totalPages: feedbackTotalPages,
  isLoading: isLoadingFeedbacks,
  isEmpty: isFeedbackEmpty,
  fetchData: fetchFeedbackData,
  goToPage: goToFeedbackPage,
} = usePagination<TeacherFeedbackItem, TeacherFeedbacksParams>(fetchFeedbackList, 8)

const {
  items: notices,
  total: noticeTotal,
  page: noticePage,
  pageSize: noticePageSize,
  totalPages: noticeTotalPages,
  isLoading: isLoadingNotices,
  isEmpty: isNoticeEmpty,
  fetchData: fetchNoticeData,
  goToPage: goToNoticePage,
} = usePagination<MessageItem, MessagesParams>(fetchNoticeList, 8)

async function fetchGrantUserList(params: { page?: number; page_size?: number }) {
  return fetchTeacherUsers({
    keyword: userSearchKeyword.value.trim() || undefined,
    role: 'student',
    page: params.page,
    page_size: params.page_size,
  })
}

const {
  items: grantUsers,
  total: grantUserTotal,
  page: grantUserPage,
  pageSize: grantUserPageSize,
  totalPages: grantUserTotalPages,
  isLoading: isLoadingGrantUsers,
  isEmpty: isGrantUserEmpty,
  fetchData: fetchGrantUserData,
  goToPage: goToGrantUserPage,
} = usePagination<TeacherUserSearchItem, { page?: number; page_size?: number }>(fetchGrantUserList, 8)

const feedbackStatusMap: Record<TeacherFeedbackItem['status'], { text: string; type: 'warning' | 'success' }> = {
  pending: { text: '待处理', type: 'warning' },
  processed: { text: '已处理', type: 'success' },
}

const noticeTypeMap: Record<MessageItem['message_type'], { text: string; type: 'primary' | 'info' }> = {
  announcement: { text: '公告', type: 'primary' },
  notification: { text: '通知', type: 'info' },
}

const showFeedbackDrawer = ref(false)
const currentFeedback = ref<TeacherFeedbackDetail | null>(null)
const isLoadingFeedbackDetail = ref(false)
const feedbackBatchMode = ref(false)
const selectedFeedbackIds = ref<number[]>([])

const showProcessDialog = ref(false)
const processTarget = ref<TeacherFeedbackItem | TeacherFeedbackDetail | null>(null)
const processFormRef = ref<FormInstance>()
const processForm = ref({ reply: '' })
const isSubmittingProcess = ref(false)

const showNoticeDrawer = ref(false)
const currentNotice = ref<MessageDetail | null>(null)
const isLoadingNoticeDetail = ref(false)
const isMarkingAllRead = ref(false)
const noticeBatchMode = ref(false)
const selectedNoticeIds = ref<number[]>([])

const processRules: FormRules = {
  reply: [
    { required: true, message: '请输入回复内容', trigger: 'blur' },
    { min: 2, max: 1000, message: '回复内容长度需在 2-1000 个字符之间', trigger: 'blur' },
  ],
}

const feedbackStatsText = computed(() => `${pendingFeedbackTotal.value} 条待处理`)
const noticeStatsText = computed(() => `${unreadNoticeTotal.value} 条未读`)
const selectedNoticeCount = computed(() => selectedNoticeIds.value.length)
const selectedFeedbackCount = computed(() => selectedFeedbackIds.value.length)
const allFeedbacksSelectedOnPage = computed(() => {
  return feedbacks.value.length > 0
    && feedbacks.value.every((feedback) => selectedFeedbackIds.value.includes(feedback.feedback_id))
})
const allNoticesSelectedOnPage = computed(() => {
  return notices.value.length > 0
    && notices.value.every((notice) => selectedNoticeIds.value.includes(notice.message_id))
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

function syncHeaderUnreadCount() {
  userStore.setUnreadCount(unreadNoticeTotal.value + pendingFeedbackTotal.value)
}

async function syncUnreadCount() {
  const data = await fetchUnreadCount()
  unreadNoticeTotal.value = data.unread_count
  syncHeaderUnreadCount()
}

async function loadStats() {
  try {
    const [pendingData, unreadData] = await Promise.all([
      fetchTeacherFeedbacks({ status: 'pending', page: 1, page_size: 1 }),
      fetchUnreadCount(),
    ])
    pendingFeedbackTotal.value = pendingData.total
    unreadNoticeTotal.value = unreadData.unread_count
    syncHeaderUnreadCount()
  } catch {
    ElMessage.warning('统计数据加载不完整')
  }
}

async function refreshFeedbacks(resetPage = false) {
  await fetchFeedbackData(resetPage)
  await loadStats()
}

async function refreshFeedbacksAfterMutation() {
  await refreshFeedbacks()
  if (feedbacks.value.length === 0 && feedbackPage.value > 1) {
    await goToFeedbackPage(feedbackPage.value - 1)
  }
}

async function refreshNotices(resetPage = false) {
  await fetchNoticeData(resetPage)
  await syncUnreadCount()
}

async function refreshNoticesAfterMutation() {
  const validPage = Math.max(1, Math.min(noticePage.value, noticeTotalPages.value))

  if (validPage !== noticePage.value) {
    noticePage.value = validPage
    await refreshNotices()
    return
  }

  if (notices.value.length === 0 && noticePage.value > 1) {
    await goToNoticePage(Math.max(1, noticePage.value - 1))
    return
  }

  await refreshNotices()
}

function removeDeletedNotices(deletedIds: number[]) {
  const deletedIdSet = new Set(deletedIds)
  const originalCount = notices.value.length

  notices.value = notices.value.filter((notice) => !deletedIdSet.has(notice.message_id))
  const removedCount = originalCount - notices.value.length

  if (removedCount > 0) {
    noticeTotal.value = Math.max(0, noticeTotal.value - removedCount)
  }

  selectedNoticeIds.value = selectedNoticeIds.value.filter((id) => !deletedIdSet.has(id))
}

function handleFeedbackSearch() {
  void refreshFeedbacks(true)
}

function handleFeedbackReset() {
  feedbackStatus.value = 'all'
  feedbackKeyword.value = ''
  exitFeedbackBatchMode()
  void refreshFeedbacks(true)
}

function handleFeedbackFilterChange() {
  exitFeedbackBatchMode()
  void refreshFeedbacks(true)
}

function handleNoticeFilterChange() {
  exitNoticeBatchMode()
  void refreshNotices(true)
}

function handleGrantUserSearch() {
  selectedGrantUser.value = null
  void fetchGrantUserData(true)
}

function handleGrantUserReset() {
  userSearchKeyword.value = ''
  selectedGrantUser.value = null
  void fetchGrantUserData(true)
}

function selectGrantUser(user: TeacherUserSearchItem) {
  selectedGrantUser.value = user
}

async function handleGrantUsernameChange() {
  if (!selectedGrantUser.value) {
    ElMessage.warning('请先选择要开放改名机会的用户')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定为用户 ${selectedGrantUser.value.username} 增加一次用户名修改机会吗？`,
      '开放改名机会',
      {
        confirmButtonText: '确认开放',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('确认操作失败')
    }
    return
  }

  isGrantingUsernameChange.value = true
  try {
    const updatedUser = await grantUsernameChangeOpportunity(selectedGrantUser.value.user_id)
    ElMessage.success('已开放一次改名机会')
    selectedGrantUser.value = updatedUser
    grantUsers.value = grantUsers.value.map((user) => (
      user.user_id === updatedUser.user_id ? updatedUser : user
    ))
  } catch {
    ElMessage.error('开放改名机会失败')
  } finally {
    isGrantingUsernameChange.value = false
  }
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

function enterFeedbackBatchMode() {
  feedbackBatchMode.value = true
  selectedFeedbackIds.value = []
}

function exitFeedbackBatchMode() {
  feedbackBatchMode.value = false
  selectedFeedbackIds.value = []
}

function handleToggleSelectAllFeedbacks() {
  if (allFeedbacksSelectedOnPage.value) {
    selectedFeedbackIds.value = []
    return
  }
  selectedFeedbackIds.value = feedbacks.value.map((feedback) => feedback.feedback_id)
}

function handleFeedbackCardClick(feedback: TeacherFeedbackItem) {
  if (feedbackBatchMode.value) {
    toggleFeedbackSelection(feedback.feedback_id)
    return
  }
  void handleViewFeedback(feedback)
}

function isNoticeSelected(messageId: number) {
  return selectedNoticeIds.value.includes(messageId)
}

function toggleNoticeSelection(messageId: number) {
  if (isNoticeSelected(messageId)) {
    selectedNoticeIds.value = selectedNoticeIds.value.filter((id) => id !== messageId)
    return
  }
  selectedNoticeIds.value = [...selectedNoticeIds.value, messageId]
}

function enterNoticeBatchMode() {
  noticeBatchMode.value = true
  selectedNoticeIds.value = []
}

function exitNoticeBatchMode() {
  noticeBatchMode.value = false
  selectedNoticeIds.value = []
}

function handleToggleSelectAllNotices() {
  if (allNoticesSelectedOnPage.value) {
    selectedNoticeIds.value = []
    return
  }
  selectedNoticeIds.value = notices.value.map((notice) => notice.message_id)
}

function handleNoticeCardClick(notice: MessageItem) {
  if (noticeBatchMode.value) {
    toggleNoticeSelection(notice.message_id)
    return
  }
  void handleViewNotice(notice)
}

async function handleViewFeedback(feedback: TeacherFeedbackItem) {
  showFeedbackDrawer.value = true
  isLoadingFeedbackDetail.value = true
  currentFeedback.value = null
  try {
    currentFeedback.value = await fetchTeacherFeedbackDetail(feedback.feedback_id)
  } catch {
    ElMessage.error('加载反馈详情失败')
    showFeedbackDrawer.value = false
  } finally {
    isLoadingFeedbackDetail.value = false
  }
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

  isSubmittingProcess.value = true
  try {
    const detail = await processTeacherFeedback(processTarget.value.feedback_id, {
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

async function handleDeleteFeedback(feedback: TeacherFeedbackItem | TeacherFeedbackDetail) {
  try {
    await ElMessageBox.confirm('确定要删除这条学生反馈吗？删除后将从列表中隐藏。', '删除反馈', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteTeacherFeedback(feedback.feedback_id)
    ElMessage.success('反馈已删除')
    selectedFeedbackIds.value = selectedFeedbackIds.value.filter((id) => id !== feedback.feedback_id)
    if (currentFeedback.value?.feedback_id === feedback.feedback_id) {
      showFeedbackDrawer.value = false
      currentFeedback.value = null
    }
    await refreshFeedbacksAfterMutation()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleBatchDeleteFeedbacks() {
  if (selectedFeedbackCount.value === 0) {
    ElMessage.warning('请先选择要删除的学生反馈')
    return
  }

  const selectedFeedbacks = feedbacks.value.filter((feedback) => isFeedbackSelected(feedback.feedback_id))

  try {
    await ElMessageBox.confirm(
      `确定要删除已选择的 ${selectedFeedbacks.length} 条学生反馈吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const result = await batchDeleteTeacherFeedbacks(selectedFeedbacks.map((feedback) => feedback.feedback_id))
    ElMessage.success(`已删除 ${result.count} 条学生反馈`)
    if (currentFeedback.value && selectedFeedbackIds.value.includes(currentFeedback.value.feedback_id)) {
      showFeedbackDrawer.value = false
      currentFeedback.value = null
    }
    selectedFeedbackIds.value = []
    await refreshFeedbacksAfterMutation()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('批量删除失败')
    }
  }
}

async function handleViewNotice(notice: MessageItem) {
  if (noticeBatchMode.value) return

  showNoticeDrawer.value = true
  isLoadingNoticeDetail.value = true
  currentNotice.value = null
  try {
    const detail = await fetchMessageDetail(notice.message_id)
    currentNotice.value = detail
    if (!notice.is_read) {
      await markAsRead(notice.message_id)
      await refreshNotices()
    }
  } catch {
    ElMessage.error('加载通知详情失败')
    showNoticeDrawer.value = false
  } finally {
    isLoadingNoticeDetail.value = false
  }
}

async function handleMarkAllRead() {
  if (unreadNoticeTotal.value === 0) return

  isMarkingAllRead.value = true
  try {
    await markAllRead()
    ElMessage.success('已全部标为已读')
    await refreshNotices()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    isMarkingAllRead.value = false
  }
}

async function handleDeleteNotice(notice: MessageItem) {
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '删除消息', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMessage(notice.message_id)
    ElMessage.success('消息已删除')
    if (currentNotice.value?.message_id === notice.message_id) {
      showNoticeDrawer.value = false
      currentNotice.value = null
    }
    removeDeletedNotices([notice.message_id])
    await refreshNoticesAfterMutation()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleBatchDeleteNotices() {
  if (selectedNoticeCount.value === 0) {
    ElMessage.warning('请先选择要删除的平台通知')
    return
  }

  const selectedNotices = notices.value.filter((notice) => isNoticeSelected(notice.message_id))

  try {
    await ElMessageBox.confirm(
      `确定要删除已选择的 ${selectedNotices.length} 条平台通知吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const results = await Promise.allSettled(
      selectedNotices.map((notice) => deleteMessage(notice.message_id))
    )
    const successIds = selectedNotices
      .filter((_, index) => results[index].status === 'fulfilled')
      .map((notice) => notice.message_id)
    const failureCount = results.length - successIds.length

    if (successIds.length > 0) {
      if (currentNotice.value && successIds.includes(currentNotice.value.message_id)) {
        showNoticeDrawer.value = false
        currentNotice.value = null
      }
      removeDeletedNotices(successIds)
      await refreshNoticesAfterMutation()
    }

    if (failureCount > 0) {
      if (successIds.length > 0) {
        ElMessage.warning(`已删除 ${successIds.length} 条，${failureCount} 条删除失败`)
      } else {
        ElMessage.error('批量删除失败，请稍后重试')
      }
      return
    }

    ElMessage.success(`已删除 ${successIds.length} 条平台通知`)
    selectedNoticeIds.value = []
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('批量删除失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([
    fetchFeedbackData(),
    fetchNoticeData(),
    loadStats(),
  ])
})

watch(notices, (currentNotices) => {
  const currentIds = new Set(currentNotices.map((notice) => notice.message_id))
  selectedNoticeIds.value = selectedNoticeIds.value.filter((id) => currentIds.has(id))
})
</script>

<template>
  <div class="teacher-message-page">
    <div class="message-hero">
      <div>
        <p class="eyebrow">Teacher Message Center</p>
        <h2 class="page-title">消息中心</h2>
        <p class="page-desc">集中处理学生发送过来的反馈，以及管理员发布的平台公告和通知。</p>
      </div>
      <div class="stat-grid">
        <div class="stat-card stat-card--warning">
          <span class="stat-label">学生反馈</span>
          <strong>{{ feedbackStatsText }}</strong>
        </div>
        <div class="stat-card stat-card--primary">
          <span class="stat-label">平台通知</span>
          <strong>{{ noticeStatsText }}</strong>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="message-tabs">
      <el-tab-pane name="feedbacks">
        <template #label>
          <span class="tab-label">
            <el-icon><ChatDotRound /></el-icon>
            学生反馈
          </span>
        </template>

        <div class="panel-card">
          <div class="filter-bar">
            <el-select v-model="feedbackStatus" placeholder="状态" class="filter-select" @change="handleFeedbackFilterChange">
              <el-option label="全部状态" value="all" />
              <el-option label="待处理" value="pending" />
              <el-option label="已处理" value="processed" />
            </el-select>
            <div class="filter-right">
              <el-input
                v-model="feedbackKeyword"
                placeholder="搜索反馈内容/课程名/学生"
                clearable
                class="search-input"
                @keyup.enter="handleFeedbackSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <div class="soft-action-surface filter-actions">
                <template v-if="feedbackBatchMode">
                  <el-button
                    class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
                    @click="handleToggleSelectAllFeedbacks"
                  >
                    {{ allFeedbacksSelectedOnPage ? '取消全选' : '全选当前页' }}
                  </el-button>
                  <el-button
                    class="soft-action-btn soft-action-btn--danger soft-action-btn--small"
                    type="danger"
                    :disabled="selectedFeedbackCount === 0"
                    @click="handleBatchDeleteFeedbacks"
                  >
                    批量删除
                  </el-button>
                  <el-button
                    class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
                    @click="exitFeedbackBatchMode"
                  >
                    取消管理
                  </el-button>
                </template>
                <template v-else>
                  <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleFeedbackSearch">搜索</el-button>
                  <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleFeedbackReset">重置</el-button>
                  <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="enterFeedbackBatchMode">批量管理</el-button>
                </template>
              </div>
            </div>
          </div>

          <div v-if="feedbackBatchMode && !isFeedbackEmpty" class="batch-toolbar">
            <span class="batch-toolbar__text">已选择 {{ selectedFeedbackCount }} 条学生反馈</span>
            <span class="batch-toolbar__hint">选择反馈后可批量删除，点击卡片可直接勾选</span>
          </div>

          <div v-loading="isLoadingFeedbacks" class="feedback-list">
            <el-empty v-if="isFeedbackEmpty" description="暂无学生反馈" />
            <div
              v-for="feedback in feedbacks"
              v-else
              :key="feedback.feedback_id"
              class="feedback-card"
              :class="{ 'is-pending': feedback.status === 'pending', 'is-batch-mode': feedbackBatchMode, 'is-selected': isFeedbackSelected(feedback.feedback_id) }"
              @click="handleFeedbackCardClick(feedback)"
            >
              <div v-if="feedbackBatchMode" class="notice-select" @click.stop>
                <el-checkbox
                  :model-value="isFeedbackSelected(feedback.feedback_id)"
                  @change="toggleFeedbackSelection(feedback.feedback_id)"
                />
              </div>
              <div class="card-main">
                <div class="card-topline">
                  <div class="student-info">
                    <UserIdentity
                      class="student-name"
                      :username="feedback.username"
                      :user-id="feedback.user_id"
                      fallback="用户"
                      compact
                    />
                    <span class="course-title">{{ feedback.course_title || '未关联课程' }}</span>
                  </div>
                  <el-tag :type="feedbackStatusMap[feedback.status].type" size="small">
                    {{ feedbackStatusMap[feedback.status].text }}
                  </el-tag>
                </div>
                <p class="feedback-content text-ellipsis-2">{{ feedback.content }}</p>
                <div class="card-meta">
                  <span class="meta-identity">
                    <span>反馈给：</span>
                    <UserIdentity
                      :username="feedback.target_username"
                      :user-id="feedback.target_user_id"
                      fallback="当前讲师"
                      compact
                    />
                  </span>
                  <span>{{ formatTime(feedback.created_at) }}</span>
                  <span v-if="feedback.images.length">{{ feedback.images.length }} 张截图</span>
                </div>
              </div>
              <div v-if="!feedbackBatchMode" class="card-actions" @click.stop>
                <el-button text type="primary" @click="handleViewFeedback(feedback)">查看详情</el-button>
                <el-button
                  v-if="feedback.status === 'pending'"
                  text
                  type="success"
                  :icon="ChatDotRound"
                  @click="openProcessDialog(feedback)"
                >
                  回复处理
                </el-button>
                <el-button text type="danger" :icon="Delete" @click="handleDeleteFeedback(feedback)">删除</el-button>
              </div>
            </div>
          </div>

          <el-pagination
            v-if="feedbackTotalPages > 1"
            :current-page="feedbackPage"
            :page-size="feedbackPageSize"
            :total="feedbackTotal"
            layout="total, prev, pager, next, jumper"
            class="pagination"
            @current-change="goToFeedbackPage"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane name="notices">
        <template #label>
          <span class="tab-label">
            <el-icon><Bell /></el-icon>
            平台通知
          </span>
        </template>

        <div class="panel-card">
          <div class="filter-bar">
            <div class="filter-left">
              <el-select v-model="noticeType" placeholder="类型" class="filter-select" @change="handleNoticeFilterChange">
                <el-option label="全部类型" value="all" />
                <el-option label="公告" value="announcement" />
                <el-option label="通知" value="notification" />
              </el-select>
              <el-select v-model="noticeReadStatus" placeholder="阅读状态" class="filter-select" @change="handleNoticeFilterChange">
                <el-option label="全部状态" value="all" />
                <el-option label="未读" value="unread" />
                <el-option label="已读" value="read" />
              </el-select>
            </div>
            <div class="soft-action-surface filter-actions">
              <template v-if="noticeBatchMode">
                <el-button
                  class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
                  @click="handleToggleSelectAllNotices"
                >
                  {{ allNoticesSelectedOnPage ? '取消全选' : '全选当前页' }}
                </el-button>
                <el-button
                  class="soft-action-btn soft-action-btn--danger soft-action-btn--small"
                  type="danger"
                  :disabled="selectedNoticeCount === 0"
                  @click="handleBatchDeleteNotices"
                >
                  批量删除
                </el-button>
                <el-button
                  class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
                  @click="exitNoticeBatchMode"
                >
                  取消管理
                </el-button>
              </template>
              <template v-else>
                <el-button
                  class="soft-action-btn soft-action-btn--primary soft-action-btn--small"
                  :loading="isMarkingAllRead"
                  :disabled="unreadNoticeTotal === 0"
                  @click="handleMarkAllRead"
                >
                  全部已读
                </el-button>
                <el-button
                  class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
                  @click="enterNoticeBatchMode"
                >
                  批量管理
                </el-button>
              </template>
            </div>
          </div>

          <div v-if="noticeBatchMode && !isNoticeEmpty" class="batch-toolbar">
            <span class="batch-toolbar__text">已选择 {{ selectedNoticeCount }} 条平台通知</span>
            <span class="batch-toolbar__hint">选择通知后可批量删除，点击卡片可直接勾选</span>
          </div>

          <div v-loading="isLoadingNotices" class="notice-list">
            <el-empty v-if="isNoticeEmpty" description="暂无平台通知" />
            <div
              v-for="notice in notices"
              v-else
              :key="notice.message_id"
              class="notice-card"
              :class="{ 'is-unread': !notice.is_read, 'is-batch-mode': noticeBatchMode, 'is-selected': isNoticeSelected(notice.message_id) }"
              @click="handleNoticeCardClick(notice)"
            >
              <div v-if="noticeBatchMode" class="notice-select" @click.stop>
                <el-checkbox
                  :model-value="isNoticeSelected(notice.message_id)"
                  @change="toggleNoticeSelection(notice.message_id)"
                />
              </div>
              <div class="notice-status-dot" />
              <div class="card-main">
                <div class="card-topline">
                  <div class="notice-title-wrap">
                    <span class="notice-title">{{ notice.title }}</span>
                    <el-tag :type="noticeTypeMap[notice.message_type].type" size="small">
                      {{ noticeTypeMap[notice.message_type].text }}
                    </el-tag>
                  </div>
                  <span class="notice-time">{{ formatTime(notice.created_at) }}</span>
                </div>
                <p class="notice-content text-ellipsis-2">{{ notice.content }}</p>
              </div>
              <div v-if="!noticeBatchMode" class="card-actions" @click.stop>
                <el-button text type="primary" @click="handleViewNotice(notice)">查看</el-button>
                <el-button text type="danger" :icon="Delete" @click="handleDeleteNotice(notice)">删除</el-button>
              </div>
            </div>
          </div>

          <el-pagination
            v-if="noticeTotalPages > 1"
            :current-page="noticePage"
            :page-size="noticePageSize"
            :total="noticeTotal"
            layout="total, prev, pager, next, jumper"
            class="pagination"
            @current-change="goToNoticePage"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane name="usernameGrant">
        <template #label>
          <span class="tab-label">
            <el-icon><RefreshRight /></el-icon>
            改名机会
          </span>
        </template>

        <div class="panel-card username-grant-panel">
          <div class="grant-intro">
            <h3>开放一次用户名修改机会</h3>
            <p>学生首次自助改名后，如确需再次修改，可由老师在这里为指定学生增加一次机会。</p>
          </div>

          <div class="filter-bar">
            <el-input
              v-model="userSearchKeyword"
              placeholder="搜索用户名或用户 ID"
              clearable
              class="search-input"
              @keyup.enter="handleGrantUserSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <div class="soft-action-surface filter-actions">
              <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleGrantUserSearch">搜索</el-button>
              <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleGrantUserReset">重置</el-button>
            </div>
          </div>

          <div v-loading="isLoadingGrantUsers" class="grant-user-list">
            <el-empty v-if="isGrantUserEmpty" description="请输入用户名或用户 ID 搜索用户" />
            <div
              v-for="user in grantUsers"
              v-else
              :key="user.user_id"
              class="grant-user-card"
              :class="{ 'is-selected': selectedGrantUser?.user_id === user.user_id }"
              @click="selectGrantUser(user)"
            >
              <div class="card-main">
                <div class="card-topline">
                  <UserIdentity class="student-name" :username="user.username" :user-id="user.user_id" fallback="用户" />
                  <el-tag size="small">{{ grantUserRoleMap[user.role] }}</el-tag>
                </div>
                <div class="card-meta">
                  <span>状态：{{ grantUserStatusMap[user.status] || user.status }}</span>
                  <span>剩余改名机会：{{ user.username_change_remaining }}</span>
                  <span v-if="user.original_username">原用户名：{{ user.original_username }}</span>
                </div>
              </div>
              <el-tag :type="user.can_change_username ? 'success' : 'info'" size="small">
                {{ user.can_change_username ? '可修改' : '无机会' }}
              </el-tag>
            </div>
          </div>

          <el-pagination
            v-if="grantUserTotalPages > 1"
            :current-page="grantUserPage"
            :page-size="grantUserPageSize"
            :total="grantUserTotal"
            layout="total, prev, pager, next, jumper"
            class="pagination"
            @current-change="goToGrantUserPage"
          />

          <div class="drawer-action-area grant-action-area">
            <div class="soft-action-surface">
                          <el-button
                class="soft-action-btn soft-action-btn--primary grant-action-btn"
                type="primary"
                :loading="isGrantingUsernameChange"
                :disabled="!selectedGrantUser"
                @click="handleGrantUsernameChange"
              >
                为选中用户开放一次机会
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-drawer v-model="showFeedbackDrawer" title="学生反馈详情" size="min(520px, 92vw)" class="message-drawer">
      <div v-if="isLoadingFeedbackDetail" class="loading-container">
        <el-skeleton :rows="7" animated />
      </div>
      <template v-else-if="currentFeedback">
        <div class="detail-section">
          <div class="detail-row">
            <span class="detail-label">学生</span>
            <span class="detail-value">
              <UserIdentity :username="currentFeedback.username" :user-id="currentFeedback.user_id" fallback="用户" />
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">关联课程</span>
            <span class="detail-value">{{ currentFeedback.course_title || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">反馈给</span>
            <span class="detail-value">
              <UserIdentity
                :username="currentFeedback.target_username"
                :user-id="currentFeedback.target_user_id"
                fallback="当前讲师"
              />
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态</span>
            <el-tag :type="feedbackStatusMap[currentFeedback.status].type">
              {{ feedbackStatusMap[currentFeedback.status].text }}
            </el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">提交时间</span>
            <span class="detail-value">{{ formatTime(currentFeedback.created_at) }}</span>
          </div>
        </div>

        <el-divider>反馈对话</el-divider>
        <div class="feedback-chat">
          <div class="chat-message chat-message--student">
            <div class="chat-meta">
              <UserIdentity :username="currentFeedback.username" :user-id="currentFeedback.user_id" fallback="用户" compact />
              <span>{{ formatTime(currentFeedback.created_at) }}</span>
            </div>
            <div class="chat-bubble chat-bubble--student">
              <div class="chat-text">{{ currentFeedback.content }}</div>
              <div v-if="currentFeedback.images.length" class="chat-images">
                <el-image
                  v-for="(img, index) in currentFeedback.images"
                  :key="img"
                  :src="img"
                  :preview-src-list="currentFeedback.images"
                  :initial-index="index"
                  fit="cover"
                  class="feedback-image"
                />
              </div>
            </div>
          </div>

          <div v-if="currentFeedback.reply" class="chat-message chat-message--teacher">
            <div class="chat-meta">
              <UserIdentity
                :username="userStore.userInfo.username"
                :user-id="userStore.userInfo.userId"
                fallback="当前老师"
                compact
              />
              <span>{{ formatTime(currentFeedback.replied_at || currentFeedback.processed_at) }}</span>
            </div>
            <div class="chat-bubble chat-bubble--teacher">
              <div class="chat-text">{{ currentFeedback.reply }}</div>
            </div>
          </div>
        </div>

        <div class="drawer-action-area">
          <div class="soft-action-surface">
            <el-button
              v-if="currentFeedback.status === 'pending'"
              class="soft-action-btn soft-action-btn--primary"
              type="primary"
              :icon="ChatDotRound"
              @click="openProcessDialog(currentFeedback)"
            >
              回复并处理
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-drawer v-model="showNoticeDrawer" title="平台通知详情" size="min(520px, 92vw)" class="message-drawer">
      <div v-if="isLoadingNoticeDetail" class="loading-container">
        <el-skeleton :rows="6" animated />
      </div>
      <template v-else-if="currentNotice">
        <div class="notice-detail-head">
          <el-tag :type="noticeTypeMap[currentNotice.message_type].type">
            {{ noticeTypeMap[currentNotice.message_type].text }}
          </el-tag>
          <span>{{ formatTime(currentNotice.created_at) }}</span>
        </div>
        <h3 class="notice-detail-title">{{ currentNotice.title }}</h3>
        <div class="rich-content notice-detail-content">{{ currentNotice.content }}</div>
        <div class="drawer-action-area">
          <div class="soft-action-surface">
            <el-button
              class="soft-action-btn soft-action-btn--danger"
              type="danger"
              :icon="Delete"
              @click="handleDeleteNotice(currentNotice)"
            >
              删除通知
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="showProcessDialog" title="回复并处理反馈" width="520px" @closed="resetProcessDialog">
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
.teacher-message-page {
  .message-hero {
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 24px;
    padding: 24px;
    border: 1px solid rgba(191, 219, 254, 0.9);
    border-radius: 20px;
    background:
      radial-gradient(circle at top right, rgba(24, 144, 255, 0.16), transparent 36%),
      linear-gradient(135deg, #f8fbff 0%, #ffffff 100%);
    box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
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
    margin: 10px 0 0;
    color: $text-secondary;
    line-height: 1.6;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(140px, 1fr));
    gap: 12px;
    min-width: 320px;
  }

  .stat-card {
    padding: 18px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(226, 232, 240, 0.9);

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
}

.message-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 16px;
  }

  :deep(.el-tabs__item) {
    height: 42px;
    font-weight: 600;
  }
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.panel-card {
  padding: 20px;
  border: 1px solid $border-color-light;
  border-radius: 16px;
  background: $bg-white;
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
  width: 280px;
}

.filter-actions,
.dialog-action-surface {
  width: fit-content;
}

.filter-actions {
  flex-wrap: wrap;
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

.grant-intro {
  margin-bottom: 18px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #f8fbff;

  h3 {
    margin: 0 0 8px;
    color: $text-primary;
    font-size: 18px;
  }

  p {
    margin: 0;
    color: $text-secondary;
    line-height: 1.6;
  }
}

.feedback-list,
.notice-list,
.grant-user-list {
  min-height: 220px;
}

.feedback-card,
.notice-card,
.grant-user-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 18px;
  border: 1px solid $border-color-light;
  border-radius: 14px;
  background: $bg-white;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;

  & + & {
    margin-top: 12px;
  }

  &:hover {
    border-color: rgba(24, 144, 255, 0.38);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
    transform: translateY(-1px);
  }
}

.feedback-card.is-pending {
  border-color: rgba(245, 158, 11, 0.45);
  background: linear-gradient(135deg, #fffaf0 0%, #ffffff 48%);
}

.notice-card {
  position: relative;
}

.notice-card.is-unread {
  border-color: rgba(24, 144, 255, 0.42);
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 52%);
}

.feedback-card.is-batch-mode,
.notice-card.is-batch-mode {
  cursor: pointer;
}

.notice-card.is-batch-mode {
  .notice-status-dot {
    margin-top: 9px;
  }
}

.feedback-card.is-selected,
.notice-card.is-selected,
.grant-user-card.is-selected {
  border-color: #2563eb;
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.14);
}

.grant-action-area {
  justify-content: flex-start;
}

.grant-action-btn {
  white-space: normal;
}

.notice-select {
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  flex-shrink: 0;
}

.notice-status-dot {
  width: 8px;
  height: 8px;
  margin-top: 8px;
  border-radius: 999px;
  background: $border-color-light;
  flex-shrink: 0;
}

.notice-card.is-unread .notice-status-dot {
  background: #1890ff;
  box-shadow: 0 0 0 5px rgba(24, 144, 255, 0.12);
}

.card-main {
  min-width: 0;
  flex: 1;
}

.card-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.student-info,
.notice-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.student-name,
.notice-title {
  color: $text-primary;
  font-size: 16px;
  font-weight: 700;
}

.course-title,
.notice-time {
  color: $text-secondary;
  font-size: 13px;
}

.feedback-content,
.notice-content {
  margin: 10px 0;
  color: $text-secondary;
  line-height: 1.6;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  color: $text-tertiary;
  font-size: 13px;
}

.meta-identity {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  min-width: 0;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.loading-container {
  padding: 24px;
}

.detail-section {
  .detail-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid $border-color-light;

    &:last-child {
      border-bottom: none;
    }
  }

  .detail-label {
    width: 72px;
    color: $text-secondary;
    flex-shrink: 0;
  }

  .detail-value {
    color: $text-primary;
  }
}

.feedback-chat {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.chat-message {
  display: flex;
  flex-direction: column;
  max-width: 72%;
  min-width: 0;

  &--student {
    align-items: flex-start;
    align-self: flex-start;
  }

  &--teacher {
    align-items: flex-end;
    align-self: flex-end;
  }
}

.chat-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-bottom: 6px;
  color: $text-tertiary;
  font-size: 12px;
}

.chat-message--teacher .chat-meta {
  justify-content: flex-end;
  text-align: right;
}

.chat-bubble {
  box-sizing: border-box;
  max-width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  line-height: 1.7;
  color: $text-primary;
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: pre-wrap;

  &--student {
    border-top-left-radius: 4px;
    background: $bg-color;
  }

  &--teacher {
    border-top-right-radius: 4px;
    background: #e8f3ff;
  }
}

.chat-images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.feedback-image {
  box-sizing: border-box;
  width: 104px;
  max-width: 100%;
  height: 104px;
  border-radius: 10px;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.drawer-action-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.notice-detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: $text-secondary;
  font-size: 13px;
}

.notice-detail-title {
  margin: 18px 0 16px;
  color: $text-primary;
  font-size: 20px;
  line-height: 1.4;
}

.notice-detail-content {
  margin-bottom: 18px;
}

.process-summary {
  margin-bottom: 16px;
  padding: 16px;
  background: $bg-white;
  border: 1px solid $border-color-light;
  border-radius: 12px;

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
    border-radius: 8px;
    line-height: 1.6;
  }
}

@media (max-width: 768px) {
  .teacher-message-page {
    .message-hero {
      flex-direction: column;
      padding: 18px;
    }

    .stat-grid {
      grid-template-columns: 1fr;
      min-width: 0;
    }
  }

  .panel-card {
    padding: 14px;
  }

  .filter-bar,
  .filter-left,
  .filter-right {
    align-items: stretch;
    flex-direction: column;
    width: 100%;
  }

  .batch-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-select,
  .search-input,
  .filter-actions,
  .dialog-action-surface,
  .grant-action-area .soft-action-surface {
    width: 100% !important;
  }

  .feedback-card,
  .notice-card,
  .grant-user-card {
    flex-direction: column;
    gap: 12px;
    padding: 14px;
  }

  .card-topline,
  .student-info,
  .notice-title-wrap,
  .card-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .notice-status-dot {
    position: absolute;
    top: 16px;
    right: 16px;
    margin-top: 0;
  }

  .notice-card.is-batch-mode .notice-status-dot {
    top: 18px;
    right: 18px;
    margin-top: 0;
  }

  .feedback-card.is-batch-mode {
    position: relative;
  }

  .feedback-card.is-batch-mode .notice-select {
    position: absolute;
    top: 14px;
    right: 14px;
  }

  .notice-select {
    padding-top: 0;
  }

  .card-actions {
    width: 100%;
  }

  .card-actions :deep(.el-button) {
    margin-left: 0;
  }

  :deep(.message-drawer) {
    width: 92% !important;
  }

  .chat-message {
    max-width: 86%;
  }

  .feedback-image {
    max-width: 100%;
  }
}
</style>
