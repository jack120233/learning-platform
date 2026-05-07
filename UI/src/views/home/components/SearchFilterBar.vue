<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCategoryStore } from '@/store/category'

const route = useRoute()
const router = useRouter()
const categoryStore = useCategoryStore()

// 选中的分类
const selectedCategory = computed({
  get: () => route.query.category_id ? Number(route.query.category_id) : 0,
  set: (val) => {
    router.push({
      query: { ...route.query, category_id: val === 0 ? undefined : val, page: 1 },
    })
  },
})

// 排序方式
const sortBy = computed({
  get: () => (route.query.sort_by as string) || 'latest',
  set: (val) => {
    router.push({
      query: { ...route.query, sort_by: val, page: 1 },
    })
  },
})

</script>

<template>
  <div class="search-filter-bar" role="region" aria-label="课程筛选">
    <!-- 分类筛选 -->
    <div class="filter-section" role="group" aria-label="分类和排序筛选">
      <div class="filter-item">
        <span class="filter-label" id="category-label">分类：</span>
        <el-radio-group
          v-model="selectedCategory"
          size="default"
          aria-labelledby="category-label"
        >
          <el-radio-button :value="0">全部</el-radio-button>
          <el-radio-button
            v-for="cat in categoryStore.getTopCategories()"
            :key="cat.category_id"
            :value="Number(cat.category_id)"
          >
            {{ cat.name }}
          </el-radio-button>
        </el-radio-group>
      </div>

      <div class="filter-item">
        <span class="filter-label" id="sort-label">排序：</span>
        <el-radio-group
          v-model="sortBy"
          size="default"
          aria-labelledby="sort-label"
        >
          <el-radio-button value="latest">最新发布</el-radio-button>
          <el-radio-button value="popular">最多学习</el-radio-button>
        </el-radio-group>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.search-filter-bar {
  margin-bottom: 24px;
  padding: 22px 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid #dbeafe;
  border-radius: 18px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-label {
  flex-shrink: 0;
  min-width: 52px;
  color: #1e293b;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.4px;
}

.search-filter-bar :deep(.el-radio-group) {
  gap: 8px;
}

.search-filter-bar :deep(.el-radio-button) {
  margin-right: 0;
}

.search-filter-bar :deep(.el-radio-button__inner) {
  height: 32px;
  padding: 0 15px;
  display: inline-flex;
  align-items: center;
  border: 1px solid transparent;
  border-radius: 999px !important;
  background: #f4f8ff;
  color: #2563eb;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.2px;
  box-shadow: none !important;
  transition: all 0.22s ease;
}

.search-filter-bar :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: transparent;
  background: linear-gradient(135deg, #1890ff 0%, #2563eb 100%);
  color: #fff;
  box-shadow: 0 8px 18px rgba(24, 144, 255, 0.22) !important;
}

.search-filter-bar :deep(.el-radio-button__inner:hover) {
  border-color: #bfdbfe;
  background: #fff;
  color: #1d4ed8;
}

.search-filter-bar :deep(.el-radio-button:first-child .el-radio-button__inner),
.search-filter-bar :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 999px !important;
}

@media (max-width: 768px) {
  .search-filter-bar {
    padding: 16px;
    border-radius: 16px;
  }

  .filter-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-filter-bar :deep(.el-radio-group) {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
  }
}
</style>
