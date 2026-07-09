import request, { type PaginatedData } from './index'

// 课程基础项（公共字段）
export interface CourseBaseItem {
  id?: number
  course_id?: number
  title: string
  cover_url?: string | null
  summary?: string | null
  teacher_name?: string | null
  author?: string | null
}

// 首页课程项
export interface HomeCourseItem extends CourseBaseItem {
  published_at: string
}

// 课程列表项
export interface CourseListItem extends CourseBaseItem {
  thumbnail_url: string
  teacher_id: number
  category_id: number
  category_name: string
  view_count: number
  published_at: string
}

// 搜索结果项
export interface CourseSearchItem extends CourseBaseItem {
  highlight?: {
    title?: string
  }
}

// 首页课程列表参数
export interface HomepageCoursesParams {
  limit?: number
}

// 课程列表参数
export interface CourseListParams {
  category_id?: number
  is_free?: boolean
  page?: number
  page_size?: number
}

// 课程搜索参数
export interface CourseSearchParams {
  keyword?: string
  category_id?: number
  sort_by?: 'published_at' | 'student_count'
  page?: number
  page_size?: number
}

// 获取首页课程列表
export function fetchHomepageCourses(params: HomepageCoursesParams = {}) {
  return request.get<unknown, HomeCourseItem[]>('/courses/homepage', {
    params: { limit: 8, ...params },
  })
}

// 获取课程列表（带筛选）
export function fetchCourseList(params: CourseListParams = {}) {
  return request.get<unknown, PaginatedData<CourseListItem>>('/courses', {
    params: { page: 1, page_size: 20, ...params },
  })
}

// 搜索课程
export function searchCourses(params: CourseSearchParams) {
  return request.get<unknown, PaginatedData<CourseSearchItem>>('/courses/search', {
    params: { page: 1, page_size: 20, ...params },
  })
}
