<script setup lang="ts">
import { onMounted } from 'vue'
import { usePagination } from '@/composables/usePagination'
import { fetchMyFeedbacks } from '@/api/profile'
import type { FeedbackItem } from '@/api/profile'

const {
  items: feedbacks,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  isEmpty,
  fetchData,
  goToPage,
} = usePagination<FeedbackItem>(fetchMyFeedbacks, 10)

// 反馈类型映射
const typeMap: Record<string, { text: string; type: 'primary' | 'success' }> = {
  system: { text: '系统问题', type: 'primary' },
  course: { text: '课程问题', type: 'success' },
}

// 状态映射
const statusMap: Record<string, { text: string; type: 'warning' | 'success' }> = {
  pending: { text: '处理中', type: 'warning' },
  processed: { text: '已处理', type: 'success' },
}

// 格式化时间
function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 初始化加载
onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="my-feedbacks-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">我的反馈</h2>
      <span class="total-count">共 {{ total }} 条反馈</span>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="isEmpty" description="暂无反馈记录">
      <template #image>
        <el-icon :size="64" color="#ccc"><ChatDotRound /></el-icon>
      </template>
    </el-empty>

    <!-- 反馈列表 -->
    <template v-else>
      <div class="feedback-list" v-loading="isLoading">
        <div
          v-for="feedback in feedbacks"
          :key="feedback.feedback_id"
          class="feedback-card"
        >
          <!-- 卡片头部 -->
          <div class="card-header">
            <div class="header-tags">
              <el-tag :type="typeMap[feedback.feedback_type]?.type || 'info'" size="small">
                {{ typeMap[feedback.feedback_type]?.text || feedback.feedback_type }}
              </el-tag>
              <el-tag
                :type="statusMap[feedback.status]?.type || 'info'"
                size="small"
              >
                {{ statusMap[feedback.status]?.text || feedback.status }}
              </el-tag>
            </div>
            <span class="feedback-time">{{ formatTime(feedback.created_at) }}</span>
          </div>

          <!-- 反馈内容 -->
          <p class="feedback-content">
            {{ feedback.content }}
          </p>

          <!-- 关联课程 -->
          <p class="feedback-course" v-if="feedback.course_title">
            <el-icon><Link /></el-icon>
            关联课程：{{ feedback.course_title }}
          </p>

          <!-- 图片列表 -->
          <div class="feedback-images" v-if="feedback.images?.length">
            <el-image
              v-for="(img, index) in feedback.images.slice(0, 4)"
              :key="index"
              :src="img"
              :preview-src-list="feedback.images"
              :initial-index="index"
              fit="cover"
              class="feedback-image"
              lazy
            >
              <template #error>
                <div class="image-placeholder">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div
              v-if="feedback.images.length > 4"
              class="more-images"
            >
              +{{ feedback.images.length - 4 }}
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="totalPages > 1"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper"
        class="pagination"
        @current-change="goToPage"
      />
    </template>
  </div>
</template>

<style lang="scss" scoped>
.my-feedbacks-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }

  .total-count {
    font-size: 14px;
    color: #666;
  }
}

.feedback-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feedback-card {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.2s ease;

  &:hover {
    background: #f0f7ff;
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.header-tags {
  display: flex;
  gap: 8px;
}

.feedback-time {
  font-size: 12px;
  color: #999;
}

.feedback-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feedback-course {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.feedback-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.feedback-image {
  width: 80px;
  height: 80px;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #ccc;
}

.more-images {
  width: 80px;
  height: 80px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>