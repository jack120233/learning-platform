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

// 分类项（用于表单选择）
export interface CategoryItem {
  category_id: number
  name: string
  parent_id: number | null
  children?: CategoryItem[]
}

// 获取分类列表
export function fetchCategories(parentId?: number, isEnabled = true): Promise<CategoryItem[]> {
  return request.get<unknown, Category[]>('/categories', {
    params: {
      parent_id: parentId,
      is_enabled: isEnabled,
    },
  })
}