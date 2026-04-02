import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { PaginatedData } from '@/api/index'

/**
 * 分页状态
 */
export interface PaginationState<T> {
  items: Ref<T[]>
  total: Ref<number>
  page: Ref<number>
  pageSize: Ref<number>
  totalPages: ComputedRef<number>
  isLoading: Ref<boolean>
  isEmpty: ComputedRef<boolean>
}

/**
 * 分页操作
 */
export interface PaginationActions {
  fetchData: (resetPage?: boolean) => Promise<void>
  goToPage: (p: number) => Promise<void>
  setPageSize: (size: number) => Promise<void>
  refresh: () => Promise<void>
}

/**
 * 分页请求函数类型
 */
export type FetchFn<T, P = Record<string, unknown>> = (params: P & { page?: number; page_size?: number }) => Promise<PaginatedData<T>>

/**
 * 通用分页 Composable
 * @param fetchFn 分页请求函数
 * @param defaultPageSize 默认每页数量
 */
export function usePagination<T, P extends object = Record<string, unknown>>(
  fetchFn: FetchFn<T, P>,
  defaultPageSize: number = 10
): PaginationState<T> & PaginationActions {
  // 状态
  const items: Ref<T[]> = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(defaultPageSize)
  const isLoading = ref(false)

  // 计算属性
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)
  const isEmpty = computed(() => !isLoading.value && items.value.length === 0)

  /**
   * 获取数据
   * @param resetPage 是否重置页码
   */
  async function fetchData(resetPage: boolean = false) {
    if (isLoading.value) return

    if (resetPage) {
      page.value = 1
    }

    isLoading.value = true
    try {
      const result = await fetchFn({
        page: page.value,
        page_size: pageSize.value,
      } as P & { page: number; page_size: number })

      const rawResult = result as any
      const list = rawResult?.items || rawResult?.list || (Array.isArray(rawResult) ? rawResult : [])
      items.value = list || []
      total.value = rawResult?.total || list?.length || 0
    } catch (error) {
      console.error('分页数据加载失败:', error)
      items.value = []
      total.value = 0
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 跳转到指定页
   */
  async function goToPage(p: number) {
    if (p < 1 || p > totalPages.value || p === page.value) return
    page.value = p
    await fetchData()
  }

  /**
   * 设置每页数量
   */
  async function setPageSize(size: number) {
    if (size === pageSize.value) return
    pageSize.value = size
    page.value = 1
    await fetchData()
  }

  /**
   * 刷新当前页
   */
  async function refresh() {
    await fetchData()
  }

  return {
    items,
    total,
    page,
    pageSize,
    totalPages,
    isLoading,
    isEmpty,
    fetchData,
    goToPage,
    setPageSize,
    refresh,
  }
}