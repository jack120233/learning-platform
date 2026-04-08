import request, { type PaginatedData } from './index'

// 课程基础项（公共字段）
export interface CourseBaseItem {
  id?: number
  course_id?: number
  title: string
  cover_url: string
  summary: string
  teacher_name: string
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
  page?: number
  page_size?: number
}

// 课程列表参数
export interface CourseListParams {
  keyword?: string
  category_id?: number
  sort_by?: 'latest' | 'popular'
  page?: number
  page_size?: number
}

// 课程搜索参数
export interface CourseSearchParams {
  q: string
  page?: number
  page_size?: number
}

// 获取首页课程列表
export function fetchHomepageCourses(params: HomepageCoursesParams = {}) {
  return request.get<unknown, PaginatedData<HomeCourseItem>>('/courses/homepage', {
    params: { page: 1, page_size: 20, ...params },
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