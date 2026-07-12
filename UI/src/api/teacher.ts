import request, { type PaginatedData } from './index'

// ==================== 老师课程管理 ====================

export type CourseStatus = 'draft' | 'published' | 'archived'
export type CourseManageScope = 'mine' | 'published_all'
export type BatchCourseAction = 'publish' | 'archive' | 'delete'

export interface TeacherCourseItem {
  id: number
  course_id: number
  title: string
  subtitle?: string | null
  summary?: string | null
  cover_url: string | null
  teacher_id: number
  teacher_name?: string | null
  author?: string | null
  status: CourseStatus
  price?: number
  original_price?: number | null
  level?: string
  is_free?: boolean
  total_duration?: number
  total_sections?: number
  student_count?: number
  rating?: number
  rating_count?: number
  view_count: number
  created_at: string
  published_at: string | null
}

/** 课程列表请求参数 */
export interface TeacherCoursesParams {
  status?: 'all' | CourseStatus
  keyword?: string
  page?: number
  page_size?: number
}

export interface ManageCoursesParams extends TeacherCoursesParams {
  scope?: CourseManageScope
}

/** 课程表单数据 */
export interface CourseFormData {
  title: string
  cover_url?: string | null
  summary?: string | null
  description?: string | null
  category_id: number | null
  tags?: string[]
}

/** 创建课程请求 */
export interface CreateCourseRequest {
  title: string
  cover_url?: string | null
  summary?: string | null
  description?: string | null
  category_id: number
  author?: string | null
  tag_ids?: number[]
  is_published?: boolean
}

/** 更新课程请求 */
export interface UpdateCourseRequest extends Partial<CreateCourseRequest> {}

/** 课程详情 */
export interface TeacherCourseDetail {
  id?: number
  course_id: number
  title: string
  cover_url?: string | null
  summary?: string | null
  description?: string | null
  category_id: number
  author?: string | null
  status: CourseStatus
  view_count: number
  created_at: string
  published_at: string | null
  tags: TagItem[]
  chapters: ChapterItem[]
  materials: MaterialItem[]
}

/** 标签项 */
export interface TagItem {
  id: number
  name: string
  slug?: string
  color?: string
}

type TagListResponse = PaginatedData<TagItem> | { items?: TagItem[]; list?: TagItem[] } | TagItem[]

/** 章节项 */
export interface ChapterItem {
  chapter_id: number
  title: string
  description?: string
  sort_order: number
  sections: SectionItem[]
  resources: ResourceItem[]
}

/** 小节项 */
export interface SectionItem {
  section_id: number
  title: string
  description?: string
  sort_order: number
  resources: ResourceItem[]
}

/** 资源项 */
export interface ResourceItem {
  resource_id: number
  resource_type: 'video' | 'audio' | 'document' | 'image'
  file_name: string
  file_url: string
  file_size: number
  duration?: number
  resolution?: string
  thumbnail_url?: string
  is_required?: boolean
}

/** 配套资料项 */
export interface MaterialItem {
  material_id: number
  file_name: string
  file_url: string
  file_size: number
}

/** 下架请求 */
export interface ArchiveCourseRequest {
  archive_reason?: string
}

export interface BatchCourseActionRequest {
  action: BatchCourseAction
  course_ids: number[]
  archive_reason?: string
}

export interface BatchCourseActionFailure {
  course_id: number
  reason: string
}

export interface BatchCourseActionResponse {
  action: BatchCourseAction
  success_ids: number[]
  failed_items: BatchCourseActionFailure[]
  success_count: number
  failed_count: number
  message?: string | null
}

export interface TeacherFeedbackItem {
  feedback_id: number
  user_id: number
  username: string | null
  feedback_type: 'system' | 'course'
  course_id: number | null
  course_title: string | null
  course_teacher_id: number | null
  target_user_id: number | null
  target_username: string | null
  content: string
  images: string[]
  status: 'pending' | 'processed'
  reply: string | null
  replied_at: string | null
  created_at: string
  processed_at: string | null
}

export interface TeacherFeedbackDetail extends TeacherFeedbackItem {
  user_email: string | null
  user_phone: string | null
}

export interface TeacherFeedbacksParams {
  feedback_type?: 'course'
  status?: 'all' | 'pending' | 'processed'
  keyword?: string
  page?: number
  page_size?: number
}

export interface ProcessTeacherFeedbackRequest {
  reply: string
}

export interface TeacherUsersParams {
  keyword?: string
  role?: 'student' | 'teacher' | 'admin'
  status?: 'active' | 'disabled' | 'pending'
  page?: number
  page_size?: number
}

