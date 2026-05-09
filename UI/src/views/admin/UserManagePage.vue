<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, View, Delete, Check, Close } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchUsers,
  toggleUserStatus,
  deleteUser,
  fetchTeacherAudits,
  reviewTeacher,
  type AdminUserItem,
  type TeacherAuditItem,
  type AdminUsersParams,
} from '@/api/admin'

// 筛选状态
const roleFilter = ref<'all' | 'student' | 'teacher' | 'admin' | 'pending'>('all')
const statusFilter = ref<'all' | 'active' | 'disabled' | 'pending'>('all')
const keyword = ref('')

// 获取用户列表
async function fetchUserList(params: AdminUsersParams) {
  return fetchUsers({
    role: roleFilter.value === 'all' ? undefined : roleFilter.value,
    status: statusFilter.value === 'all' ? undefined : statusFilter.value,
    keyword: keyword.value || undefined,
    ...params,
  })
}

const {
  items: users,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  fetchData,
  goToPage,
} = usePagination<AdminUserItem, AdminUsersParams>(fetchUserList, 10)

// 角色映射
const roleMap: Record<string, { text: string; type: 'primary' | 'success' | 'warning' }> = {
  student: { text: '学生', type: 'primary' },
  teacher: { text: '讲师', type: 'success' },
  admin: { text: '管理员', type: 'warning' },
}

// 状态映射
const statusMap: Record<string, { text: string; type: 'success' | 'danger' | 'warning' }> = {
  active: { text: '正常', type: 'success' },
  disabled: { text: '禁用', type: 'danger' },
  pending: { text: '待审核', type: 'warning' },
}

