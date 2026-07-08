<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCategoryStore } from '@/store/category'
import { fetchCourseList, searchCourses, type CourseBaseItem } from '@/api/course'

import BannerCarousel from './components/BannerCarousel.vue'
import SearchFilterBar from './components/SearchFilterBar.vue'
import CourseListSection from './components/CourseListSection.vue'
import PaginationBar from './components/PaginationBar.vue'

const route = useRoute()
const categoryStore = useCategoryStore()

// 课程列表（使用公共类型）
const courseList = ref<CourseBaseItem[]>([])
const loading = ref(true)
const error = ref(false)
const total = ref(0)

function normalizeSortBy(sortBy: unknown) {
  if (sortBy === 'popular') return 'student_count' as const
  if (sortBy === 'latest') return 'published_at' as const
  return undefined
}

// 加载课程数据
const loadCourses = async () => {
  loading.value = true
  error.value = false

  try {
    const { keyword, category_id, sort_by, page, page_size } = route.query
    const normalizedPage = Number(page) || 1
    const normalizedPageSize = Number(page_size) || 20
    const normalizedCategoryId = category_id ? Number(category_id) : undefined
    const normalizedSortBy = normalizeSortBy(sort_by)

    if (keyword || normalizedSortBy) {
      // 搜索和排序模式走搜索接口，确保参数与后端协议一致
      const res = await searchCourses({
        keyword: keyword as string | undefined,
        category_id: normalizedCategoryId,
        sort_by: normalizedSortBy,
        page: normalizedPage,
        page_size: normalizedPageSize,
      })
      courseList.value = res.items || []
      total.value = res.total || 0
    } else {
      // 未搜索时也走标准列表接口，避免 /homepage 的 limit 接口与分页栏协议不一致
      const res = await fetchCourseList({
        category_id: normalizedCategoryId,
        page: normalizedPage,
        page_size: normalizedPageSize,
      })
      courseList.value = res.items || []
      total.value = res.total || 0
    }
  } catch (err) {
    console.error('加载课程失败:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

// 重试加载
const handleRetry = () => {
  loadCourses()
}

// 监听路由变化
watch(
  () => route.query,
  () => {
    loadCourses()
  },
  { deep: true }
)

// 初始化
onMounted(async () => {
  // 加载分类数据
  await categoryStore.loadCategories()
  // 加载课程数据
  loadCourses()
})
</script>

<template>
  <div class="home-page">
    <div class="page-container">
      <!-- 顶部展示区 -->
      <BannerCarousel />

      <!-- 搜索筛选 -->
      <SearchFilterBar />

      <!-- 课程列表 -->
      <CourseListSection
        :courses="courseList"
        :loading="loading"
        :error="error"
        @retry="handleRetry"
      />

      <!-- 分页 -->
      <PaginationBar :total="total" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.home-page {
  padding: 24px 0 40px;
  min-height: calc(100vh - 64px - 200px);
}

.page-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

@media (max-width: 768px) {
  .home-page {
    padding-top: 16px;
  }

  .page-container {
    padding: 0 14px;
  }
}
</style>
