<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Edit, Setting, Lock, Phone, Message, Promotion, Clock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/store/user'
import { register, getCaptcha, sendEmailCode } from '@/api/auth'
import { useCountdown } from '@/composables/useCountdown'
import {
  usernameRules,
  passwordRules,
  createConfirmPasswordRules,
  phoneRules,
  emailRules,
  emailCodeRules,
  captchaRules,
} from '@/utils/validators'
import AuthLayout from '@/layouts/AuthLayout.vue'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = ref({
  role: 'student' as 'student' | 'teacher' | 'admin',
  username: '',
  password: '',
  confirmPassword: '',
  phone: '',
  email: '',
  captcha: '',
  captchaId: '',
  emailCode: '',
  referrerEmail: '',
})

// UI 状态
const isSubmitting = ref(false)
const isSendingCode = ref(false)
const captchaImage = ref('')
const isRefreshingCaptcha = ref(false)

// 弹窗控制
const showTeacherPendingDialog = ref(false)

// 倒计时
const { countdown, isActive: isCountdownActive, start: startCountdown } = useCountdown(60)

// 角色选项
const roleOptions: { value: 'student' | 'teacher' | 'admin'; label: string; desc: string }[] = [
  { value: 'student', label: '学员', desc: '浏览课程，参与学习' },
  { value: 'teacher', label: '讲师', desc: '发布课程，审核通过后生效' },
  { value: 'admin', label: '管理员', desc: '管理平台，需推荐人邀请' },
]

// 表单校验规则
const formRules = computed<FormRules>(() => ({
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  username: usernameRules,
  password: passwordRules,
  confirmPassword: createConfirmPasswordRules(() => formData.value.password),
  phone: phoneRules,
  email: emailRules,
  captcha: captchaRules,
  emailCode: emailCodeRules,
  referrerEmail: formData.value.role === 'admin' ? [
    { required: true, message: '请输入推荐管理员邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ] : [],
}))

// 加载图形验证码
const loadCaptcha = async () => {
  isRefreshingCaptcha.value = true
  try {
    const response = await getCaptcha()
    captchaImage.value = response.captcha_image
    formData.value.captchaId = response.captcha_id
    formData.value.captcha = ''
  } catch (error) {
    ElMessage.error('加载验证码失败')
    captchaImage.value = ''
  } finally {
    isRefreshingCaptcha.value = false
  }
}

// 刷新图形验证码
const handleRefreshCaptcha = async () => {
  if (isRefreshingCaptcha.value) return
  await loadCaptcha()
}

// 发送邮箱验证码
const handleSendEmailCode = async () => {
  // 先校验邮箱格式
  if (!formData.value.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }

  // 简单校验邮箱格式
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(formData.value.email)) {
    ElMessage.warning('请输入正确的邮箱地址')
    return
  }

  isSendingCode.value = true

  try {
    await sendEmailCode({
      email: formData.value.email,
      purpose: 'register',
    })

    startCountdown()
    ElMessage.success('验证码已发送')
  } catch (error: any) {
    const message = error.message || '发送失败'
    if (message.includes('频繁') || error.code === 429) {
      ElMessage.warning('发送过于频繁，请 60 秒后重试')
    } else {
      ElMessage.error(message)
    }
  } finally {
    isSendingCode.value = false
  }
}

// 角色切换
const handleRoleChange = () => {
  // 清空推荐管理员邮箱
  if (formData.value.role !== 'admin') {
    formData.value.referrerEmail = ''
  }
  // 清除校验错误
  formRef.value?.clearValidate()
}

// 提交注册
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    // 滚动到第一个错误字段
    const firstError = document.querySelector('.el-form-item.is-error')
    firstError?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  isSubmitting.value = true

  try {
    const response = await register({
      username: formData.value.username,
      email: formData.value.email,
      phone: formData.value.phone,
      password: formData.value.password,
      confirm_password: formData.value.confirmPassword,
      role: formData.value.role,
      captcha: formData.value.captcha,
      captcha_id: formData.value.captchaId,
      email_code: formData.value.emailCode,
      referrer_email: formData.value.role === 'admin' ? formData.value.referrerEmail : undefined,
    })

    // 存储登录信息
    userStore.setLoginInfo({
      user_id: response.user_id,
      username: response.username,
      email: response.email,
      role: response.role as any,
      status: response.status,
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    })

    // 根据角色处理
    if (response.role === 'teacher' && response.status === 'pending') {
      showTeacherPendingDialog.value = true
    } else {
      ElMessage.success('注册成功')
      router.push('/')
    }
  } catch (error: any) {
    const message = error.message || '注册失败'

    if (message.includes('用户名')) {
      ElMessage.error('该用户名已被使用')
    } else if (message.includes('手机号')) {
      ElMessage.error('该手机号已被使用')
    } else if (message.includes('邮箱')) {
      ElMessage.error('该邮箱已被使用')
    } else if (message.includes('验证码')) {
      ElMessage.error('验证码错误')
      // 自动刷新图形验证码
      loadCaptcha()
    } else if (message.includes('推荐')) {
      ElMessage.error('推荐管理员账号不存在，请确认后重新输入')
    } else {
      ElMessage.error(message)
      // 其他错误也刷新验证码
      loadCaptcha()
    }
  } finally {
    isSubmitting.value = false
  }
}

