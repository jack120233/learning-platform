import request, { type PaginatedData } from './index'

// ==================== 类型定义 ====================

interface BackendUserProfile {
  id?: number
  user_id?: number
  username: string
  original_username?: string | null
  username_change_remaining?: number | null
  can_change_username?: boolean | null
  email: string
  phone?: string | null
  role: 'student' | 'teacher' | 'admin'
  status: 'active' | 'disabled' | 'pending'
  created_at: string
  last_login_at?: string | null
}

/** 用户详细信息 */
export interface UserProfile {
  user_id: number | null
  username: string
  original_username: string | null
  username_change_remaining: number
  can_change_username: boolean
  email: string
  phone: string
  role: 'student' | 'teacher' | 'admin'
  status: 'active' | 'disabled' | 'pending'
  created_at: string
  last_login_at: string
}

/** 更新个人信息请求 */
export interface UpdateProfileRequest {
  username?: string
  email?: string
  phone?: string
  email_code?: string
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

/** 发送邮箱验证码请求 */
export interface SendEmailCodeRequest {
  email: string
  purpose: 'bind_email' | 'change_email'
}

/** 学习记录项 */
export interface LearningRecordItem {
  id: number
  course_id: number
  course_title: string
  course_name?: string | null
  course_cover: string | null
  progress: number
  total_duration: number
  last_section_id: number | null
  last_section_title: string | null
  last_learn_at: string
  course_status: 'published' | 'archived' | string
  completed_at: string | null
  created_at: string
  updated_at: string
}

/** 学习记录请求参数 */
export interface LearningRecordsParams {
  time_range: 'recent_7' | 'recent_30' | 'all'
  page?: number
  page_size?: number
}

/** 消息项 */
export interface MessageItem {
  message_id: number
  message_type: 'announcement' | 'notification'
  title: string
  content: string
  is_read: boolean
  created_at: string
}

/** 消息列表请求参数 */
export interface MessagesParams {
  message_type?: 'all' | 'announcement' | 'notification'
  is_read?: boolean
  page?: number
  page_size?: number
}

/** 消息列表响应（含未读数） */
export interface MessagesListData extends PaginatedData<MessageItem> {
  unread_count: number
}

/** 消息详情 */
export interface MessageDetail extends MessageItem {
  read_at: string | null
  link?: string | null
}

/** 反馈项 */
export interface FeedbackItem {
  feedback_id: number
  feedback_type: 'system' | 'course'
  title?: string
  content: string
  images: string[]
  status: 'pending' | 'processed'
  course_id?: number
  course_title?: string
  target_user_id?: number | null
  target_username?: string | null
  reply?: string | null
  replied_at?: string | null
  created_at: string
}

/** 我的反馈请求参数 */
export interface MyFeedbacksParams {
  page?: number
  page_size?: number
}

// ==================== API 函数 ====================

/**
 * 获取个人信息
 */
export function fetchProfile(): Promise<UserProfile> {
  return request.get<unknown, BackendUserProfile>('/users/me')
    .then(mapUserProfile)
}

/**
 * 获取当前用户权限编码列表
 */
export function fetchMyPermissions(): Promise<string[]> {
  return request.get<unknown, string[]>('/users/me/permissions')
}

/**
 * 更新个人信息
 */
export function updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
  return request.post<unknown, BackendUserProfile>('/users/me', data)
    .then(mapUserProfile)
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordRequest): Promise<{ success: boolean }> {
  return request.post<unknown, { success: boolean }>('/users/me/change-password', data)
}

/**
 * 发送邮箱验证码
 */
export function sendEmailCode(data: SendEmailCodeRequest): Promise<{ success: boolean }> {
  return request.post<unknown, { success: boolean }>('/auth/send-email-code', data)
}

/**
 * 获取学习记录列表
 */
export function fetchLearningRecords(params: LearningRecordsParams): Promise<PaginatedData<LearningRecordItem>> {
  return request.get<unknown, PaginatedData<LearningRecordItem>>('/users/me/learning-records', {
    params: { page: 1, page_size: 10, ...params },
  })
}

/**
 * 删除/隐藏学习记录
 */
export function deleteLearningRecords(recordIds: number[]): Promise<{ deleted_count: number }> {
  return request.post<unknown, { deleted_count: number }>('/users/me/learning-records/delete', {
    record_ids: recordIds,
  })
}

/**
 * 获取消息列表
 */
export async function fetchMessages(params: MessagesParams = {}): Promise<MessagesListData> {
  const requestParams: Record<string, unknown> = {
    page: params.page ?? 1,
    page_size: params.page_size ?? 10,
    is_read: params.is_read,
  }

  if (params.message_type && params.message_type !== 'all') {
    requestParams.type = params.message_type
  }

  const [listData, unreadData] = await Promise.all([
    request.get<unknown, PaginatedData<BackendMessageItem>>('/messages', {
      params: requestParams,
    }),
    request.get<unknown, BackendUnreadCountResponse>('/messages/unread-count'),
  ])

  return {
    ...listData,
    items: listData.items.map(mapMessageItem),
    unread_count: unreadData.total,
  }
}

