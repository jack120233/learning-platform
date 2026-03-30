<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Message, Phone, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/store/user'
import { sendEmailCode, resetPassword } from '@/api/auth'
import { useCountdown } from '@/composables/useCountdown'
import { maskEmail } from '@/utils/format'
import { createLoginIdRules, passwordRules, createConfirmPasswordRules } from '@/utils/validators'
import AuthLayout from '@/layouts/AuthLayout.vue'

const router = useRouter()
const userStore = useUserStore()

// 步骤控制
const currentStep = ref(0) // 0=验证身份, 1=输入验证码, 2=设置新密码, 3=成功

// 表单引用
const step1FormRef = ref<FormInstance>()
const step2FormRef = ref<FormInstance>()
const step3FormRef = ref<FormInstance>()

// 找回方式
const resetMethod = ref<'email' | 'phone'>('email')

// 表单数据
const formData = ref({
  loginId: '',
  emailCode: '',
  targetEmail: '', // 实际接收验证码的邮箱
  maskedEmail: '', // 脱敏展示的邮箱
  newPassword: '',
  confirmPassword: '',
})

// UI 状态
const isVerifying = ref(false)
const isVerifyingCode = ref(false)
const isResetting = ref(false)
const isSendingCode = ref(false)

// 错误信息
const step1Error = ref('')
const step2Error = ref('')
const step3Error = ref('')

// 倒计时
const { countdown, isActive: isCountdownActive, start: startCountdown } = useCountdown(60)

// 步骤标题
const stepTitles = ['验证身份', '输入验证码', '设置新密码']

// 步骤1校验规则
const step1Rules = computed<FormRules>(() => ({
  loginId: createLoginIdRules(() => resetMethod.value),
}))

// 步骤2校验规则
const step2Rules: FormRules = {
  emailCode: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { len: 6, message: '验证码为 6 位', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为 6 位数字', trigger: 'blur' },
  ],
}

// 步骤3校验规则
const step3Rules = computed<FormRules>(() => ({
  newPassword: passwordRules,
  confirmPassword: createConfirmPasswordRules(() => formData.value.newPassword),
}))

// 切换找回方式
const handleMethodChange = () => {
  formData.value.loginId = ''
  step1Error.value = ''
  step1FormRef.value?.clearValidate()
}

// 步骤1：发送验证码
const handleStep1Next = async () => {
  if (!step1FormRef.value) return

  try {
    await step1FormRef.value.validate()
  } catch {
    return
  }

  step1Error.value = ''
  isVerifying.value = true

  try {
    // 发送验证码
    await sendEmailCode({
      email: formData.value.loginId,
      purpose: 'reset_password',
    })

    // 记录目标邮箱
    formData.value.targetEmail = formData.value.loginId
    formData.value.maskedEmail = maskEmail(formData.value.loginId)

    // 启动倒计时
    startCountdown()

    ElMessage.success('验证码已发送')
    currentStep.value = 1
  } catch (error: any) {
    const message = error.message || '发送失败'

    if (message.includes('不存在') || message.includes('未注册')) {
      step1Error.value = '该邮箱/手机号未注册账号'
    } else if (message.includes('频繁') || error.code === 429) {
      step1Error.value = '发送过于频繁，请 60 秒后重试'
    } else {
      step1Error.value = message
    }
  } finally {
    isVerifying.value = false
  }
}

// 步骤2：重新发送验证码
const handleResendCode = async () => {
  if (isCountdownActive.value) return

  isSendingCode.value = true
  step2Error.value = ''

  try {
    await sendEmailCode({
      email: formData.value.targetEmail || formData.value.loginId,
      purpose: 'reset_password',
    })

    startCountdown()
    ElMessage.success('验证码已重新发送')
  } catch (error: any) {
    const message = error.message || '发送失败'
    if (message.includes('频繁') || error.code === 429) {
      ElMessage.warning('发送过于频繁，请稍后重试')
    } else {
      ElMessage.error(message)
    }
  } finally {
    isSendingCode.value = false
  }
}

// 步骤2：上一步
const handleStep2Prev = () => {
  currentStep.value = 0
}

// 步骤2：下一步
const handleStep2Next = async () => {
  if (!step2FormRef.value) return

  try {
    await step2FormRef.value.validate()
  } catch {
    return
  }

  // 前端仅做格式校验，验证码有效性在步骤3由后端校验
  currentStep.value = 2
}

// 步骤3：上一步
const handleStep3Prev = () => {
  currentStep.value = 1
}

// 步骤3：确认重置
const handleResetPassword = async () => {
  if (!step3FormRef.value) return

  try {
    await step3FormRef.value.validate()
  } catch {
    return
  }

  step3Error.value = ''
  isResetting.value = true

  try {
    await resetPassword({
      username: formData.value.loginId,
      email_code: formData.value.emailCode,
      new_password: formData.value.newPassword,
      confirm_password: formData.value.confirmPassword,
    })

    ElMessage.success('密码重置成功')
    currentStep.value = 3
  } catch (error: any) {
    const message = error.message || '重置失败'

    if (message.includes('验证码')) {
      step3Error.value = '验证码错误或已过期'
      // 弹窗询问是否返回重新获取
      ElMessageBox.confirm('验证码已失效，是否返回重新获取？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }).then(() => {
        currentStep.value = 0
        formData.value.emailCode = ''
      }).catch(() => {})
    } else if (message.includes('密码')) {
      step3Error.value = '密码需为 8-20 位字母 + 数字组合'
    } else if (message.includes('不存在')) {
      step3Error.value = '该账号不存在'
    } else {
      step3Error.value = message
    }
  } finally {
    isResetting.value = false
  }
}