// 讲师弹窗关闭
const handleTeacherDialogClose = () => {
  showTeacherPendingDialog.value = false
  router.push('/')
}

// 初始化
onMounted(() => {
  // 检查登录态
  if (userStore.isLoggedIn) {
    router.replace('/')
    return
  }

  // 加载图形验证码
  loadCaptcha()
})
</script>

<template>
  <AuthLayout title="加入我们" sub-title="创建账号，开启学习之旅">
    <div class="register-form">
      <h2 class="form-title">注册</h2>

      <!-- 注册表单 -->
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
        size="large"
      >
        <!-- 角色选择器 -->
        <el-form-item label="选择角色" prop="role">
          <el-radio-group v-model="formData.role" class="role-picker" @change="handleRoleChange">
            <el-radio-button
              v-for="option in roleOptions"
              :key="option.value"
              :value="option.value"
              class="role-option"
            >
              <div class="role-content">
                <el-icon :size="24">
                  <User v-if="option.value === 'student'" />
                  <Edit v-else-if="option.value === 'teacher'" />
                  <Setting v-else />
                </el-icon>
                <span class="role-label">{{ option.label }}</span>
                <span class="role-desc">{{ option.desc }}</span>
              </div>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 用户名 -->
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名（4-20位字母、数字、下划线）"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <!-- 密码 -->
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码（8-20位，包含字母和数字）"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <!-- 确认密码 -->
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="formData.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <!-- 手机号 -->
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="formData.phone"
            placeholder="请输入 11 位手机号"
            :prefix-icon="Phone"
            clearable
          />
        </el-form-item>

        <!-- 邮箱 -->
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="formData.email"
            placeholder="请输入邮箱地址"
            :prefix-icon="Message"
            clearable
          />
        </el-form-item>

        <!-- 图形验证码 -->
        <el-form-item label="图形验证码" prop="captcha">
          <div class="captcha-row">
            <el-input
              v-model="formData.captcha"
              placeholder="请输入 4 位验证码"
              maxlength="4"
              clearable
            />
            <button
              type="button"
              class="captcha-image"
              :class="{ loading: isRefreshingCaptcha }"
              :disabled="isRefreshingCaptcha"
              aria-label="图形验证码，点击刷新"
              @click="handleRefreshCaptcha"
            >
              <img
                v-if="captchaImage"
                :src="captchaImage"
                alt="验证码"
              />
              <span v-else class="placeholder">点击刷新</span>
            </button>
          </div>
        </el-form-item>

        <!-- 邮箱验证码 -->
        <el-form-item label="邮箱验证码" prop="emailCode">
          <div class="code-input-row">
            <el-input
              v-model="formData.emailCode"
              placeholder="请输入 6 位验证码"
              maxlength="6"
              clearable
            />
            <el-button
              :disabled="isCountdownActive"
              :loading="isSendingCode"
              @click="handleSendEmailCode"
            >
              {{ isCountdownActive ? `${countdown}s 后重发` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <!-- 推荐管理员邮箱（管理员专用） -->
        <el-form-item
          v-if="formData.role === 'admin'"
          label="推荐管理员邮箱"
          prop="referrerEmail"
        >
          <el-input
            v-model="formData.referrerEmail"
            placeholder="请输入推荐管理员的邮箱"
            :prefix-icon="Promotion"
            clearable
          />
        </el-form-item>

        <!-- 注册按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="isSubmitting"
            class="submit-btn"
            @click="handleSubmit"
          >
            {{ isSubmitting ? '注册中...' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 登录链接 -->
      <div class="login-link">
        已有账号？<router-link to="/login">去登录</router-link>
      </div>
    </div>

    <!-- 讲师审核中弹窗 -->
    <el-dialog
      v-model="showTeacherPendingDialog"
      title="申请已提交"
      width="400px"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <div class="pending-dialog">
        <el-icon :size="64" color="#faad14"><Clock /></el-icon>
        <p class="pending-text">
          您的讲师申请已提交，审核通过后将通过站内消息通知您。<br />
          当前您可以作为学员浏览和学习课程。
        </p>
      </div>
      <template #footer>
        <el-button type="primary" @click="handleTeacherDialogClose">
          我知道了
        </el-button>
      </template>
    </el-dialog>
  </AuthLayout>
</template>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.register-form {
  width: 100%;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 24px;
  text-align: center;
}

.role-picker {
  display: flex;
  gap: 12px;
  width: 100%;

  :deep(.el-radio-button) {
    flex: 1;
    margin: 0 !important;

    .el-radio-button__inner {
      width: 100%;
      padding: 16px 8px;
      border: 2px solid $border-color;
      border-radius: $radius-md;
      background: transparent;
      box-shadow: none;
    }

    &.is-active .el-radio-button__inner {
      border-color: $primary-color;
      background-color: rgba($primary-color, 0.05);
      box-shadow: none;
    }

    .role-label {
      color: $text-primary;
    }

    &.is-active .role-label {
      color: $primary-color;
    }
  }
}

.role-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.role-label {
  font-size: 15px;
  font-weight: 500;
  color: $text-primary;
  margin-top: 8px;
}

.role-desc {
  font-size: 12px;
  color: $text-tertiary;
  margin-top: 4px;
  text-align: center;
}

.captcha-row {
  display: flex;
  gap: 12px;

  .el-input {
    flex: 1;
  }

  .captcha-image {
    width: 120px;
    height: 40px;
    border: 1px solid $border-color;
    border-radius: $radius-sm;
    overflow: hidden;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: $bg-color;
    padding: 0;
    font-family: inherit;

    &:disabled {
      cursor: not-allowed;
    }

    &.loading {
      opacity: 0.6;
    }

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    .placeholder {
      font-size: 12px;
      color: $text-tertiary;
    }
  }
}

.code-input-row {
  display: flex;
  gap: 12px;

  .el-input {
    flex: 1;
  }

  .el-button {
    width: 120px;
  }
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.login-link {
  text-align: center;
  color: $text-secondary;
  font-size: 14px;
  margin-top: 24px;

  a {
    color: $primary-color;
    text-decoration: none;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }
}

.pending-dialog {
  text-align: center;
  padding: 24px 0;

  .pending-text {
    margin-top: 24px;
    font-size: 14px;
    color: $text-secondary;
    line-height: 1.8;
  }
}

@media (max-width: $breakpoint-sm) {
  .role-picker {
    flex-direction: column;
  }

  .captcha-row {
    .captcha-image {
      width: 100px;
    }
  }

  .code-input-row {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}
</style>