/**
 * 获取消息详情
 */
export function fetchMessageDetail(id: number): Promise<MessageDetail> {
  return request.get<unknown, BackendMessageItem>(`/messages/${id}`)
    .then(mapMessageDetail)
}

/**
 * 标记消息已读
 */
export function markAsRead(id: number): Promise<{ success: boolean }> {
  return request.post<unknown, { success: boolean }>(`/messages/${id}/read`)
}

/**
 * 批量标记所有消息已读
 */
export function markAllRead(): Promise<{ success: boolean }> {
  return request.post<unknown, { success: boolean }>('/messages/mark-all-read')
}

/**
 * 删除消息
 */
export function deleteMessage(id: number): Promise<{ success: boolean }> {
  return request.delete<unknown, { success: boolean }>(`/messages/${id}`)
}

/**
 * 获取未读消息数
 */
export function fetchUnreadCount(): Promise<{ unread_count: number }> {
  return request.get<unknown, BackendUnreadCountResponse>('/messages/unread-count')
    .then((data) => ({ unread_count: data.total }))
}

/**
 * 获取我的反馈列表
 */
export async function fetchMyFeedbacks(params: MyFeedbacksParams = {}): Promise<PaginatedData<FeedbackItem>> {
  const data = await request.get<unknown, PaginatedData<BackendFeedbackItem>>('/users/me/feedbacks', {
    params: { page: 1, page_size: 10, ...params },
  })

  return {
    ...data,
    items: data.items.map(mapFeedbackItem),
  }
}

/**
 * 删除我的反馈
 */
export function deleteMyFeedback(feedbackId: number): Promise<void> {
  return request.delete<unknown, void>(`/feedbacks/${feedbackId}`)
}

interface BackendMessageItem {
  id: number
  type: string
  title: string
  content: string
  link?: string | null
  is_read: boolean
  read_at: string | null
  created_at: string
}

interface BackendFeedbackItem {
  id: number
  feedback_id?: number
  type: string
  feedback_type?: 'system' | 'course'
  title: string
  content: string
  contact?: string | null
  images?: string[] | null
  status: string
  reply?: string | null
  replied_at?: string | null
  course_id?: number | null
  course_title?: string | null
  target_user_id?: number | null
  target_username?: string | null
  created_at: string
}

interface BackendUnreadCountResponse {
  total: number
  announcement?: number
  notification?: number
  system?: number
  course?: number
  interaction?: number
}

function mapUserProfile(profile: BackendUserProfile): UserProfile {
  const remaining = Math.max(profile.username_change_remaining ?? 1, 0)

  return {
    user_id: profile.user_id ?? profile.id ?? null,
    username: profile.username,
    original_username: profile.original_username ?? null,
    username_change_remaining: remaining,
    can_change_username: profile.can_change_username ?? remaining > 0,
    email: profile.email,
    phone: profile.phone ?? '',
    role: profile.role,
    status: profile.status,
    created_at: profile.created_at,
    last_login_at: profile.last_login_at ?? '',
  }
}

function mapMessageType(type: string): MessageItem['message_type'] {
  return type === 'announcement' ? 'announcement' : 'notification'
}

function mapMessageItem(item: BackendMessageItem): MessageItem {
  return {
    message_id: item.id,
    message_type: mapMessageType(item.type),
    title: item.title,
    content: item.content,
    is_read: item.is_read,
    created_at: item.created_at,
  }
}

function mapMessageDetail(item: BackendMessageItem): MessageDetail {
  return {
    ...mapMessageItem(item),
    read_at: item.read_at,
    link: item.link ?? null,
  }
}

function mapFeedbackItem(item: BackendFeedbackItem): FeedbackItem {
  const normalizedStatus = ['processed', 'resolved', 'closed'].includes(item.status) ? 'processed' : 'pending'
  const feedbackType = item.feedback_type ?? (item.type === 'course' ? 'course' : 'system')

  return {
    feedback_id: item.feedback_id ?? item.id,
    feedback_type: feedbackType,
    title: item.title,
    content: item.content,
    images: item.images ?? [],
    status: normalizedStatus,
    course_id: item.course_id ?? undefined,
    course_title: item.course_title ?? undefined,
    target_user_id: item.target_user_id ?? null,
    target_username: item.target_username ?? null,
    reply: item.reply ?? null,
    replied_at: item.replied_at ?? null,
    created_at: item.created_at,
  }
}
