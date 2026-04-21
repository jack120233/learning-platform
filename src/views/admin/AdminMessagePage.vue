<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { sendAdminMessage, type AdminMessageFormData } from '@/api/admin'

const formRef = ref()
const isSubmitting = ref(false)
const formData = ref<AdminMessageFormData>({
  user_id: 0,
  type: 'system',
  title: '',
  content: '',
  link: '',
})

const rules = {
  user_id: [
    { required: true, message: '请输入接收用户 ID', trigger: 'blur' },
  ],
  title: [
    { required: true, message: '请输入消息标题', trigger: 'blur' },
  ],
  content: [
    { required: true, message: '请输入消息内容', trigger: 'blur' },
  ],
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  isSubmitting.value = true
  try {
    await sendAdminMessage({
      user_id: Number(formData.value.user_id),
      type: formData.value.type,
      title: formData.value.title,
      content: formData.value.content,
      link: formData.value.link || undefined,
    })
    ElMessage.success('系统消息发送成功')
    formData.value = {
      user_id: 0,
      type: 'system',
      title: '',
      content: '',
      link: '',
    }
    formRef.value?.clearValidate()
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="admin-message-page">
    <div class="page-header">
      <h2 class="page-title">系统消息</h2>
      <p class="page-desc">向指定用户发送系统消息或站内通知。</p>
    </div>

    <el-card shadow="never" class="message-card">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="96px">
        <el-form-item label="接收用户 ID" prop="user_id">
          <el-input-number v-model="formData.user_id" :min="1" :precision="0" style="width: 220px" />
        </el-form-item>
        <el-form-item label="消息类型">
          <el-select v-model="formData.type" style="width: 220px">
            <el-option label="系统消息" value="system" />
            <el-option label="通知" value="notification" />
            <el-option label="公告" value="announcement" />
            <el-option label="课程消息" value="course" />
            <el-option label="互动消息" value="interaction" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息标题" prop="title">
          <el-input v-model="formData.title" maxlength="200" show-word-limit placeholder="请输入消息标题" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="formData.link" maxlength="500" show-word-limit placeholder="可选，填写站内跳转链接" />
        </el-form-item>
        <el-form-item label="消息内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="8"
            maxlength="1000"
            show-word-limit
            placeholder="请输入消息内容"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">
            发送消息
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.admin-message-page {
  .page-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid $border-color-light;
  }

  .page-title {
    margin: 0 0 8px;
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
  }

  .page-desc {
    margin: 0;
    color: $text-secondary;
    line-height: 1.6;
  }
}

.message-card {
  max-width: 720px;
}
</style>
