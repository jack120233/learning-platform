<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import {
  fetchAdminCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  type AdminCategoryItem,
  type AdminCategoryFormData,
} from '@/api/admin'

const isLoading = ref(false)
const categories = ref<AdminCategoryItem[]>([])
const showDialog = ref(false)
const isEdit = ref(false)
const isSaving = ref(false)
const currentCategory = ref<AdminCategoryItem | null>(null)
const formRef = ref()
const formData = ref<AdminCategoryFormData>({
  name: '',
  slug: '',
  description: '',
  icon: '',
  parent_id: null,
  sort_order: 0,
  is_active: true,
})

const parentOptions = computed(() => categories.value.map(item => ({
  label: item.name,
  value: item.category_id,
})))

const rules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
  ],
  slug: [
    { required: true, message: '请输入分类标识', trigger: 'blur' },
  ],
}

async function loadCategories() {
  isLoading.value = true
  try {
    categories.value = await fetchAdminCategories()
  } finally {
    isLoading.value = false
  }
}

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

function getParentName(parentId: number | null) {
  if (!parentId) return '一级分类'
  return categories.value.find(item => item.category_id === parentId)?.name || `分类${parentId}`
}

function openCreateDialog() {
  isEdit.value = false
  currentCategory.value = null
  formData.value = {
    name: '',
    slug: '',
    description: '',
    icon: '',
    parent_id: null,
    sort_order: 0,
    is_active: true,
  }
  showDialog.value = true
}

function openEditDialog(category: AdminCategoryItem) {
  isEdit.value = true
  currentCategory.value = category
  formData.value = {
    name: category.name,
    slug: category.slug,
    description: category.description || '',
    icon: category.icon || '',
    parent_id: category.parent_id,
    sort_order: category.sort_order,
    is_active: category.is_active,
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
    const payload: AdminCategoryFormData = {
      name: formData.value.name,
      slug: formData.value.slug,
      description: formData.value.description || undefined,
      icon: formData.value.icon || undefined,
      parent_id: formData.value.parent_id ?? null,
      sort_order: formData.value.sort_order ?? 0,
      is_active: formData.value.is_active,
    }

    if (isEdit.value && currentCategory.value) {
      await updateCategory(currentCategory.value.category_id, payload)
      ElMessage.success('分类更新成功')
    } else {
      await createCategory(payload)
      ElMessage.success('分类创建成功')
    }

    showDialog.value = false
    await loadCategories()
  } finally {
    isSaving.value = false
  }
}

async function handleDelete(category: AdminCategoryItem) {
  await ElMessageBox.confirm(
    `确定要删除分类「${category.name}」吗？`,
    '删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )

  await deleteCategory(category.category_id)
  ElMessage.success('分类已删除')
  await loadCategories()
}

onMounted(() => {
  loadCategories()
})
</script>

<template>
  <div class="category-manage-page">
    <div class="page-header">
      <h2 class="page-title">分类管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        新增分类
      </el-button>
    </div>

    <el-table :data="categories" v-loading="isLoading" stripe border>
      <el-table-column prop="name" label="分类名称" min-width="160" />
      <el-table-column prop="slug" label="标识" min-width="150" />
      <el-table-column label="父分类" min-width="140">
        <template #default="{ row }">
          {{ getParentName(row.parent_id) }}
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="90" align="center" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" :icon="Edit" @click="openEditDialog(row)">
            编辑
          </el-button>
          <el-button text size="small" type="danger" :icon="Delete" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="isEdit ? '编辑分类' : '新增分类'" width="560px">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="90px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入分类名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="分类标识" prop="slug">
          <el-input v-model="formData.slug" placeholder="请输入分类 slug" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="formData.parent_id" placeholder="请选择父分类，留空表示一级分类" clearable style="width: 100%">
            <el-option
              v-for="option in parentOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formData.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="图标链接">
          <el-input v-model="formData.icon" placeholder="可选，填写分类图标链接" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="分类描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入分类描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="isSaving" @click="submitForm">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.category-manage-page {
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
</style>
