<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import { useCountdown } from '@/composables/useCountdown'
import { fetchProfile, updateProfile, sendEmailCode, uploadAvatar } from '@/api/profile'
import type { UserProfile, UpdateProfileRequest } from '@/api/profile'
import UserIdentity from '@/components/common/UserIdentity.vue'

const userStore = useUserStore()
const { countdown, isActive: isCountdownActive, start: startCountdown } = useCountdown(60)

// 状态
const profile = ref<UserProfile | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)
const isUploading = ref(false)

// 表单数据
const form = ref<UpdateProfileRequest>({
  username: '',
  email: '',
  phone: '',
  email_code: '',
})

// 原始字段（用于检测是否变化）
const originalUsername = ref('')
const originalEmail = ref('')

// 用户名/邮箱是否被修改
const usernameChanged = computed(() => {
  return (form.value.username || '').trim().toLowerCase() !== originalUsername.value
})

const hasUnlimitedUsernameChanges = computed(() => {
  return profile.value?.role === 'teacher' || profile.value?.role === 'admin'
})

const canEditUsername = computed(() => {
  if (!profile.value) return false
  return hasUnlimitedUsernameChanges.value || profile.value.can_change_username
})

const canSubmitUsernameChange = computed(() => {
  return !usernameChanged.value || canEditUsername.value
})

const usernameChangeTip = computed(() => {
  if (!profile.value || hasUnlimitedUsernameChanges.value || !profile.value.can_change_username) return ''
  if (profile.value.username_change_remaining <= 0) return ''
  return `剩余 ${profile.value.username_change_remaining} 次修改机会`
})

const emailChanged = computed(() => {
  return form.value.email !== originalEmail.value
})

// 表单引用
const formRef = ref()

// 表单校验规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度需在 2-50 个字符之间', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9]+$/, message: '用户名只能包含字母和数字', trigger: 'blur' },
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
    form.value.username = profile.value.username
    form.value.email = profile.value.email
    form.value.phone = profile.value.phone || ''
    originalUsername.value = profile.value.username.toLowerCase()
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

  if (usernameChanged.value && !canEditUsername.value) {
    ElMessage.warning('用户名修改机会已用完')
    return
  }

  // 检查邮箱是否修改且未输入验证码
  if (emailChanged.value && !form.value.email_code) {
    ElMessage.warning('修改邮箱需要验证码')
    return
  }

  if (usernameChanged.value) {
    try {
      await ElMessageBox.confirm(
        hasUnlimitedUsernameChanges.value
          ? '用户名修改后将立即生效，请确认新用户名准确无误。'
          : '用户名修改后会消耗一次修改机会，请确认新用户名准确无误。',
        '确认修改用户名',
        {
          confirmButtonText: '确认修改',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
    } catch (error) {
      if (error !== 'cancel' && error !== 'close') {
        ElMessage.error('确认操作失败')
      }
      return
    }
  }

  isSaving.value = true
  try {
    const data: UpdateProfileRequest = {
      phone: form.value.phone || undefined,
      avatar: profile.value?.avatar,
    }

    if (usernameChanged.value) {
      data.username = form.value.username?.trim().toLowerCase()
    }

    // 如果邮箱修改了，需要带上验证码
    if (emailChanged.value) {
      data.email = form.value.email
      data.email_code = form.value.email_code
    }

    const result = await updateProfile(data)

    // 更新本地状态
    profile.value = result
    form.value.username = result.username
    originalUsername.value = result.username.toLowerCase()
    originalEmail.value = result.email

    // 更新 userStore
    userStore.setUserInfo({
      username: result.username,
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
      <div class="avatar-section soft-action-surface--card">
        <el-avatar :src="profile.avatar" :size="80" class="avatar">
          <el-icon :size="40"><User /></el-icon>
        </el-avatar>
        <div class="avatar-copy">
          <div class="avatar-title">个人头像</div>
          <div class="avatar-tip">支持 JPG/PNG/GIF，最大 10MB</div>
        </div>
        <el-upload
          :show-file-list="false"
          :http-request="handleUploadAvatar"
          accept=".jpg,.jpeg,.png,.gif"
        >
          <el-button class="soft-action-btn soft-action-btn--primary" type="primary" :loading="isUploading">
            <el-icon><Upload /></el-icon>
            更换头像
          </el-button>
        </el-upload>
      </div>

      <!-- 只读信息展示 -->
      <div class="info-section">
        <div class="info-row info-row--identity">
          <span class="info-label">当前用户名</span>
          <span class="info-value">
            <UserIdentity :username="profile.username" :user-id="profile.user_id" fallback="用户" />
          </span>
        </div>

        <div class="info-row info-row--role">
          <span class="info-label">角色</span>
          <span class="info-value info-value--tags">
            <el-tag effect="light" size="large">{{ roleMap[profile.role] || profile.role }}</el-tag>
            <el-tag
              v-if="profile.role === 'teacher' && profile.status === 'pending'"
              :type="statusMap[profile.status]?.type"
              effect="light"
              size="large"
            >
              {{ statusMap[profile.status]?.text }}
            </el-tag>
          </span>
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
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            maxlength="50"
            :disabled="!canEditUsername"
          />
          <div v-if="usernameChangeTip" class="form-tip">
            {{ usernameChangeTip }}
          </div>
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
              class="soft-action-btn soft-action-btn--secondary soft-action-btn--small"
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
          <div class="profile-save-surface soft-action-surface">
            <el-button
              class="soft-action-btn soft-action-btn--primary"
              type="primary"
              :loading="isSaving"
              :disabled="!canSubmitUsernameChange"
              @click="handleSave"
            >
              保存修改
            </el-button>
          </div>
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
  margin-bottom: 32px;
  justify-content: flex-start;
}

.avatar {
  flex-shrink: 0;
  background: #e6f7ff;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
}

.avatar-copy {
  flex: 1;
  min-width: 0;
}

.avatar-title {
  color: #1e293b;
  font-weight: 600;
}

.avatar-tip {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.info-section {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fbff 0%, #ffffff 100%);
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 12px 14px;
  border: 1px solid #edf2f7;
  border-radius: 12px;
  background: #fff;
}

.info-row--identity,
.info-row--role {
  grid-column: span 2;
}

.info-label {
  width: 88px;
  color: #64748b;
  font-size: 13px;
  flex-shrink: 0;
}

.info-value {
  min-width: 0;
  color: #1f2937;
  font-weight: 600;
}

.info-value--tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.edit-form {
  max-width: 500px;
}

.email-input-group {
  display: flex;
  gap: 12px;
  width: 100%;
}

.profile-save-surface {
  width: fit-content;
}

.form-tip {
  font-size: 12px;
  color: #faad14;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .avatar-section {
    align-items: stretch;
  }

  .info-section {
    grid-template-columns: 1fr;
    padding: 12px;
  }

  .info-row,
  .info-row--identity,
  .info-row--role {
    grid-column: span 1;
  }

  .info-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .email-input-group {
    flex-direction: column;
  }

  .profile-save-surface {
    width: 100%;
  }
}
</style>