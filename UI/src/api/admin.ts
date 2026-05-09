import request, { type PaginatedData } from './index'

// ==================== 用户管理 ====================

interface BackendAdminUserItem {
  id: number
  username: string
  email: string
  phone?: string | null
  nickname?: string | null
  role: 'student' | 'teacher' | 'admin'
  status: 'active' | 'disabled' | 'pending'
  created_at: string
  last_login_at: string | null
}

/** 管理端用户列表项 */
export interface AdminUserItem {
  user_id: number
  username: string
  email: string
  phone: string
  nickname: string
  role: 'student' | 'teacher' | 'admin'
  status: 'active' | 'disabled' | 'pending'
  created_at: string
  last_login_at: string
}

/** 用户列表请求参数 */
export interface AdminUsersParams {
  role?: 'all' | 'student' | 'teacher' | 'admin' | 'pending'
  status?: 'all' | 'active' | 'disabled' | 'pending'
  keyword?: string
  page?: number
  page_size?: number
}

/** 用户详情 */
export interface AdminUserDetail extends AdminUserItem {
  avatar: string
  bio: string
  teacher_intro: string
}

/** 讲师审核列表项 */
export interface TeacherAuditItem {
  audit_id: number
  user_id: number
  username: string
  real_name: string
  email: string
  phone: string
  organization?: string | null
  title?: string | null
  introduction?: string | null
  certificate_urls?: string[] | null
  audit_status: 'pending' | 'approved' | 'rejected'
  created_at: string
  reviewed_at?: string | null
  review_comment?: string | null
}

/** 审核请求 */
export interface ReviewTeacherRequest {
  approve: boolean
  comment?: string
}

/** 用户状态更新请求 */
export interface UpdateUserStatusRequest {
  status: 'active' | 'disabled'
}

// ==================== 角色权限 ====================

/** 权限项 */
export interface PermissionItem {
  permission_id: number
  name: string
  code: string
  description: string
  parent_id: number | null
  children?: PermissionItem[]
}

/** 角色权限配置 */
export interface RolePermissions {
  role: 'student' | 'teacher' | 'admin'
  permissions: number[]
}

// ==================== 管理员申请 ====================

/** 管理员申请列表项 */
export interface AdminApplicationItem {
  application_id: number
  user_id: number
  username: string
  reason: string
  department?: string | null
  status: 'pending' | 'approved' | 'rejected'
  review_comment?: string | null
  created_at: string
  reviewed_at?: string | null
}

/** 管理员申请列表请求参数 */
export interface AdminApplicationsParams {
  status?: 'all' | 'pending' | 'approved' | 'rejected'
  page?: number
  page_size?: number
}

/** 管理员申请审核请求 */
export interface ReviewAdminApplicationRequest {
  approve: boolean
  comment?: string
}

// ==================== 分类管理 ====================

/** 后台分类项 */
export interface AdminCategoryItem {
  category_id: number
  name: string
  slug: string
  description?: string | null
  icon?: string | null
  sort_order: number
  parent_id: number | null
  is_active: boolean
  created_at: string
}

/** 分类表单数据 */
export interface AdminCategoryFormData {
  name: string
  slug: string
  description?: string
  icon?: string
  parent_id?: number | null
  sort_order?: number
  is_active?: boolean
}

// ==================== 标签管理 ====================

/** 后台标签项 */
export interface AdminTagItem {
  tag_id: number
  name: string
  slug: string
  color?: string | null
  use_count: number
  created_at: string
}

/** 标签列表请求参数 */
export interface AdminTagsParams {
  keyword?: string
  page?: number
  page_size?: number
}

/** 标签表单数据 */
export interface AdminTagFormData {
  name: string
  slug: string
  color?: string
}

/** 标签批量删除失败项 */
export interface AdminTagBatchDeleteFailure {
  tag_id: number
  reason: string
}

/** 标签批量删除结果 */
export interface AdminTagBatchDeleteResult {
  success_ids: number[]
  failed_items: AdminTagBatchDeleteFailure[]
  success_count: number
  failed_count: number
  message?: string | null
}

// ==================== 系统消息管理 ====================

/** 系统消息表单数据 */
export interface AdminMessageFormData {
  user_id: number | null
  type: 'announcement' | 'notification' | 'system' | 'course'
  title: string
  content: string
}

