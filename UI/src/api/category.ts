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
  return request.get<unknown, any[]>('/categories', {
    params: {
      parent_id: parentId,
      is_enabled: isEnabled,
    },
  }).then(data => {
    // 兼容后端返回 id 而前端期望 category_id 的差异
    const mapData = (list: any[]): CategoryItem[] => {
      return list.map(item => ({
        ...item,
        category_id: item.category_id !== undefined ? item.category_id : item.id,
        children: item.children ? mapData(item.children) : undefined
      }))
    }
    return mapData(data)
  })
}