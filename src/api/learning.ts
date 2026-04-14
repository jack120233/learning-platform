import request from './index'

// ==================== 类型定义 ====================

/** 课程详情完整数据 */
export interface CourseDetail {
  id?: number        // 后端物理主键
  course_id?: number // 兼容旧字段
  title: string
  cover_url: string
  thumbnail_url?: string
  summary: string
  description: string
  teacher_id: number
  teacher_name: string | null
  teacher_avatar?: string
  author?: string
  category_id: number
  category_name: string | null
  tags: Array<string | { id: number; name?: string }> // 后端返回对象数组
  status: 'draft' | 'published' | 'archived'
  view_count?: number
  student_count?: number
  rating?: number
  level?: string
  is_free?: boolean
  price?: number
  published_at: string
  total_sections?: number
  materials?: CourseMaterial[]
  chapters?: CourseChapter[]
}

/** 配套资料 */
export interface CourseMaterial {
  material_id: number
  file_name: string
  file_url: string
  file_size: number
  download_count: number
}

/** 课程章节 */
export interface CourseChapter {
  id?: number          // 后端返回字段
  chapter_id?: number  // 兼容旧字段
  course_id?: number
  title: string
  description?: string | null
  sort_order: number
  is_free?: boolean
  total_duration?: number
  section_count?: number
  sections: CourseSection[]
}

/** 课程小节 */
export interface CourseSection {
  id?: number          // 后端返回字梘
  section_id?: number  // 兼容旧字段
  chapter_id?: number
  course_id?: number
  title: string
  description?: string | null
  sort_order: number
  is_free?: boolean
  duration?: number
  resource_count?: number
  resources?: SectionResource[]  // 详情页可能不返回
}

/** 小节资源 */
export interface SectionResource {
  resource_id: number
  resource_type: 'video' | 'audio' | 'document' | 'image'
  file_name: string
  duration?: number
}

/** 继续学习信息 */
export interface ContinueLearningInfo {
  course_id: number
  last_section_id: number
  last_section_title: string
  last_resource_id: number
  last_resource_type: string
  current_time: number
  last_learn_at: string
}

/** 资源播放地址响应 */
export interface ResourcePlayInfo {
  resource_id: number
  resource_type: 'video' | 'audio' | 'document' | 'image'
  file_url: string
  duration?: number
  resolution?: string
  thumbnail_url?: string
}

/** 保存学习进度请求 */
export interface SaveProgressRequest {
  section_id: number
  resource_id: number
  current_time: number
  total_time: number
  is_completed: boolean
}

/** 学习进度 */
export interface LearningProgress {
  section_id: number
  resource_id: number
  current_time: number
  total_time: number
  is_completed: boolean
  last_learn_at: string
}

/** 提交反馈请求 */
export interface SubmitFeedbackRequest {
  feedback_type: 'system' | 'course'
  course_id?: number
  content: string
  images?: string[]
}

/** 提交反馈响应 */
export interface SubmitFeedbackResponse {
  feedback_id: number
  created_at: string
}

/** 上传文件响应 */
export interface UploadFileResponse {
  file_url: string
  file_name: string
  file_size: number
}

// ==================== API 函数 ====================

/**
 * 获取课程详情
 */
export function fetchCourseDetail(courseId: number): Promise<CourseDetail> {
  return request.get<unknown, CourseDetail>(`/courses/${courseId}`)
}

/**
 * 获取继续学习信息
 */
export function fetchContinueInfo(courseId: number): Promise<ContinueLearningInfo> {
  return request.get<unknown, ContinueLearningInfo>(`/learning/courses/${courseId}/continue`)
}

/**
 * 开始学习（首次学习）
 */
export function startLearning(courseId: number): Promise<{ course_id: number; started_at: string }> {
  return request.post<unknown, { course_id: number; started_at: string }>(`/learning/courses/${courseId}/start`)
}

/**
 * 获取资源播放地址
 */
export function getResourcePlayUrl(resourceId: number): Promise<ResourcePlayInfo> {
  return request.get<unknown, ResourcePlayInfo>(`/learning/resources/${resourceId}/play`)
}

/**
 * 获取学习进度
 */
export function getProgress(sectionId: number, resourceId: number): Promise<LearningProgress> {
  return request.get<unknown, LearningProgress>('/learning/progress', {
    params: { section_id: sectionId, resource_id: resourceId },
  })
}

/**
 * 保存学习进度
 */
export function saveProgress(data: SaveProgressRequest): Promise<{ success: boolean }> {
  return request.post<unknown, { success: boolean }>('/learning/progress', data)
}

/**
 * 提交反馈
 */
export function submitFeedback(data: SubmitFeedbackRequest): Promise<SubmitFeedbackResponse> {
  return request.post<unknown, SubmitFeedbackResponse>('/feedbacks', data)
}

/**
 * 上传文件
 */
export function uploadFile(file: File): Promise<UploadFileResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<unknown, UploadFileResponse>('/upload/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}