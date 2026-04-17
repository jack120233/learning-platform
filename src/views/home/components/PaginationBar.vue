<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
const isMobile = ref(false)
const mobileJumpPage = ref(1)

let mediaQuery: MediaQueryList | null = null

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

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / pageSizeModel.value)))
const displayPage = computed(() => Math.min(Math.max(currentPage.value, 1), totalPages.value))

const syncMobileState = () => {
  if (typeof window === 'undefined') return
  isMobile.value = mediaQuery?.matches ?? window.innerWidth <= 768
  mobileJumpPage.value = displayPage.value
}

const handleViewportChange = () => {
  syncMobileState()
}

const handleMobileJump = () => {
  const targetPage = Math.min(Math.max(Number(mobileJumpPage.value) || 1, 1), totalPages.value)
  mobileJumpPage.value = targetPage

  if (targetPage !== currentPage.value) {
    currentPage.value = targetPage
  }
}

onMounted(() => {
  mediaQuery = window.matchMedia('(max-width: 768px)')
  syncMobileState()

  if (typeof mediaQuery.addEventListener === 'function') {
    mediaQuery.addEventListener('change', handleViewportChange)
  } else {
    mediaQuery.addListener(handleViewportChange)
  }
})

onBeforeUnmount(() => {
  if (!mediaQuery) return

  if (typeof mediaQuery.removeEventListener === 'function') {
    mediaQuery.removeEventListener('change', handleViewportChange)
  } else {
    mediaQuery.removeListener(handleViewportChange)
  }
})

watch([displayPage, totalPages], () => {
  mobileJumpPage.value = displayPage.value
}, { immediate: true })
</script>

<template>
  <div
    v-if="total > 0"
    class="pagination-bar"
    :class="{ 'pagination-bar--mobile': isMobile }"
  >
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSizeModel"
      :page-sizes="[10, 20, 40, 60]"
      :total="total"
      :layout="isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper'"
      :pager-count="isMobile ? 5 : 7"
      background
    />

    <template v-if="isMobile">
      <div class="pagination-mobile-meta">
        <span>共 {{ totalPages }} 页</span>
        <span>当前第 {{ displayPage }} 页</span>
      </div>

      <div class="pagination-mobile-jumper">
        <span>前往</span>
        <el-input-number
          v-model="mobileJumpPage"
          :min="1"
          :max="totalPages"
          :step="1"
          :precision="0"
          size="small"
          controls-position="right"
          class="pagination-mobile-input"
        />
        <span>页</span>
        <el-button size="small" type="primary" plain @click="handleMobileJump">
          确定
        </el-button>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.pagination-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.pagination-bar :deep(.el-pagination) {
  justify-content: center;
  flex-wrap: wrap;
}

.pagination-bar--mobile {
  padding: 16px 12px;
  gap: 12px;
}

.pagination-bar--mobile :deep(.el-pagination) {
  width: 100%;
}

.pagination-mobile-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px 16px;
  width: 100%;
  font-size: 13px;
  line-height: 1.5;
  color: #606266;
}

.pagination-mobile-jumper {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
  font-size: 13px;
  color: #606266;
}

.pagination-mobile-input {
  width: 108px;
}

@media (max-width: 768px) {
  .pagination-bar {
    margin-top: 24px;
  }

  .pagination-bar :deep(.el-pager li),
  .pagination-bar :deep(.btn-prev),
  .pagination-bar :deep(.btn-next) {
    min-width: 32px;
  }
}
</style>
