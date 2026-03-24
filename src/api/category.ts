import request from './index'

// 分类
export interface Category {
  category_id: number
  name: string
  parent_id: number | null
  icon_url?: string
  sort_order: number
  is_enabled: boolean
  children?: Category[]
}

// 获取分类列表
export function fetchCategories(parentId?: number, isEnabled = true) {
  return request.get<unknown, Category[]>('/categories', {
    params: {
      parent_id: parentId,
      is_enabled: isEnabled,
    },
  })
}