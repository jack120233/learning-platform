import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchCategories, type CategoryItem } from '@/api/category'

export const useCategoryStore = defineStore('category', () => {
  // 状态
  const categories = ref<CategoryItem[]>([])
  const isLoaded = ref(false)
  const loading = ref(false)

  // 加载分类
  async function loadCategories() {
    if (isLoaded.value) return categories.value

    loading.value = true
    try {
      categories.value = await fetchCategories()
      isLoaded.value = true
      return categories.value
    } catch (error) {
      console.error('加载分类失败:', error)
      return []
    } finally {
      loading.value = false
    }
  }

  // 获取启用的一级分类
  function getTopCategories() {
    return categories.value.filter((cat) => cat.parent_id === null)
  }

  // 根据ID获取分类
  function getCategoryById(id: number) {
    return categories.value.find((cat) => cat.category_id === id)
  }

  return {
    categories,
    isLoaded,
    loading,
    loadCategories,
    getTopCategories,
    getCategoryById,
  }
})