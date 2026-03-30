<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCategoryStore } from '@/store/category'
import { fetchHomepageCourses, fetchCourseList, searchCourses, type CourseBaseItem } from '@/api/course'

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

// 加载课程数据
const loadCourses = async () => {
  loading.value = true
  error.value = false

  try {
    const { keyword, category_id, sort_by, page, page_size } = route.query

    if (keyword) {
      // 搜索模式
      const res = await searchCourses({
        q: keyword as string,
        page: Number(page) || 1,
        page_size: Number(page_size) || 20,
      })
      courseList.value = res.items || []
      total.value = res.total || 0
    } else if (category_id || sort_by) {
      // 筛选模式
      const res = await fetchCourseList({
        category_id: category_id ? Number(category_id) : undefined,
        sort_by: sort_by as 'latest' | 'popular',
        page: Number(page) || 1,
        page_size: Number(page_size) || 20,
      })
      courseList.value = res.items || []
      total.value = res.total || 0
    } else {
      // 首页模式
      const res = await fetchHomepageCourses({
        page: Number(page) || 1,
        page_size: Number(page_size) || 20,
      })
      // 兼容直接返回数组或分页对象
      if (Array.isArray(res)) {
        courseList.value = res
        total.value = res.length
      } else {
        courseList.value = (res as any).items || []
        total.value = (res as any).total || 0
      }
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
      <!-- Banner轮播 -->
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
</style>