// ==================== 公告管理 ====================

/** 公告列表项 */
export interface AnnouncementItem {
  announcement_id: number
  title: string
  content: string
  status: 'draft' | 'published'
  published_at: string | null
  creator_name: string
  created_at: string
}

/** 公告表单数据 */
export interface AnnouncementFormData {
  title: string
  content: string
  status: 'draft' | 'published'
}

/** 公告列表请求参数 */
export interface AnnouncementsParams {
  status?: 'all' | 'draft' | 'published'
  keyword?: string
  page?: number
  page_size?: number
}

interface BackendTeacherAuditItem {
  id: number
  user_id: number
  username?: string | null
  real_name: string
  email: string
  phone: string
  organization?: string | null
  title?: string | null
  introduction?: string | null
  certificate_urls?: string[] | null
  status: 'pending' | 'approved' | 'rejected'
  review_comment?: string | null
  created_at: string
  reviewed_at?: string | null
}

interface BackendAdminApplicationItem {
  id: number
  user_id: number
  username?: string | null
  reason: string
  department?: string | null
  status: 'pending' | 'approved' | 'rejected'
  review_comment?: string | null
  created_at: string
  reviewed_at?: string | null
}

interface BackendCategoryItem {
  id: number
  name: string
  slug: string
  description?: string | null
  icon?: string | null
  sort_order: number
  parent_id: number | null
  is_active: boolean
  created_at: string
}

interface BackendTagItem {
  id: number
  name: string
  slug: string
  color?: string | null
  use_count: number
  created_at: string
}

interface BackendAnnouncementItem {
  id: number
  title: string
  content: string
  is_published: boolean
  publish_at: string | null
  author_id: number | null
  author_name?: string | null
  created_at: string
}

interface BackendAnnouncementPayload {
  title: string
  content: string
  is_published: boolean
  publish_at?: string | null
}

// ==================== 反馈管理 ====================

/** 反馈列表项（管理端） */
export interface AdminFeedbackItem {
  feedback_id: number
  user_id: number
  username: string | null
  feedback_type: 'system' | 'course'
  course_id: number | null
  course_title: string | null
  target_user_id: number | null
  target_username: string | null
  target_nickname: string | null
  content: string
  images: string[]
  status: 'pending' | 'processed'
  reply: string | null
  replied_at: string | null
  created_at: string
  processed_at: string | null
}

/** 反馈详情 */
export interface AdminFeedbackDetail extends AdminFeedbackItem {
  user_email: string | null
  user_phone: string | null
}

/** 反馈处理请求 */
export interface ProcessFeedbackRequest {
  reply: string
}

/** 反馈列表请求参数 */
export interface AdminFeedbacksParams {
  feedback_type?: 'all' | 'system' | 'course'
  status?: 'all' | 'pending' | 'processed'
  keyword?: string
  page?: number
  page_size?: number
}

// ==================== API 函数 ====================

// ---------- 用户管理 ----------

function mapAdminUserItem(item: BackendAdminUserItem): AdminUserItem {
  return {
    user_id: item.id,
    username: item.username,
    email: item.email,
    phone: item.phone || '',
    nickname: item.nickname || '',
    role: item.role,
    status: item.status,
    created_at: item.created_at,
    last_login_at: item.last_login_at || '',
  }
}

/** 获取用户列表 */
export function fetchUsers(params: AdminUsersParams = {}) {
  return request.get<unknown, PaginatedData<BackendAdminUserItem>>('/users', {
    params: { page: 1, page_size: 10, ...params },
  }).then((data) => ({
    ...data,
    items: data.items.map(mapAdminUserItem),
  }))
}

/** 获取用户详情 */
export function fetchUserDetail(userId: number) {
  return request.get<unknown, AdminUserDetail>(`/users/${userId}`)
}

/** 更新用户状态（禁用/启用） */
export function toggleUserStatus(userId: number, data: UpdateUserStatusRequest) {
  return request.post<unknown, void>(`/users/${userId}/status`, data)
}

/** 删除用户 */
export function deleteUser(userId: number) {
  return request.post<unknown, void>(`/users/${userId}/delete`)
}

