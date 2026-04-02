import request, { type PaginatedData } from './index'

// ==================== 讲师课程管理 ====================

export interface TeacherCourseItem {
  id?: number
  course_id: number
  title: string
  cover_url: string
  status: 'draft' | 'published' | 'archived'
  view_count: number
  created_at: string
  published_at: string | null
}

/** 课程列表请求参数 */
export interface TeacherCoursesParams {
  status?: 'all' | 'draft' | 'published' | 'archived'
  keyword?: string
  page?: number
  page_size?: number
}

/** 课程表单数据 */
export interface CourseFormData {
  title: string
  cover_url: string
  summary: string
  description?: string
  category_id: number | null
  tags?: string[]
}

/** 创建课程请求 */
export interface CreateCourseRequest {
  title: string
  cover_url: string
  summary: string
  description?: string
  category_id: number
  tags?: string[]
}

/** 更新课程请求 */
export interface UpdateCourseRequest extends Partial<CreateCourseRequest> {}

/** 课程详情 */
export interface TeacherCourseDetail extends CourseFormData {
  course_id: number
  status: 'draft' | 'published' | 'archived'
  view_count: number
  created_at: string
  published_at: string | null
  chapters: ChapterItem[]
  materials: MaterialItem[]
}

/** 章节项 */
export interface ChapterItem {
  chapter_id: number
  title: string
  sort_order: number
  sections: SectionItem[]
}

/** 小节项 */
export interface SectionItem {
  section_id: number
  title: string
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
  archive_reason: string
}

/** 章节表单数据 */
export interface ChapterFormData {
  title: string
  sort_order?: number
}

/** 小节表单数据 */
export interface SectionFormData {
  title: string
  sort_order?: number
}

/** 资源上传项 */
export interface ResourceUploadItem {
  resource_id?: number
  resource_type: 'video' | 'audio' | 'document' | 'image'
  file_name: string
  file_url: string
  file_size: number
  duration?: number
  resolution?: string
  thumbnail_url?: string
}

/** 分片上传初始化请求 */
export interface ChunkUploadInitRequest {
  file_name: string
  file_size: number
  chunk_size: number
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

// ==================== 标签管理 ====================

/** 获取标签列表 */
export function fetchTags() {
  return request.get<unknown, any>('/tags', { params: { page_size: 100 } }).then(res => {
    const list = res.items || res.list || (Array.isArray(res) ? res : [])
    return list.map((item: any) => typeof item === 'string' ? item : item.name)
  })
}

/** 创建标签 */
export function createTag(data: { name: string, slug?: string, color?: string }) {
  const payload = {
    name: data.name,
    slug: data.slug || `t-${Math.random().toString(36).slice(2, 8)}`,
    ...(data.color ? { color: data.color } : {})
  }
  return request.post<unknown, any>('/tags', payload)
}

// ==================== API 函数 ====================

/** 获取我的课程列表 */
export function fetchMyCourses(params: TeacherCoursesParams = {}) {
  return request.get<unknown, PaginatedData<TeacherCourseItem>>('/courses/my-courses', {
    params: { page: 1, page_size: 10, ...params },
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
  return request.post<unknown, void>(`/courses/${courseId}/publish`)
}

/** 下架课程 */
export function archiveCourse(courseId: number, data: ArchiveCourseRequest) {
  return request.post<unknown, void>(`/courses/${courseId}/archive`, data)
}

/** 删除课程 */
export function deleteCourse(courseId: number) {
  return request.post<unknown, void>(`/courses/${courseId}/delete`)
}

// ==================== 章节管理 ====================

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
  return request.post<unknown, void>(`/courses/${courseId}/chapters/${chapterId}/delete`)
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
  return request.post<unknown, void>(`/courses/${courseId}/chapters/${chapterId}/sections/${sectionId}/delete`)
}

/** 更新小节排序 */
export function updateSectionSort(courseId: number, chapterId: number, sectionIds: number[]) {
  return request.post<unknown, void>(`/courses/${courseId}/chapters/${chapterId}/sections/sort`, { section_ids: sectionIds })
}

// ==================== 资源管理 ====================

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