<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchPermissionTree,
  fetchRolePermissions,
  updateRolePermissions,
  type PermissionItem,
} from '@/api/admin'

// 角色列表
const roles = [
  { name: '学生', value: 'student' as const },
  { name: '讲师', value: 'teacher' as const },
  { name: '管理员', value: 'admin' as const },
]

// 当前选中的角色
const activeRole = ref<'student' | 'teacher' | 'admin'>('student')

// 权限树数据
const permissionTree = ref<PermissionItem[]>([])

// 当前角色权限
const checkedPermissions = ref<number[]>([])

// 加载状态
const isLoading = ref(false)
const isSaving = ref(false)

// 树引用
const treeRef = ref()

// 加载权限树
async function loadPermissionTree() {
  try {
    const result = await fetchPermissionTree()
    permissionTree.value = result
  } catch (error) {
    ElMessage.error('加载权限树失败')
  }
}

// 加载角色权限
async function loadRolePermissions() {
  isLoading.value = true
  try {
    const result = await fetchRolePermissions(activeRole.value)
    checkedPermissions.value = result
    // 设置树的选中状态
    treeRef.value?.setCheckedKeys(result)
  } catch (error) {
    ElMessage.error('加载角色权限失败')
  } finally {
    isLoading.value = false
  }
}

// 保存权限配置
async function handleSave() {
  isSaving.value = true
  try {
    const checkedKeys = treeRef.value?.getCheckedKeys() || []
    await updateRolePermissions(activeRole.value, checkedKeys)
    ElMessage.success('权限配置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 监听角色切换
watch(activeRole, () => {
  loadRolePermissions()
})

// 初始化
onMounted(async () => {
  await loadPermissionTree()
  await loadRolePermissions()
})
</script>

<template>
  <div class="role-permission-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">角色权限管理</h2>
    </div>

    <!-- 角色选择 -->
    <el-tabs v-model="activeRole" class="role-tabs">
      <el-tab-pane
        v-for="role in roles"
        :key="role.value"
        :label="role.name"
        :name="role.value"
      />
    </el-tabs>

    <!-- 权限树 -->
    <div class="permission-tree-container" v-loading="isLoading">
      <el-tree
        ref="treeRef"
        :data="permissionTree"
        :props="{
          label: 'name',
          children: 'children',
        }"
        show-checkbox
        node-key="permission_id"
        :default-checked-keys="checkedPermissions"
        :default-expand-all="true"
        class="permission-tree"
      >
        <template #default="{ data }">
          <span class="tree-node">
            <span class="node-label">{{ data.name }}</span>
            <span class="node-desc">{{ data.description }}</span>
          </span>
        </template>
      </el-tree>
    </div>

    <!-- 操作按钮 -->
    <div class="action-bar">
      <el-button type="primary" :loading="isSaving" @click="handleSave">
        保存配置
      </el-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>

.role-permission-page {
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

.role-tabs {
  margin-bottom: 24px;
}

.permission-tree-container {
  background: #fff;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: 16px;
  min-height: 400px;
}

.permission-tree {
  .tree-node {
    display: flex;
    align-items: center;
    gap: 12px;

    .node-label {
      font-weight: 500;
      color: $text-primary;
    }

    .node-desc {
      font-size: $font-size-sm;
      color: $text-tertiary;
    }
  }
}

.action-bar {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid $border-color-light;
}
</style>