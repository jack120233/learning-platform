<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { useCountdown } from '@/composables/useCountdown'
import { fetchProfile, updateProfile, sendEmailCode, uploadAvatar } from '@/api/profile'
import type { UserProfile, UpdateProfileRequest } from '@/api/profile'

const userStore = useUserStore()
const { countdown, isActive: isCountdownActive, start: startCountdown } = useCountdown(60)

// 状态
const profile = ref<UserProfile | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)
const isUploading = ref(false)

// 表单数据
const form = ref<UpdateProfileRequest>({
  nickname: '',
  email: '',
  phone: '',
  email_code: '',
})

// 原始邮箱（用于检测邮箱是否变化）
const originalEmail = ref('')

// 邮箱是否被修改
const emailChanged = computed(() => {
  return form.value.email !== originalEmail.value
})

// 表单引用
const formRef = ref()

// 表单校验规则
const rules = {
  nickname: [
    { max: 20, message: '昵称最长 20 个字符', trigger: 'blur' },
    { pattern: /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/, message: '昵称只能包含中文、英文、数字和下划线', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  email_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为 6 位数字', trigger: 'blur' },
  ],
}

// 角色映射
const roleMap: Record<string, string> = {
  student: '学生',
  teacher: '讲师',
  admin: '管理员',
}

// 状态映射
const statusMap: Record<string, { text: string; type: 'success' | 'warning' | 'danger' }> = {
  active: { text: '正常', type: 'success' },
  disabled: { text: '已禁用', type: 'danger' },
  pending: { text: '待审核', type: 'warning' },
}

// 加载个人信息
async function loadProfile() {
  isLoading.value = true
  try {
    profile.value = await fetchProfile()
    // 填充表单
    form.value.nickname = profile.value.nickname || profile.value.username
    form.value.email = profile.value.email
    form.value.phone = profile.value.phone || ''
    originalEmail.value = profile.value.email
  } catch (error) {
    ElMessage.error('加载个人信息失败')
  } finally {
    isLoading.value = false
  }
}

// 发送验证码
async function handleSendCode() {
  if (!form.value.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }

  // 简单的邮箱格式校验
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(form.value.email)) {
    ElMessage.warning('请输入正确的邮箱格式')
    return
  }

  try {
    await sendEmailCode({
      email: form.value.email,
      purpose: 'change_email',
    })
    ElMessage.success('验证码已发送')
    startCountdown()
  } catch (error) {
    // 错误已由拦截器处理
  }
}

// 上传头像
async function handleUploadAvatar(options: { file: File }) {
  const { file } = options

  // 校验文件类型
  const validTypes = ['image/jpeg', 'image/png', 'image/gif']
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('仅支持 JPG/PNG/GIF 格式')
    return
  }

  // 校验文件大小（最大 10MB）
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片最大 10MB')
    return
  }

  isUploading.value = true
  try {
    const result = await uploadAvatar(file)
    // 更新头像
    await updateProfile({ avatar: result.file_url })
    // 更新本地状态
    if (profile.value) {
      profile.value.avatar = result.file_url
    }
    // 更新 userStore
    userStore.setUserInfo({ avatarUrl: result.file_url })
    ElMessage.success('头像更新成功')
  } catch (error) {
    // 错误已由拦截器处理
  } finally {
    isUploading.value = false
  }
}

// 保存修改
async function handleSave() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  // 检查邮箱是否修改且未输入验证码
  if (emailChanged.value && !form.value.email_code) {
    ElMessage.warning('修改邮箱需要验证码')
    return
  }

  isSaving.value = true
  try {
    const data: UpdateProfileRequest = {
      nickname: form.value.nickname,
      phone: form.value.phone || undefined,
      avatar: profile.value?.avatar,
    }

    // 如果邮箱修改了，需要带上验证码
    if (emailChanged.value) {
      data.email = form.value.email
      data.email_code = form.value.email_code
    }

    const result = await updateProfile(data)

    // 更新本地状态
    profile.value = result
    originalEmail.value = result.email

    // 更新 userStore
    userStore.setUserInfo({
      nickname: result.nickname,
      email: result.email,
      avatarUrl: result.avatar,
    })

    // 清空验证码
    form.value.email_code = ''

    ElMessage.success('保存成功')
  } catch (error) {
    // 错误已由拦截器处理
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <div class="profile-info-page" v-loading="isLoading">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">个人信息</h2>
    </div>

    <template v-if="profile">
      <!-- 头像区域 -->
      <div class="avatar-section">
        <el-avatar :src="profile.avatar" :size="80" class="avatar">
          <el-icon :size="40"><User /></el-icon>
        </el-avatar>
        <el-upload
          :show-file-list="false"
          :http-request="handleUploadAvatar"
          accept=".jpg,.jpeg,.png,.gif"
        >
          <el-button type="primary" plain :loading="isUploading">
            <el-icon><Upload /></el-icon>
            更换头像
          </el-button>
        </el-upload>
      </div>

      <!-- 只读信息展示 -->
      <div class="info-section">
        <div class="info-row">
          <span class="info-label">用户名</span>
          <span class="info-value">{{ profile.username }}</span>
        </div>

        <div class="info-row">
          <span class="info-label">角色</span>
          <el-tag>{{ roleMap[profile.role] || profile.role }}</el-tag>
        </div>

        <div class="info-row" v-if="profile.role === 'teacher' && profile.status === 'pending'">
          <span class="info-label">审核状态</span>
          <el-tag :type="statusMap[profile.status]?.type">
            {{ statusMap[profile.status]?.text }}
          </el-tag>
        </div>

        <div class="info-row">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ profile.created_at }}</span>
        </div>
      </div>

      <!-- 可编辑表单 -->
      <el-divider>编辑信息</el-divider>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="edit-form"
      >
        <el-form-item label="昵称" prop="nickname">
          <el-input
            v-model="form.nickname"
            placeholder="请输入昵称"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <div class="email-input-group">
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱"
              style="flex: 1"
            />
            <el-button
              v-if="emailChanged"
              type="primary"
              plain
              :disabled="isCountdownActive"
              @click="handleSendCode"
            >
              {{ isCountdownActive ? `${countdown}s` : '发送验证码' }}
            </el-button>
          </div>
          <div class="form-tip" v-if="emailChanged">
            邮箱已修改，需要验证新邮箱
          </div>
        </el-form-item>

        <el-form-item
          v-if="emailChanged"
          label="验证码"
          prop="email_code"
        >
          <el-input
            v-model="form.email_code"
            placeholder="请输入 6 位验证码"
            maxlength="6"
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            maxlength="11"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="isSaving" @click="handleSave">
            保存修改
          </el-button>
        </el-form-item>
      </el-form>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.profile-info-page {
  .page-header {
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
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
  padding: 24px;
  background: #fafafa;
  border-radius: 8px;
}

.avatar {
  background: #e6f7ff;
}

.info-section {
  margin-bottom: 24px;
}

.info-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }
}

.info-label {
  width: 100px;
  color: #666;
  flex-shrink: 0;
}

.info-value {
  color: #333;
}

.edit-form {
  max-width: 500px;
}

.email-input-group {
  display: flex;
  gap: 12px;
  width: 100%;
}

.form-tip {
  font-size: 12px;
  color: #faad14;
  margin-top: 4px;
}
</style>