<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchAdminApplications,
  reviewAdminApplication,
  type AdminApplicationItem,
} from '@/api/admin'

const statusFilter = ref<'all' | 'pending' | 'approved' | 'rejected'>('pending')

async function fetchApplicationList(params: { page?: number; page_size?: number }) {
  return fetchAdminApplications({
    status: statusFilter.value,
    ...params,
  })
}

const {
  items: applications,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  fetchData,
  goToPage,
} = usePagination<AdminApplicationItem, { page?: number; page_size?: number }>(fetchApplicationList, 10)

const statusMap: Record<string, { text: string; type: 'warning' | 'success' | 'danger' }> = {
  pending: { text: '待审核', type: 'warning' },
  approved: { text: '已通过', type: 'success' },
  rejected: { text: '已驳回', type: 'danger' },
}

const detailDrawer = ref(false)
const currentApplication = ref<AdminApplicationItem | null>(null)
const showDialog = ref(false)
const reviewForm = ref({
  approve: true,
  comment: '',
})
const isSubmitting = ref(false)

function formatTime(value: string | null | undefined) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function openDetail(item: AdminApplicationItem) {
  currentApplication.value = item
  detailDrawer.value = true
}

function openReviewDialog(item: AdminApplicationItem, approve: boolean) {
  currentApplication.value = item
  reviewForm.value = {
    approve,
    comment: approve ? '' : item.review_comment || '',
  }
  showDialog.value = true
}

async function submitReview() {
  if (!currentApplication.value) return

  if (!reviewForm.value.approve && !reviewForm.value.comment.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }

  isSubmitting.value = true
  try {
    await reviewAdminApplication(currentApplication.value.application_id, {
      approve: reviewForm.value.approve,
      comment: reviewForm.value.comment.trim() || undefined,
    })
    ElMessage.success(reviewForm.value.approve ? '审核已通过' : '已驳回申请')
    showDialog.value = false
    await fetchData()
  } finally {
    isSubmitting.value = false
  }
}

function handleStatusChange() {
  fetchData(true)
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="admin-application-page">
    <div class="page-header">
      <h2 class="page-title">管理员申请</h2>
    </div>

    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="审核状态" style="width: 140px" @change="handleStatusChange">
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已驳回" value="rejected" />
        <el-option label="全部状态" value="all" />
      </el-select>
    </div>

    <el-table :data="applications" v-loading="isLoading" stripe border>
      <el-table-column prop="username" label="申请人" min-width="140" />
      <el-table-column prop="department" label="所属部门" min-width="140" />
      <el-table-column prop="reason" label="申请理由" min-width="260" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
            {{ statusMap[row.status]?.text || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="申请时间" width="170" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="审核时间" width="170" align="center">
        <template #default="{ row }">
          {{ formatTime(row.reviewed_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" :icon="Search" @click="openDetail(row)">
            详情
          </el-button>
          <template v-if="row.status === 'pending'">
            <el-button text size="small" type="success" @click="openReviewDialog(row, true)">
              通过
            </el-button>
            <el-button text size="small" type="danger" @click="openReviewDialog(row, false)">
              驳回
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="totalPages > 1"
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next, jumper"
      class="pagination"
      @current-change="goToPage"
    />

    <el-drawer v-model="detailDrawer" title="管理员申请详情" size="460px">
      <template v-if="currentApplication">
        <div class="detail-section">
          <div class="detail-row"><span class="detail-label">申请人</span><span class="detail-value">{{ currentApplication.username }}</span></div>
          <div class="detail-row"><span class="detail-label">所属部门</span><span class="detail-value">{{ currentApplication.department || '-' }}</span></div>
          <div class="detail-row detail-row--column">
            <span class="detail-label">申请理由</span>
            <p class="detail-text">{{ currentApplication.reason }}</p>
          </div>
          <div class="detail-row"><span class="detail-label">审核意见</span><span class="detail-value">{{ currentApplication.review_comment || '-' }}</span></div>
          <div class="detail-row"><span class="detail-label">申请时间</span><span class="detail-value">{{ formatTime(currentApplication.created_at) }}</span></div>
          <div class="detail-row"><span class="detail-label">审核时间</span><span class="detail-value">{{ formatTime(currentApplication.reviewed_at) }}</span></div>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="showDialog" :title="reviewForm.approve ? '通过申请' : '驳回申请'" width="520px">
      <el-form label-width="90px">
        <el-form-item label="申请人">
          <span>{{ currentApplication?.username }}</span>
        </el-form-item>
        <el-form-item :label="reviewForm.approve ? '审核备注' : '驳回原因'">
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="4"
            :placeholder="reviewForm.approve ? '可选填写审核备注' : '请填写驳回原因'"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="submitReview">
          确认提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.admin-application-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid $border-color-light;
  }

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
  }
}

.filter-bar {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;

  &--column {
    flex-direction: column;
  }
}

.detail-label {
  flex-shrink: 0;
  color: $text-secondary;
}

.detail-value {
  color: $text-primary;
  text-align: right;
  word-break: break-word;
}

.detail-text {
  margin: 0;
  color: $text-primary;
  line-height: 1.7;
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .detail-row {
    flex-direction: column;
    gap: 8px;
  }

  .detail-value {
    text-align: left;
  }
}
</style>
