<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Search } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  type AnnouncementItem,
  type AnnouncementFormData,
  type AnnouncementsParams,
} from '@/api/admin'

// 筛选状态
const statusFilter = ref<'all' | 'draft' | 'published'>('all')
const keyword = ref('')

// 获取公告列表
async function fetchAnnouncementList(params: AnnouncementsParams) {
  return fetchAnnouncements({
    status: statusFilter.value === 'all' ? undefined : statusFilter.value,
    keyword: keyword.value || undefined,
    ...params,
  })
}

const {
  items: announcements,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  fetchData,
  goToPage,
} = usePagination<AnnouncementItem, AnnouncementsParams>(fetchAnnouncementList, 10)

// 状态映射
const statusMap: Record<string, { text: string; type: 'info' | 'success' }> = {
  draft: { text: '草稿', type: 'info' },
  published: { text: '已发布', type: 'success' },
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

// 公告弹窗
const showDialog = ref(false)
const isEdit = ref(false)
const currentAnnouncement = ref<AnnouncementItem | null>(null)
const formData = ref<AnnouncementFormData>({
  title: '',
  content: '',
  status: 'draft',
})
const isSaving = ref(false)
const formRef = ref()

// 表单校验规则
const rules = {
  title: [
    { required: true, message: '请输入公告标题', trigger: 'blur' },
    { max: 100, message: '标题最多 100 个字符', trigger: 'blur' },
  ],
  content: [
    { required: true, message: '请输入公告内容', trigger: 'blur' },
  ],
}

// 新增公告
function handleCreate() {
  isEdit.value = false
  currentAnnouncement.value = null
  formData.value = {
    title: '',
    content: '',
    status: 'draft',
  }
  showDialog.value = true
}

// 编辑公告
function handleEdit(announcement: AnnouncementItem) {
  isEdit.value = true
  currentAnnouncement.value = announcement
  formData.value = {
    title: announcement.title,
    content: announcement.content,
    status: announcement.status,
  }
  showDialog.value = true
}

// 提交表单
async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  isSaving.value = true
  try {
    if (isEdit.value && currentAnnouncement.value) {
      await updateAnnouncement(currentAnnouncement.value.announcement_id, formData.value)
      ElMessage.success('公告更新成功')
    } else {
      await createAnnouncement(formData.value)
      ElMessage.success('公告创建成功')
    }
    showDialog.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 发布公告
async function handlePublish(announcement: AnnouncementItem) {
  try {
    await updateAnnouncement(announcement.announcement_id, {
      ...announcement,
      status: 'published',
    })
    ElMessage.success('公告已发布')
    fetchData()
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

// 转为草稿
async function handleToDraft(announcement: AnnouncementItem) {
  try {
    await updateAnnouncement(announcement.announcement_id, {
      ...announcement,
      status: 'draft',
    })
    ElMessage.success('已转为草稿')
    fetchData()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 删除公告
async function handleDelete(announcement: AnnouncementItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除公告「${announcement.title}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteAnnouncement(announcement.announcement_id)
    ElMessage.success('公告已删除')
    fetchData()
  } catch (error) {
    // 用户取消
  }
}

// 搜索
function handleSearch() {
  page.value = 1
  fetchData()
}

// 重置筛选
function handleReset() {
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
  <div class="announcement-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">公告管理</h2>
      <div class="header-actions soft-action-surface">
        <el-button class="soft-action-btn soft-action-btn--primary" type="primary" :icon="Plus" @click="handleCreate">
          新增公告
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="状态" style="width: 120px" @change="fetchData">
        <el-option label="全部状态" value="all" />
        <el-option label="草稿" value="draft" />
        <el-option label="已发布" value="published" />
      </el-select>
      <div class="search-area">
        <el-input
          v-model="keyword"
          placeholder="搜索公告标题"
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

    <!-- 公告表格 -->
    <el-table class="announcement-table" :data="announcements" v-loading="isLoading" stripe border>
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
            {{ statusMap[row.status]?.text || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发布时间" width="120" align="center">
        <template #default="{ row }">
          {{ formatTime(row.published_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="creator_name" label="创建人" width="100" align="center" />
      <el-table-column label="操作" width="280" fixed="right" align="center">
        <template #default="{ row }">
          <div class="announcement-row-actions soft-action-surface">
            <el-button
              class="announcement-action-btn soft-action-btn soft-action-btn--secondary soft-action-btn--small"
              size="small"
              :icon="Edit"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              class="announcement-action-btn soft-action-btn soft-action-btn--primary soft-action-btn--small"
              size="small"
              type="primary"
              @click="handlePublish(row)"
            >
              发布
            </el-button>
            <el-button
              v-if="row.status === 'published'"
              class="announcement-action-btn announcement-action-btn--warning soft-action-btn soft-action-btn--small"
              size="small"
              @click="handleToDraft(row)"
            >
              转草稿
            </el-button>
            <el-button
              class="announcement-action-btn soft-action-btn soft-action-btn--danger soft-action-btn--small"
              size="small"
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </div>
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

    <!-- 公告表单弹窗 -->
    <el-dialog
      v-model="showDialog"
      :title="isEdit ? '编辑公告' : '新增公告'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="formData.title"
            placeholder="请输入公告标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="6"
            placeholder="请输入公告内容"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="formData.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="published">发布</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-action-surface soft-action-surface">
          <el-button class="soft-action-btn soft-action-btn--secondary" @click="showDialog = false">取消</el-button>
          <el-button class="soft-action-btn soft-action-btn--primary" type="primary" :loading="isSaving" @click="handleSubmit">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>

.announcement-page {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
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

  .search-area {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.header-actions,
.filter-actions,
.dialog-action-surface {
  width: fit-content;
}

.announcement-table {
  border-radius: 14px;
  overflow: hidden;
}

.announcement-row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  max-width: 100%;
  padding: 5px;
}

.announcement-action-btn {
  min-width: 54px;
  margin-left: 0;
}

.announcement-action-btn--warning {
  color: #b7791f;
  border-color: #fde68a;
  background: linear-gradient(135deg, #fffbeb 0%, #fff7ed 100%);

  &:hover,
  &:focus {
    color: #92400e;
    border-color: #fbbf24;
    background: #fef3c7;
  }
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .announcement-page .page-header,
  .filter-bar,
  .filter-bar .search-area {
    align-items: stretch;
    flex-direction: column;
  }

  .header-actions,
  .filter-actions,
  .dialog-action-surface {
    width: 100%;
  }

  .announcement-row-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }

  .announcement-action-btn {
    width: 100%;
    min-width: 0;
  }
}
</style>