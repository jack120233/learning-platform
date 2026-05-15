<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchTeacherAudits,
  reviewTeacher,
  type TeacherAuditItem,
} from '@/api/admin'

const statusFilter = ref<'all' | 'pending' | 'approved' | 'rejected'>('pending')

async function fetchAuditList(params: { page?: number; page_size?: number }) {
  return fetchTeacherAudits({
    status: statusFilter.value,
    ...params,
  })
}

const {
  items: audits,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  fetchData,
  goToPage,
} = usePagination<TeacherAuditItem, { page?: number; page_size?: number }>(fetchAuditList, 10)

const statusMap: Record<string, { text: string; type: 'warning' | 'success' | 'danger' }> = {
  pending: { text: '待审核', type: 'warning' },
  approved: { text: '已通过', type: 'success' },
  rejected: { text: '已驳回', type: 'danger' },
}

const detailDrawer = ref(false)
const currentAudit = ref<TeacherAuditItem | null>(null)
const showDialog = ref(false)
const auditForm = ref({
  approve: true,
  comment: '',
})
const isSubmitting = ref(false)

const dialogTitle = computed(() => (auditForm.value.approve ? '通过申请' : '驳回申请'))

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

function openDetail(audit: TeacherAuditItem) {
  currentAudit.value = audit
  detailDrawer.value = true
}

function openReviewDialog(audit: TeacherAuditItem, approve: boolean) {
  currentAudit.value = audit
  auditForm.value = {
    approve,
    comment: approve ? '' : audit.review_comment || '',
  }
  showDialog.value = true
}

async function submitReview() {
  if (!currentAudit.value) return

  if (!auditForm.value.approve && !auditForm.value.comment.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }

  isSubmitting.value = true
  try {
    await reviewTeacher(currentAudit.value.audit_id, {
      approve: auditForm.value.approve,
      comment: auditForm.value.comment.trim() || undefined,
    })
    ElMessage.success(auditForm.value.approve ? '审核已通过' : '已驳回申请')
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
  <div class="teacher-audit-page">
    <div class="page-header">
      <h2 class="page-title">老师审核</h2>
    </div>

    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="审核状态" style="width: 140px" @change="handleStatusChange">
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已驳回" value="rejected" />
        <el-option label="全部状态" value="all" />
      </el-select>
    </div>

    <el-table :data="audits" v-loading="isLoading" stripe border>
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="real_name" label="真实姓名" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="联系电话" width="140" />
      <el-table-column prop="organization" label="所属机构" min-width="150" />
      <el-table-column prop="title" label="职称" min-width="120" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.audit_status]?.type || 'info'" size="small">
            {{ statusMap[row.audit_status]?.text || row.audit_status }}
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
          <template v-if="row.audit_status === 'pending'">
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

    <el-drawer v-model="detailDrawer" title="老师申请详情" size="480px">
      <template v-if="currentAudit">
        <div class="detail-section">
          <div class="detail-row"><span class="detail-label">用户名</span><span class="detail-value">{{ currentAudit.username }}</span></div>
          <div class="detail-row"><span class="detail-label">真实姓名</span><span class="detail-value">{{ currentAudit.real_name }}</span></div>
          <div class="detail-row"><span class="detail-label">邮箱</span><span class="detail-value">{{ currentAudit.email }}</span></div>
          <div class="detail-row"><span class="detail-label">联系电话</span><span class="detail-value">{{ currentAudit.phone }}</span></div>
          <div class="detail-row"><span class="detail-label">所属机构</span><span class="detail-value">{{ currentAudit.organization || '-' }}</span></div>
          <div class="detail-row"><span class="detail-label">职称</span><span class="detail-value">{{ currentAudit.title || '-' }}</span></div>
          <div class="detail-row detail-row--column">
            <span class="detail-label">个人简介</span>
            <p class="detail-text">{{ currentAudit.introduction || '暂无简介' }}</p>
          </div>
          <div class="detail-row detail-row--column">
            <span class="detail-label">资质材料</span>
            <div class="certificate-list">
              <template v-if="currentAudit.certificate_urls?.length">
                <a
                  v-for="(url, index) in currentAudit.certificate_urls"
                  :key="url"
                  :href="url"
                  target="_blank"
                  rel="noreferrer"
                  class="certificate-link"
                >
                  资质材料 {{ index + 1 }}
                </a>
              </template>
              <span v-else class="detail-value">暂无材料</span>
            </div>
          </div>
          <div class="detail-row"><span class="detail-label">审核意见</span><span class="detail-value">{{ currentAudit.review_comment || '-' }}</span></div>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="showDialog" :title="dialogTitle" width="520px">
      <el-form label-width="90px">
        <el-form-item label="审核对象">
          <span>{{ currentAudit?.username }} / {{ currentAudit?.real_name }}</span>
        </el-form-item>
        <el-form-item :label="auditForm.approve ? '审核备注' : '驳回原因'">
          <el-input
            v-model="auditForm.comment"
            type="textarea"
            :rows="4"
            :placeholder="auditForm.approve ? '可选填写审核备注' : '请填写驳回原因'"
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
.teacher-audit-page {
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

.certificate-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.certificate-link {
  color: $primary-color;
  text-decoration: none;
}

@media (max-width: 768px) {
  .filter-bar {
    margin-bottom: 16px;
  }

  .detail-row {
    flex-direction: column;
    gap: 8px;
  }

  .detail-value {
    text-align: left;
  }
}
</style>