// 成功页：去登录
const handleGoLogin = () => {
  router.push('/login')
}

// 页面离开提示
onBeforeRouteLeave((_to, _from, next) => {
  if (formData.value.loginId && currentStep.value < 3) {
    ElMessageBox.confirm('确定要离开吗？当前填写的信息将丢失', '提示', {
      confirmButtonText: '确定离开',
      cancelButtonText: '继续填写',
      type: 'warning',
    }).then(() => next()).catch(() => next(false))
  } else {
    next()
  }
})

// 初始化
onMounted(() => {
  // 检查登录态
  if (userStore.isLoggedIn) {
    router.replace('/')
  }
})
</script>

<template>
  <AuthLayout title="找回密码" sub-title="重置您的登录密码">
    <div class="forgot-password-form">
      <h2 class="form-title">找回密码</h2>

      <!-- 步骤条 -->
      <el-steps :active="currentStep" align-center class="steps">
        <el-step v-for="(title, index) in stepTitles" :key="index" :title="title" />
      </el-steps>

      <!-- 步骤1：验证身份 -->
      <div v-show="currentStep === 0" class="step-content">
        <el-form
          ref="step1FormRef"
          :model="formData"
          :rules="step1Rules"
          label-position="top"
          size="large"
        >
          <!-- 找回方式选择 -->
          <el-form-item label="找回方式">
            <el-radio-group v-model="resetMethod" @change="handleMethodChange">
              <el-radio-button value="email">邮箱找回</el-radio-button>
              <el-radio-button value="phone">手机号找回</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <!-- 账号输入 -->
          <el-form-item prop="loginId">
            <el-input
              v-model="formData.loginId"
              :placeholder="resetMethod === 'email' ? '请输入注册邮箱' : '请输入注册手机号'"
              :prefix-icon="resetMethod === 'email' ? Message : Phone"
              clearable
            />
          </el-form-item>

          <!-- 错误提示 -->
          <el-alert
            v-if="step1Error"
            :title="step1Error"
            type="error"
            :closable="false"
            show-icon
            class="error-alert"
          />

          <el-form-item>
            <el-button
              type="primary"
              :loading="isVerifying"
              class="submit-btn"
              @click="handleStep1Next"
            >
              {{ isVerifying ? '发送中...' : '下一步' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤2：输入验证码 -->
      <div v-show="currentStep === 1" class="step-content">
        <el-alert
          :title="`验证码已发送至 ${formData.maskedEmail}，请查收`"
          type="success"
          :closable="false"
          show-icon
          class="email-hint"
        />

        <el-form
          ref="step2FormRef"
          :model="formData"
          :rules="step2Rules"
          label-position="top"
          size="large"
        >
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
                @click="handleResendCode"
              >
                {{ isCountdownActive ? `${countdown}s 后重发` : '重新发送' }}
              </el-button>
            </div>
          </el-form-item>

          <!-- 错误提示 -->
          <el-alert
            v-if="step2Error"
            :title="step2Error"
            type="error"
            :closable="false"
            show-icon
            class="error-alert"
          />

          <el-form-item>
            <div class="button-row">
              <el-button @click="handleStep2Prev">上一步</el-button>
              <el-button
                type="primary"
                :loading="isVerifyingCode"
                @click="handleStep2Next"
              >
                下一步
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤3：设置新密码 -->
      <div v-show="currentStep === 2" class="step-content">
        <el-form
          ref="step3FormRef"
          :model="formData"
          :rules="step3Rules"
          label-position="top"
          size="large"
        >
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="formData.newPassword"
              type="password"
              placeholder="请输入新密码（8-20位字母+数字）"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input
              v-model="formData.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <!-- 错误提示 -->
          <el-alert
            v-if="step3Error"
            :title="step3Error"
            type="error"
            :closable="false"
            show-icon
            class="error-alert"
          />

          <el-form-item>
            <div class="button-row">
              <el-button @click="handleStep3Prev">上一步</el-button>
              <el-button
                type="primary"
                :loading="isResetting"
                @click="handleResetPassword"
              >
                {{ isResetting ? '重置中...' : '确认重置' }}
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 成功页 -->
      <div v-show="currentStep === 3" class="step-content success-content">
        <el-result icon="success" title="密码重置成功" sub-title="请使用新密码登录">
          <template #extra>
            <el-button type="primary" size="large" @click="handleGoLogin">
              去登录
            </el-button>
          </template>
        </el-result>
      </div>
    </div>
  </AuthLayout>
</template>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.forgot-password-form {
  width: 100%;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 24px;
  text-align: center;
}

.steps {
  margin-bottom: 32px;

  :deep(.el-step__title) {
    font-size: 13px;
  }
}

.step-content {
  margin-top: 24px;
}

.error-alert {
  margin-bottom: 16px;
}

.email-hint {
  margin-bottom: 24px;
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

.button-row {
  display: flex;
  gap: 12px;
  width: 100%;

  .el-button {
    flex: 1;
  }
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.success-content {
  padding: 24px 0;
}

:deep(.el-radio-group) {
  width: 100%;
  display: flex;

  .el-radio-button {
    flex: 1;

    .el-radio-button__inner {
      width: 100%;
    }
  }
}
</style>