// 格式化时间
function formatTime(time: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

// 用户详情抽屉
const showDetailDrawer = ref(false)
const currentUser = ref<AdminUserItem | null>(null)

function handleViewDetail(user: AdminUserItem) {
  currentUser.value = user
  showDetailDrawer.value = true
}

// 禁用/启用用户
async function handleToggleStatus(user: AdminUserItem) {
  const newStatus = user.status === 'active' ? 'disabled' : 'active'
  const actionText = newStatus === 'disabled' ? '禁用' : '启用'

  try {
    await ElMessageBox.confirm(
      `确定要${actionText}用户「${user.username}」吗？`,
      `${actionText}确认`,
      {
        confirmButtonText: `确定${actionText}`,
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await toggleUserStatus(user.user_id, { status: newStatus as 'active' | 'disabled' })
    ElMessage.success(`用户已${actionText}`)
    fetchData()
  } catch (error) {
    // 用户取消
  }
}

// 删除用户
async function handleDelete(user: AdminUserItem) {
  try {
    await ElMessageBox.confirm(
      `删除用户「${user.username}」将级联删除学习记录和反馈，是否确认？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteUser(user.user_id)
    ElMessage.success('用户已删除')
    fetchData()
  } catch (error) {
    // 用户取消
  }
}

// 讲师审核弹窗
const showAuditDialog = ref(false)
const auditItem = ref<TeacherAuditItem | null>(null)
const auditForm = ref({
  approve: true,
  comment: '',
})
const isSubmitting = ref(false)

async function handleAudit(user: AdminUserItem) {
  // 获取审核记录
  try {
    const result = await fetchTeacherAudits({ status: 'pending' })
    const audit = result.items.find(a => a.user_id === user.user_id)
    if (audit) {
      auditItem.value = audit
      auditForm.value = {
        approve: true,
        comment: '',
      }
      showAuditDialog.value = true
    } else {
      ElMessage.warning('未找到审核记录')
    }
  } catch (error) {
    ElMessage.error('获取审核记录失败')
  }
}

async function handleSubmitAudit() {
  if (!auditItem.value) return

  if (!auditForm.value.approve && !auditForm.value.comment.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }

  isSubmitting.value = true
  try {
    await reviewTeacher(auditItem.value!.audit_id, {
      approve: auditForm.value.approve,
      comment: auditForm.value.comment.trim() || undefined,
    })
    ElMessage.success(auditForm.value.approve ? '审核通过' : '已驳回')
    showAuditDialog.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('审核失败')
  } finally {
    isSubmitting.value = false
  }
}

// 搜索
function handleSearch() {
  page.value = 1
  fetchData()
}

// 重置筛选
function handleReset() {
  roleFilter.value = 'all'
  statusFilter.value = 'all'
  keyword.value = ''
  page.value = 1
  fetchData()
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="user-manage-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="roleFilter" placeholder="角色" style="width: 140px" @change="fetchData">
          <el-option label="全部角色" value="all" />
          <el-option label="学生" value="student" />
          <el-option label="讲师" value="teacher" />
          <el-option label="管理员" value="admin" />
          <el-option label="待审核讲师" value="pending" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态" style="width: 120px" @change="fetchData">
          <el-option label="全部状态" value="all" />
          <el-option label="正常" value="active" />
          <el-option label="禁用" value="disabled" />
          <el-option label="待审核" value="pending" />
        </el-select>
      </div>
      <div class="filter-right">
        <el-input
          v-model="keyword"
          placeholder="搜索邮箱/手机号"
          clearable
          style="width: 200px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="filter-actions soft-action-surface">
          <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleSearch">搜索</el-button>
          <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
        </div>
      </div>
    </div>

    <!-- 用户表格 -->
    <el-table :data="users" v-loading="isLoading" stripe border>
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column label="角色" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="roleMap[row.role]?.type || 'info'" size="small">
            {{ roleMap[row.role]?.text || row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
            {{ statusMap[row.status]?.text || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="120" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="最近登录" width="120" align="center">
        <template #default="{ row }">
          {{ formatTime(row.last_login_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" :icon="View" @click="handleViewDetail(row)">
            详情
          </el-button>
          <el-button
            v-if="row.status === 'active'"
            text
            size="small"
            type="warning"
            @click="handleToggleStatus(row)"
          >
            禁用
          </el-button>
          <el-button
            v-if="row.status === 'disabled'"
            text
            size="small"
            type="success"
            @click="handleToggleStatus(row)"
          >
            启用
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            text
            size="small"
            type="primary"
            @click="handleAudit(row)"
          >
            审核
          </el-button>
          <el-button text size="small" type="danger" :icon="Delete" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-if="totalPages > 1"
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next, jumper"
      class="pagination"
      @current-change="goToPage"
    />

    <!-- 用户详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" title="用户详情" size="400px">
      <template v-if="currentUser">
        <div class="detail-section">
          <div class="detail-row">
            <span class="detail-label">用户名</span>
            <span class="detail-value">{{ currentUser.username }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">邮箱</span>
            <span class="detail-value">{{ currentUser.email }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">手机号</span>
            <span class="detail-value">{{ currentUser.phone || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">角色</span>
            <el-tag :type="roleMap[currentUser.role]?.type || 'info'">
              {{ roleMap[currentUser.role]?.text || currentUser.role }}
            </el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态</span>
            <el-tag :type="statusMap[currentUser.status]?.type || 'info'">
              {{ statusMap[currentUser.status]?.text || currentUser.status }}
            </el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">注册时间</span>
            <span class="detail-value">{{ currentUser.created_at }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">最近登录</span>
            <span class="detail-value">{{ currentUser.last_login_at || '-' }}</span>
          </div>
        </div>
      </template>
    </el-drawer>

    <!-- 讲师审核弹窗 -->
    <el-dialog v-model="showAuditDialog" title="讲师审核" width="500px">
      <template v-if="auditItem">
        <div class="audit-info">
          <p><strong>用户名：</strong>{{ auditItem.username }}</p>
          <p><strong>邮箱：</strong>{{ auditItem.email }}</p>
          <p><strong>手机号：</strong>{{ auditItem.phone || '-' }}</p>
        </div>
        <el-divider />
        <el-form label-width="80px">
          <el-form-item label="审核结果">
            <el-radio-group v-model="auditForm.approve">
              <el-radio :value="true">
                <el-icon><Check /></el-icon> 通过
              </el-radio>
              <el-radio :value="false">
                <el-icon><Close /></el-icon> 驳回
              </el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item :label="auditForm.approve ? '审核备注' : '驳回原因'">
            <el-input
              v-model="auditForm.comment"
              type="textarea"
              :rows="3"
              :placeholder="auditForm.approve ? '可选填写审核备注' : '请输入驳回原因（必填）'"
            />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <div class="dialog-action-surface soft-action-surface">
          <el-button class="soft-action-btn soft-action-btn--secondary" @click="showAuditDialog = false">取消</el-button>
          <el-button class="soft-action-btn soft-action-btn--primary" type="primary" :loading="isSubmitting" @click="handleSubmitAudit">
            确认提交
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>

.user-manage-page {
  .page-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid $border-color-light;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;

  .filter-left {
    display: flex;
    gap: 12px;
  }

  .filter-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.filter-actions,
.dialog-action-surface {
  width: fit-content;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.detail-section {
  .detail-row {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid $border-color-light;

    &:last-child {
      border-bottom: none;
    }
  }

  .detail-label {
    width: 80px;
    color: $text-secondary;
    flex-shrink: 0;
  }

  .detail-value {
    color: $text-primary;
  }
}

.audit-info {
  p {
    margin: 8px 0;
    color: $text-primary;
  }
}

@media (max-width: 768px) {
  .filter-bar {
    .filter-left,
    .filter-right {
      width: 100%;
      flex-wrap: wrap;
    }
  }

  .filter-actions,
  .dialog-action-surface {
    width: 100%;
  }
}
</style>