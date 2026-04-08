import request, { type PaginatedData } from './index'

// ==================== 用户管理 ====================

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
  email: string
  phone: string
  nickname: string
  audit_status: 'pending' | 'approved' | 'rejected'
  created_at: string
  reject_reason?: string
}

/** 审核请求 */
export interface ReviewTeacherRequest {
  audit_status: 'approved' | 'rejected'
  reject_reason?: string
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

// ==================== 反馈管理 ====================

/** 反馈列表项（管理端） */
export interface AdminFeedbackItem {
  feedback_id: number
  user_id: number
  username: string
  feedback_type: 'system' | 'course'
  course_id: number | null
  course_title: string | null
  content: string
  images: string[]
  status: 'pending' | 'processed'
  created_at: string
  processed_at: string | null
}

/** 反馈详情 */
export interface AdminFeedbackDetail extends AdminFeedbackItem {
  user_email: string
  user_phone: string
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

/** 获取用户列表 */
export function fetchUsers(params: AdminUsersParams = {}) {
  return request.get<unknown, PaginatedData<AdminUserItem>>('/users', {
    params: { page: 1, page_size: 10, ...params },
  })
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
  return request.get<unknown, PaginatedData<TeacherAuditItem>>('/users/teacher-audits', {
    params: { page: 1, page_size: 10, ...params },
  })
}

/** 审核讲师 */
export function reviewTeacher(auditId: number, data: ReviewTeacherRequest) {
  return request.post<unknown, void>(`/users/teacher-audits/${auditId}/review`, data)
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
  return request.get<unknown, PaginatedData<AnnouncementItem>>('/announcements', {
    params: { page: 1, page_size: 10, ...params },
  })
}

/** 获取公告详情 */
export function fetchAnnouncementDetail(announcementId: number) {
  return request.get<unknown, AnnouncementItem>(`/announcements/${announcementId}`)
}

/** 创建公告 */
export function createAnnouncement(data: AnnouncementFormData) {
  return request.post<unknown, AnnouncementItem>('/announcements', data)
}

/** 更新公告 */
export function updateAnnouncement(announcementId: number, data: AnnouncementFormData) {
  return request.post<unknown, AnnouncementItem>(`/announcements/${announcementId}`, data)
}

/** 删除公告 */
export function deleteAnnouncement(announcementId: number) {
  return request.post<unknown, void>(`/announcements/${announcementId}/delete`)
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
export function processFeedback(feedbackId: number) {
  return request.post<unknown, void>(`/feedbacks/${feedbackId}/process`)
}

/** 批量标记反馈已处理 */
export function batchProcessFeedbacks(feedbackIds: number[]) {
  return request.post<unknown, void>('/feedbacks/batch-process', { feedback_ids: feedbackIds })
}