/** 获取讲师审核列表 */
export function fetchTeacherAudits(params: { status?: 'all' | 'pending' | 'approved' | 'rejected'; page?: number; page_size?: number } = {}) {
  return request.get<unknown, PaginatedData<BackendTeacherAuditItem>>('/users/teacher-audits', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
      status: params.status === 'all' ? undefined : params.status,
    },
  }).then((data) => ({
    ...data,
    items: data.items.map(mapTeacherAuditItem),
  }))
}

/** 审核讲师 */
export function reviewTeacher(auditId: number, data: ReviewTeacherRequest) {
  return request.post<unknown, void>(`/users/teacher-audits/${auditId}/review`, data)
}

/** 获取管理员申请列表 */
export function fetchAdminApplications(params: AdminApplicationsParams = {}) {
  return request.get<unknown, PaginatedData<BackendAdminApplicationItem>>('/users/admin-applications', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
      status: params.status === 'all' ? undefined : params.status,
    },
  }).then((data) => ({
    ...data,
    items: data.items.map(mapAdminApplicationItem),
  }))
}

/** 审核管理员申请 */
export function reviewAdminApplication(applicationId: number, data: ReviewAdminApplicationRequest) {
  return request.post<unknown, void>(`/users/admin-applications/${applicationId}/review`, data)
}

/** 获取后台分类列表 */
export function fetchAdminCategories(params: { parent_id?: number; is_active?: boolean } = {}) {
  return request.get<unknown, BackendCategoryItem[]>('/categories', {
    params,
  }).then((items) => items.map(mapCategoryItem))
}

/** 创建分类 */
export function createCategory(data: AdminCategoryFormData) {
  return request.post<unknown, BackendCategoryItem>('/categories', data).then(mapCategoryItem)
}

/** 更新分类 */
export function updateCategory(categoryId: number, data: AdminCategoryFormData) {
  return request.put<unknown, BackendCategoryItem>(`/categories/${categoryId}`, data).then(mapCategoryItem)
}

/** 删除分类 */
export function deleteCategory(categoryId: number) {
  return request.delete<unknown, void>(`/categories/${categoryId}`)
}

/** 获取后台标签列表 */
export function fetchAdminTags(params: AdminTagsParams = {}) {
  return request.get<unknown, PaginatedData<BackendTagItem>>('/tags', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
      keyword: params.keyword,
    },
  }).then((data) => ({
    ...data,
    items: data.items.map(mapTagItem),
  }))
}

/** 创建标签 */
export function createAdminTag(data: AdminTagFormData) {
  return request.post<unknown, BackendTagItem>('/tags', data).then(mapTagItem)
}

/** 删除标签 */
export function deleteAdminTag(tagId: number) {
  return request.delete<unknown, void>(`/tags/${tagId}`)
}

/** 批量删除标签 */
export function batchDeleteAdminTags(tagIds: number[]) {
  return request.post<unknown, AdminTagBatchDeleteResult>('/tags/batch-delete', {
    tag_ids: tagIds,
  })
}

/** 发送系统消息 */
export function sendAdminMessage(data: AdminMessageFormData) {
  return request.post<unknown, void>('/messages/send', data)
}

// ---------- 角色权限管理 ----------

/** 获取权限树 */
export function fetchPermissionTree() {
  return request.get<unknown, PermissionItem[]>('/permissions/tree')
}

/** 获取角色权限 */
export function fetchRolePermissions(role: 'student' | 'teacher' | 'admin') {
  return request.get<unknown, number[]>(`/roles/${role}/permissions`)
}

/** 更新角色权限 */
export function updateRolePermissions(role: 'student' | 'teacher' | 'admin', permissions: number[]) {
  return request.post<unknown, void>(`/roles/${role}/permissions`, { permissions })
}

// ---------- 公告管理 ----------

/** 获取公告列表 */
export function fetchAnnouncements(params: AnnouncementsParams = {}) {
  const requestParams: Record<string, unknown> = {
    page: params.page ?? 1,
    page_size: params.page_size ?? 10,
    keyword: params.keyword,
  }

  if (params.status === 'draft') {
    requestParams.is_published = false
  } else if (params.status === 'published') {
    requestParams.is_published = true
  }

  return request.get<unknown, PaginatedData<BackendAnnouncementItem>>('/announcements', {
    params: requestParams,
  }).then((data) => ({
    ...data,
    items: data.items.map(mapAnnouncementItem),
  }))
}