export interface TeacherUserSearchItem {
  id: number
  user_id: number
  username: string
  email: string
  role: 'student' | 'teacher' | 'admin'
  status: 'active' | 'disabled' | 'pending'
  original_username: string | null
  username_change_remaining: number
  can_change_username: boolean
  created_at: string
  last_login_at: string | null
}

/** 章节表单数据 */
export interface ChapterFormData {
  title: string
  description?: string
  sort_order?: number
}

/** 小节表单数据 */
export interface SectionFormData {
  title: string
  description?: string
  sort_order?: number
}

/** 资源上传项 */
export interface ResourceUploadItem {
  resource_id?: number
  resource_type: 'video' | 'audio' | 'document' | 'image'
  title?: string
  file_name: string
  file_url: string
  file_size: number
  duration?: number
  resolution?: string
  thumbnail_url?: string
  sort_order?: number
  is_free?: boolean
  is_required?: boolean
}

/** 分片上传初始化请求 */
export interface ChunkUploadInitRequest {
  file_name: string
  file_size: number
  chunk_size: number
  content_type?: string
}

/** 分片上传初始化响应 */
export interface ChunkUploadInitResponse {
  upload_id: string
  chunk_size: number
  total_chunks: number
}

/** 分片上传完成请求 */
export interface ChunkUploadCompleteRequest {
  upload_id: string
  file_name: string
  total_chunks: number
}

/** 上传文件响应 */
export interface UploadFileResponse {
  file_url: string
  file_name: string
  file_size: number
}

// ==================== 老师课程统计 ====================

export type TeacherStatisticsPermissionType = 'all' | 'owner' | 'authorized'
export type TeacherStatisticsStudentStatus = 'all' | 'inactive' | 'low_progress' | 'completed'

export interface TeacherStatisticsCoursesParams {
  keyword?: string
  permission_type?: TeacherStatisticsPermissionType
  status?: 'all' | CourseStatus
  page?: number
  page_size?: number
}

export interface TeacherCourseStatisticsItem {
  course_id: number
  course_title: string
  course_cover?: string | null
  course_status: CourseStatus
  permission_type: 'owner' | 'authorized'
  started_student_count: number
  active_student_count_7d: number
  avg_progress: number
  completion_rate: number
  total_duration_seconds: number
  recent_learn_at?: string | null
}

export interface TeacherCourseStatisticsOverview {
  course_id: number
  course_title: string
  range: '7d' | '30d'
  started_student_count: number
  active_student_count: number
  avg_progress: number
  completion_rate: number
  avg_duration_seconds: number
  total_duration_seconds: number
  recent_learn_at?: string | null
}

export interface TeacherCourseStatisticsStudentsParams {
  status?: TeacherStatisticsStudentStatus
  keyword?: string
  page?: number
  page_size?: number
}

export interface TeacherCourseStudentStatisticsItem {
  student_id: number
  username: string
  progress: number
  total_duration_seconds: number
  last_learn_at?: string | null
  completed_at?: string | null
  is_completed: boolean
}

// ==================== 标签管理 ====================

/** 获取标签列表 */
export function fetchTags(): Promise<TagItem[]> {
  return request.get<unknown, TagListResponse>('/tags', { params: { page_size: 100 } }).then(res => {
    if (Array.isArray(res)) {
      return res
    }
    if ('items' in res && res.items) {
      return res.items
    }
    if ('list' in res && res.list) {
      return res.list
    }
    return []
  })
}

/** 创建标签 */
export function createTag(data: { name: string, slug?: string, color?: string }): Promise<TagItem> {
  const payload = {
    name: data.name,
    slug: data.slug || `t-${Math.random().toString(36).slice(2, 8)}`,
    ...(data.color ? { color: data.color } : {})
  }
  return request.post<unknown, TagItem>('/tags', payload)
}

/** 删除标签 */
export function deleteTag(tagId: number) {
  return request.delete<unknown, void>(`/tags/${tagId}`)
}

// ==================== API 函数 ====================

/** 获取我的课程列表 */
export function fetchMyCourses(params: TeacherCoursesParams = {}) {
  return request.get<unknown, PaginatedData<TeacherCourseItem>>('/courses/my-courses', {
    params: { page: 1, page_size: 10, ...params },
  })
}

