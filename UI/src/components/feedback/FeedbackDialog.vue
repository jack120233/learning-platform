<script setup lang="ts">
import FeedbackForm from './FeedbackForm.vue'

// Props
interface Props {
  visible: boolean
}

defineProps<Props>()

// Emits
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

// 关闭弹窗
function handleClose() {
  emit('update:visible', false)
}

// 提交成功
function handleSuccess() {
  handleClose()
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="提交反馈"
    width="560px"
    :close-on-click-modal="false"
    @update:model-value="emit('update:visible', $event)"
  >
    <FeedbackForm
      mode="dialog"
      @success="handleSuccess"
      @cancel="handleClose"
    />
  </el-dialog>
</template>

<style lang="scss" scoped>
:deep(.el-dialog__body) {
  padding: 20px 24px;
}
</style>