/** 获取公告详情 */
export function fetchAnnouncementDetail(announcementId: number) {
  return request.get<unknown, BackendAnnouncementItem>(`/announcements/${announcementId}`)
    .then(mapAnnouncementItem)
}

/** 创建公告 */
export function createAnnouncement(data: AnnouncementFormData) {
  return request.post<unknown, BackendAnnouncementItem>(
    '/announcements',
    mapAnnouncementPayload(data)
  ).then(mapAnnouncementItem)
}

/** 更新公告 */
export function updateAnnouncement(announcementId: number, data: AnnouncementFormData) {
  return request.post<unknown, BackendAnnouncementItem>(
    `/announcements/${announcementId}`,
    mapAnnouncementPayload(data)
  ).then(mapAnnouncementItem)
}

/** 删除公告 */
export function deleteAnnouncement(announcementId: number) {
  return request.post<unknown, void>(`/announcements/${announcementId}/delete`)
}

function mapTeacherAuditItem(item: BackendTeacherAuditItem): TeacherAuditItem {
  return {
    audit_id: item.id,
    user_id: item.user_id,
    username: item.username || `用户${item.user_id}`,
    real_name: item.real_name,
    email: item.email,
    phone: item.phone,
    organization: item.organization,
    title: item.title,
    introduction: item.introduction,
    certificate_urls: item.certificate_urls,
    audit_status: item.status,
    created_at: item.created_at,
    reviewed_at: item.reviewed_at,
    review_comment: item.review_comment,
  }
}

function mapAdminApplicationItem(item: BackendAdminApplicationItem): AdminApplicationItem {
  return {
    application_id: item.id,
    user_id: item.user_id,
    username: item.username || `用户${item.user_id}`,
    reason: item.reason,
    department: item.department,
    status: item.status,
    review_comment: item.review_comment,
    created_at: item.created_at,
    reviewed_at: item.reviewed_at,
  }
}

function mapCategoryItem(item: BackendCategoryItem): AdminCategoryItem {
  return {
    category_id: item.id,
    name: item.name,
    slug: item.slug,
    description: item.description,
    icon: item.icon,
    sort_order: item.sort_order,
    parent_id: item.parent_id,
    is_active: item.is_active,
    created_at: item.created_at,
  }
}

function mapTagItem(item: BackendTagItem): AdminTagItem {
  return {
    tag_id: item.id,
    name: item.name,
    slug: item.slug,
    color: item.color,
    use_count: item.use_count,
    created_at: item.created_at,
  }
}

function mapAnnouncementItem(item: BackendAnnouncementItem): AnnouncementItem {
  return {
    announcement_id: item.id,
    title: item.title,
    content: item.content,
    status: item.is_published ? 'published' : 'draft',
    published_at: item.publish_at,
    creator_name: item.author_name || (item.author_id === null ? '-' : String(item.author_id)),
    created_at: item.created_at,
  }
}

function mapAnnouncementPayload(data: AnnouncementFormData): BackendAnnouncementPayload {
  const isPublished = data.status === 'published'
  return {
    title: data.title,
    content: data.content,
    is_published: isPublished,
    publish_at: isPublished ? undefined : null,
  }
}

// ---------- 反馈管理 ----------

/** 获取反馈列表 */
export function fetchFeedbacks(params: AdminFeedbacksParams = {}) {
  return request.get<unknown, PaginatedData<AdminFeedbackItem>>('/feedbacks', {
    params: { page: 1, page_size: 10, ...params },
  })
}

/** 获取反馈详情 */
export function fetchFeedbackDetail(feedbackId: number) {
  return request.get<unknown, AdminFeedbackDetail>(`/feedbacks/${feedbackId}`)
}

/** 标记反馈已处理 */
export function processFeedback(feedbackId: number, data: ProcessFeedbackRequest) {
  return request.post<unknown, AdminFeedbackDetail>(`/feedbacks/${feedbackId}/process`, data)
}

/** 批量标记反馈已处理 */
export function batchProcessFeedbacks(feedbackIds: number[]) {
  return request.post<unknown, void>('/feedbacks/batch-process', { feedback_ids: feedbackIds })
}
