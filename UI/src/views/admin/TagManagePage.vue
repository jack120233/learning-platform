<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import {
  batchDeleteAdminTags,
  createAdminTag,
  deleteAdminTag,
  fetchAdminTags,
  type AdminTagBatchDeleteResult,
  type AdminTagFormData,
  type AdminTagItem,
  type AdminTagsParams,
} from '@/api/admin'

const keyword = ref('')
const showDialog = ref(false)
const isSaving = ref(false)
const formRef = ref()
const selectedRows = ref<AdminTagItem[]>([])
const formData = ref<AdminTagFormData>({
  name: '',
  slug: '',
  color: '#409EFF',
})

const rules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
  ],
  slug: [
    { required: true, message: '请输入标签标识', trigger: 'blur' },
  ],
}

async function fetchTagList(params: AdminTagsParams) {
  return fetchAdminTags({
    keyword: keyword.value || undefined,
    ...params,
  })
}

const {
  items: tags,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  fetchData,
  goToPage,
} = usePagination<AdminTagItem, AdminTagsParams>(fetchTagList, 10)

const selectedCount = computed(() => selectedRows.value.length)

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

function handleSelectionChange(selection: AdminTagItem[]) {
  selectedRows.value = selection
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function handleReset() {
  keyword.value = ''
  selectedRows.value = []
  page.value = 1
  fetchData()
}

function openCreateDialog() {
  formData.value = {
    name: '',
    slug: '',
    color: '#409EFF',
  }
  showDialog.value = true
}

async function submitForm() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  isSaving.value = true
  try {
    await createAdminTag({
      name: formData.value.name,
      slug: formData.value.slug,
      color: formData.value.color || undefined,
    })
    ElMessage.success('标签创建成功')
    showDialog.value = false
    await reloadTable(true)
  } finally {
    isSaving.value = false
  }
}

function formatBatchDeleteMessage(result: AdminTagBatchDeleteResult) {
  const parts = [`批量删除完成，成功 ${result.success_count} 个`]
  if (result.failed_count > 0) {
    const failedText = result.failed_items
      .map(item => `标签ID ${item.tag_id}：${item.reason}`)
      .join('；')
    parts.push(`失败 ${result.failed_count} 个`)
    parts.push(failedText)
  }
  return parts.join('，')
}

async function reloadTable(resetPage = false) {
  selectedRows.value = []
  await fetchData(resetPage)
}

async function handleDelete(tag: AdminTagItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除标签「${tag.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    )

    await deleteAdminTag(tag.tag_id)
    ElMessage.success('标签已删除')
    await reloadTable(tags.value.length === 1 && page.value > 1)
  } catch (error) {
    // 用户取消
  }
}

async function handleBatchDelete() {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择标签')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要批量删除已选择的 ${selectedRows.value.length} 个标签吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    )

    const result = await batchDeleteAdminTags(selectedRows.value.map(item => item.tag_id))
    if (result.failed_count > 0) {
      ElMessage.warning(formatBatchDeleteMessage(result))
    } else {
      ElMessage.success(`批量删除成功，共删除 ${result.success_count} 个标签`)
    }
    await reloadTable(tags.value.length === selectedRows.value.length && page.value > 1)
  } catch (error) {
    // 用户取消
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="tag-manage-page">
    <div class="page-header">
      <h2 class="page-title">标签管理</h2>
      <div class="header-actions soft-action-surface">
        <el-button class="soft-action-btn soft-action-btn--primary" type="primary" :icon="Plus" @click="openCreateDialog">
          新增标签
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索标签名称或标识"
        clearable
        style="width: 240px"
        @keyup.enter="handleSearch"
      />
      <div class="filter-actions soft-action-surface">
        <el-button class="soft-action-btn soft-action-btn--primary soft-action-btn--small" @click="handleSearch">搜索</el-button>
        <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" @click="handleReset">重置</el-button>
      </div>
    </div>

    <div v-if="selectedCount > 0" class="batch-actions soft-action-surface--card">
      <span class="selected-count">已选择 {{ selectedCount }} 个标签</span>
      <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" type="danger" size="small" :icon="Delete" @click="handleBatchDelete">
        批量删除
      </el-button>
    </div>

    <el-table
      :data="tags"
      v-loading="isLoading"
      stripe
      border
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="50" />
      <el-table-column prop="name" label="标签名称" min-width="140" />
      <el-table-column prop="slug" label="标识" min-width="140" />
      <el-table-column label="颜色" width="100" align="center">
        <template #default="{ row }">
          <span class="tag-color" :style="{ backgroundColor: row.color || '#dcdfe6' }"></span>
        </template>
      </el-table-column>
      <el-table-column prop="use_count" label="使用次数" width="100" align="center" />
      <el-table-column label="创建时间" width="170" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" type="danger" :icon="Delete" @click="handleDelete(row)">
            删除
          </el-button>
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

    <el-dialog v-model="showDialog" title="新增标签" width="520px">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="90px">
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入标签名称" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="标签标识" prop="slug">
          <el-input v-model="formData.slug" placeholder="请输入标签 slug" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="formData.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-action-surface soft-action-surface">
          <el-button class="soft-action-btn soft-action-btn--secondary" @click="showDialog = false">取消</el-button>
          <el-button class="soft-action-btn soft-action-btn--primary" type="primary" :loading="isSaving" @click="submitForm">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.tag-manage-page {
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
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.header-actions,
.filter-actions,
.dialog-action-surface {
  width: fit-content;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: $radius-sm;

  .selected-count {
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.tag-color {
  display: inline-block;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid $border-color;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .tag-manage-page .page-header {
    align-items: stretch;
    flex-direction: column;
    gap: 12px;
  }

  .header-actions,
  .filter-actions,
  .dialog-action-surface {
    width: 100%;
  }

  .batch-actions {
    flex-wrap: wrap;
  }
}
</style>
