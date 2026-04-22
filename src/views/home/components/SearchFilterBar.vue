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
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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
  font-size: 14px;
  color: #333;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .filter-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