/** 获取课程管理列表 */
export function fetchManageCourses(params: ManageCoursesParams = {}) {
  const normalizedStatus = params.status === 'all' ? undefined : params.status
  return request.get<unknown, PaginatedData<TeacherCourseItem>>('/courses/manage', {
    params: {
      scope: params.scope || 'mine',
      status: normalizedStatus,
      keyword: params.keyword,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

/** 获取课程详情 */
export function fetchCourseDetail(courseId: number) {
  return request.get<unknown, TeacherCourseDetail>(`/courses/${courseId}`)
}

/** 创建课程 */
export function createCourse(data: CreateCourseRequest) {
  return request.post<unknown, TeacherCourseDetail>('/courses', data)
}

/** 更新课程 */
export function updateCourse(courseId: number, data: UpdateCourseRequest) {
  return request.post<unknown, TeacherCourseDetail>(`/courses/${courseId}`, data)
}

/** 发布课程 */
export function publishCourse(courseId: number) {
  return request.post<unknown, TeacherCourseDetail>(`/courses/${courseId}/publish`)
}

/** 下架课程 */
export function archiveCourse(courseId: number, data: ArchiveCourseRequest) {
  return request.post<unknown, TeacherCourseDetail>(`/courses/${courseId}/archive`, data)
}

/** 删除课程 */
export function deleteCourse(courseId: number) {
  return request.delete<unknown, void>(`/courses/${courseId}`)
}

/** 批量课程操作 */
export function batchCourseAction(data: BatchCourseActionRequest) {
  return request.post<unknown, BatchCourseActionResponse>('/courses/batch-action', data)
}

/** 获取课程反馈列表 */
export function fetchTeacherFeedbacks(params: TeacherFeedbacksParams = {}) {
  const normalizedStatus = params.status === 'all' ? undefined : params.status
  return request.get<unknown, PaginatedData<TeacherFeedbackItem>>('/feedbacks', {
    params: {
      feedback_type: params.feedback_type ?? 'course',
      status: normalizedStatus,
      keyword: params.keyword,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

/** 获取课程反馈详情 */
export function fetchTeacherFeedbackDetail(feedbackId: number) {
  return request.get<unknown, TeacherFeedbackDetail>(`/feedbacks/${feedbackId}`)
}

/** 回复并处理课程反馈 */
export function processTeacherFeedback(feedbackId: number, data: ProcessTeacherFeedbackRequest) {
  return request.post<unknown, TeacherFeedbackDetail>(`/feedbacks/${feedbackId}/process`, data)
}

/** 删除课程反馈 */
export function deleteTeacherFeedback(feedbackId: number) {
  return request.delete<unknown, void>(`/feedbacks/${feedbackId}`)
}

/** 批量删除课程反馈 */
export async function batchDeleteTeacherFeedbacks(feedbackIds: number[]) {
  const results = await Promise.allSettled(feedbackIds.map((feedbackId) => deleteTeacherFeedback(feedbackId)))
  return {
    count: results.filter((result) => result.status === 'fulfilled').length,
  }
}

/** 搜索用户列表 */
export function fetchTeacherUsers(params: TeacherUsersParams = {}) {
  return request.get<unknown, PaginatedData<TeacherUserSearchItem>>('/users', {
    params: {
      keyword: params.keyword,
      role: params.role,
      status: params.status,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export function fetchTeacherStatisticsCourses(params: TeacherStatisticsCoursesParams = {}) {
  return request.get<unknown, PaginatedData<TeacherCourseStatisticsItem>>('/teacher/statistics/courses', {
    params: {
      keyword: params.keyword,
      permission_type: params.permission_type,
      status: params.status,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export function fetchTeacherStatisticsCourseOverview(courseId: number, range: '7d' | '30d' = '7d') {
  return request.get<unknown, TeacherCourseStatisticsOverview>(`/teacher/statistics/courses/${courseId}/overview`, {
    params: { range },
  })
}

export function fetchTeacherStatisticsCourseStudents(courseId: number, params: TeacherCourseStatisticsStudentsParams = {}) {
  return request.get<unknown, PaginatedData<TeacherCourseStudentStatisticsItem>>(`/teacher/statistics/courses/${courseId}/students`, {
    params: {
      status: params.status,
      keyword: params.keyword,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export function exportTeacherStatisticsCourseStudents(courseId: number, params: TeacherCourseStatisticsStudentsParams = {}) {
  return request.get<unknown, Blob>(`/teacher/statistics/courses/${courseId}/students/export`, {
    params: {
      status: params.status,
      keyword: params.keyword,
    },
    responseType: 'blob',
  })
}

// ---------- 标签管理 ----------

/** 获取标签列表 */

/** 开放用户名修改机会 */
export function grantUsernameChangeOpportunity(userId: number) {
  return request.post<unknown, TeacherUserSearchItem>(`/users/${userId}/username-change-opportunity`)
}

/** 获取课程章节列表 */
export function fetchChapters(courseId: number) {
  return request.get<unknown, ChapterItem[]>(`/courses/${courseId}/chapters`)
}

/** 获取章节下的小节列表 */
export function fetchSections(courseId: number, chapterId: number) {
  return request.get<unknown, SectionItem[]>(`/courses/${courseId}/chapters/${chapterId}/sections`)
}

/** 创建章节 */
export function createChapter(courseId: number, data: ChapterFormData) {
  return request.post<unknown, ChapterItem>(`/courses/${courseId}/chapters`, data)
}

/** 更新章节 */
export function updateChapter(courseId: number, chapterId: number, data: ChapterFormData) {
  return request.post<unknown, ChapterItem>(`/courses/${courseId}/chapters/${chapterId}`, data)
}

/** 删除章节 */
export function deleteChapter(courseId: number, chapterId: number) {
  return request.delete<unknown, void>(`/courses/${courseId}/chapters/${chapterId}`)
}

/** 更新章节排序 */
export function updateChapterSort(courseId: number, chapterIds: number[]) {
  return request.post<unknown, void>(`/courses/${courseId}/chapters/sort`, { chapter_ids: chapterIds })
}

// ==================== 小节管理 ====================

/** 创建小节 */
export function createSection(courseId: number, chapterId: number, data: SectionFormData) {
  return request.post<unknown, SectionItem>(`/courses/${courseId}/chapters/${chapterId}/sections`, data)
}

/** 更新小节 */
export function updateSection(courseId: number, chapterId: number, sectionId: number, data: SectionFormData) {
  return request.post<unknown, SectionItem>(`/courses/${courseId}/chapters/${chapterId}/sections/${sectionId}`, data)
}

/** 删除小节 */
export function deleteSection(courseId: number, chapterId: number, sectionId: number) {
  return request.delete<unknown, void>(`/courses/${courseId}/chapters/${chapterId}/sections/${sectionId}`)
}

/** 更新小节排序 */
export function updateSectionSort(courseId: number, chapterId: number, sectionIds: number[]) {
  return request.post<unknown, void>(`/courses/${courseId}/chapters/${chapterId}/sections/sort`, { section_ids: sectionIds })
}

// ==================== 资源管理 ====================

/** 上传资源到章节 */
export function uploadChapterResource(courseId: number, chapterId: number, data: ResourceUploadItem) {
  return request.post<unknown, ResourceItem>(`/courses/${courseId}/chapters/${chapterId}/resources`, data)
}

/** 删除章节资源 */
export function deleteChapterResource(courseId: number, chapterId: number, resourceId: number) {
  return request.post<unknown, void>(`/courses/${courseId}/chapters/${chapterId}/resources/${resourceId}/delete`)
}

/** 上传资源到小节 */
export function uploadResource(courseId: number, sectionId: number, data: ResourceUploadItem) {
  return request.post<unknown, ResourceItem>(`/courses/${courseId}/sections/${sectionId}/resources`, data)
}

/** 删除资源 */
export function deleteResource(courseId: number, sectionId: number, resourceId: number) {
  return request.post<unknown, void>(`/courses/${courseId}/sections/${sectionId}/resources/${resourceId}/delete`)
}

// ==================== 配套资料 ====================

/** 上传配套资料 */
export function uploadMaterial(courseId: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<unknown, MaterialItem>(`/courses/${courseId}/materials`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 删除配套资料 */
export function deleteMaterial(courseId: number, materialId: number) {
  return request.post<unknown, void>(`/courses/${courseId}/materials/${materialId}/delete`)
}

// ==================== 文件上传 ====================

/** 上传文件（普通） */
export function uploadFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<unknown, UploadFileResponse>('/upload/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 初始化分片上传 */
export function initChunkUpload(data: ChunkUploadInitRequest) {
  return request.post<unknown, ChunkUploadInitResponse>('/upload/init', data)
}

/** 上传分片 */
export function uploadChunk(uploadId: string, chunkIndex: number, chunk: Blob) {
  const formData = new FormData()
  formData.append('upload_id', uploadId)
  formData.append('chunk_index', String(chunkIndex))
  formData.append('chunk', chunk)
  return request.post<unknown, { chunk_index: number }>('/upload/chunk', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 完成分片上传 */
export function completeChunkUpload(data: ChunkUploadCompleteRequest) {
  return request.post<unknown, UploadFileResponse>('/upload/complete', data)
}
