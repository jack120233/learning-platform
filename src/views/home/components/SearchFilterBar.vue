<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { debounce } from 'lodash-es'
import { useCategoryStore } from '@/store/category'

const route = useRoute()
const router = useRouter()
const categoryStore = useCategoryStore()

// 搜索关键词
const keyword = ref((route.query.keyword as string) || '')

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

// 搜索历史
const searchHistory = ref<string[]>([])

// 热门搜索词
const hotKeywords = ['Python', '前端开发', '数据分析', '人工智能', '职业技能']

// 加载搜索历史
const loadSearchHistory = () => {
  const stored = localStorage.getItem('edu_search_history')
  if (stored) {
    searchHistory.value = JSON.parse(stored)
  }
}

// 保存搜索历史
const saveSearchHistory = (kw: string) => {
  const history = searchHistory.value.filter((item) => item !== kw)
  history.unshift(kw)
  if (history.length > 10) history.pop()
  searchHistory.value = history
  localStorage.setItem('edu_search_history', JSON.stringify(history))
}

// 清除搜索历史
const clearHistory = () => {
  searchHistory.value = []
  localStorage.removeItem('edu_search_history')
}

// 搜索处理（防抖）
const handleSearch = debounce(() => {
  if (keyword.value.trim()) {
    saveSearchHistory(keyword.value.trim())
    router.push({
      query: { ...route.query, keyword: keyword.value.trim(), page: 1 },
    })
  }
}, 300)

// 清空搜索
const clearSearch = () => {
  keyword.value = ''
  const newQuery = { ...route.query }
  delete newQuery.keyword
  router.push({ query: newQuery })
}

// 点击历史搜索
const handleHistoryClick = (kw: string) => {
  keyword.value = kw
  handleSearch()
}

// 点击热门词
const handleHotClick = (kw: string) => {
  keyword.value = kw
  handleSearch()
}

// 初始化
loadSearchHistory()

// 监听路由变化同步关键词
watch(
  () => route.query.keyword,
  (newKeyword) => {
    keyword.value = (newKeyword as string) || ''
  }
)
</script>

<template>
  <div class="search-filter-bar" role="search" aria-label="课程搜索和筛选">
    <div class="search-section">
      <!-- 搜索框 -->
      <div class="search-input-wrapper">
        <el-input
          v-model="keyword"
          placeholder="搜索课程、讲师"
          size="large"
          clearable
          aria-label="搜索课程或讲师"
          @input="handleSearch"
          @clear="clearSearch"
        >
          <template #prefix>
            <el-icon aria-hidden="true"><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 搜索历史 -->
      <div v-if="searchHistory.length > 0 && !keyword" class="search-history">
        <div class="history-header">
          <span class="label" id="history-label">搜索历史</span>
          <el-button
            type="primary"
            text
            size="small"
            aria-label="清除所有搜索历史"
            @click="clearHistory"
          >
            清除
          </el-button>
        </div>
        <div class="history-tags" role="list" aria-labelledby="history-label">
          <el-tag
            v-for="item in searchHistory"
            :key="item"
            type="info"
            effect="plain"
            class="history-tag"
            role="listitem"
            tabindex="0"
            :aria-label="`搜索：${item}`"
            @click="handleHistoryClick(item)"
            @keyup.enter="handleHistoryClick(item)"
          >
            {{ item }}
          </el-tag>
        </div>
      </div>

      <!-- 热门搜索 -->
      <div v-if="!keyword" class="hot-keywords">
        <span class="label" id="hot-label">热门搜索：</span>
        <div class="hot-tags" role="list" aria-labelledby="hot-label">
          <el-tag
            v-for="item in hotKeywords"
            :key="item"
            type="warning"
            effect="plain"
            class="hot-tag"
            role="listitem"
            tabindex="0"
            :aria-label="`搜索热门词：${item}`"
            @click="handleHotClick(item)"
            @keyup.enter="handleHotClick(item)"
          >
            {{ item }}
          </el-tag>
        </div>
      </div>
    </div>

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

.search-section {
  margin-bottom: 20px;
}

.search-input-wrapper {
  max-width: 600px;
  margin: 0 auto 16px;
}

.search-history {
  margin-bottom: 16px;

  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
}

.hot-keywords {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.label {
  font-size: 13px;
  color: #666;
}

.history-tags,
.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-tag,
.hot-tag {
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: scale(1.05);
  }

  &:focus-visible {
    outline: 2px solid #1890ff;
    outline-offset: 2px;
  }
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