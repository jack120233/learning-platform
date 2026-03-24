<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface Props {
  total: number
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  pageSize: 20,
})

const route = useRoute()
const router = useRouter()

// 当前页码
const currentPage = computed({
  get: () => Number(route.query.page) || 1,
  set: (val) => {
    router.push({
      query: { ...route.query, page: val },
    })
    // 滚动到列表顶部
    window.scrollTo({ top: 0, behavior: 'smooth' })
  },
})

// 每页条数
const pageSizeModel = computed({
  get: () => Number(route.query.page_size) || props.pageSize,
  set: (val) => {
    router.push({
      query: { ...route.query, page_size: val, page: 1 },
    })
  },
})
</script>

<template>
  <div class="pagination-bar" v-if="total > 0">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSizeModel"
      :page-sizes="[10, 20, 40, 60]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      background
    />
  </div>
</template>

<style lang="scss" scoped>
.pagination-bar {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
</style>