<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Edit, Lock, Phone, Message, Clock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/store/user'
import { register } from '@/api/auth'
import {
  passwordRules,
  createConfirmPasswordRules,
  phoneRules,
  emailRules,
} from '@/utils/validators'
import AuthLayout from '@/layouts/AuthLayout.vue'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = ref({
  role: 'student' as 'student' | 'teacher',
  username: '',
  password: '',
  confirmPassword: '',
  phone: '',
  email: '',
})

// UI 状态
const isSubmitting = ref(false)

// 弹窗控制
const showTeacherPendingDialog = ref(false)

// 角色选项
const roleOptions: { value: 'student' | 'teacher'; label: string; desc: string }[] = [
  { value: 'student', label: '学生', desc: '浏览课程，参与学习' },
  { value: 'teacher', label: '老师', desc: '发布课程，审核通过后生效' },
]

// 表单校验规则
const realNameRules = [
  { required: true, message: '请输入真实姓名', trigger: 'blur' },
  { min: 2, max: 50, message: '真实姓名长度需在 2-50 个字符之间', trigger: 'blur' },
]

const formRules = computed<FormRules>(() => ({
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  username: realNameRules,
  password: passwordRules,
  confirmPassword: createConfirmPasswordRules(() => formData.value.password),
  phone: phoneRules,
  email: emailRules,
}))

// 角色切换
const handleRoleChange = () => {
  formRef.value?.clearValidate()
}

// 提交注册
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    const firstError = document.querySelector('.el-form-item.is-error')
    firstError?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  isSubmitting.value = true

  try {
    const response = await register({
      username: formData.value.username.trim(),
      email: formData.value.email.trim(),
      phone: formData.value.phone.trim() || undefined,
      password: formData.value.password,
      confirm_password: formData.value.confirmPassword,
      role: formData.value.role,
      real_name: formData.value.username.trim(),
    })

    userStore.setLoginInfo({
      user_id: response.user_id,
      username: response.username,
      email: response.email,
      role: response.role as any,
      status: response.status,
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    })

    await userStore.loadMyPermissions(true).catch(() => [])

    if (response.role === 'teacher' && response.status === 'pending') {
      showTeacherPendingDialog.value = true
    } else {
      ElMessage.success('注册成功')
      router.push('/')
    }
  } catch (error: any) {
    const message = error.message || '注册失败'

    if (message.includes('用户名')) {
      ElMessage.error('该真实姓名已被使用')
    } else if (message.includes('手机号')) {
      ElMessage.error('该手机号已被使用')
    } else if (message.includes('邮箱')) {
      ElMessage.error('该邮箱已被使用')
    } else {
      ElMessage.error(message)
    }
  } finally {
    isSubmitting.value = false
  }
}

// 老师申请弹窗关闭
const handleTeacherDialogClose = () => {
  showTeacherPendingDialog.value = false
  router.push('/')
}

// 初始化
onMounted(() => {
  if (userStore.isLoggedIn) {
    router.replace('/')
  }
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
                  <Edit v-else />
                </el-icon>
                <span class="role-label">{{ option.label }}</span>
                <span class="role-desc">{{ option.desc }}</span>
              </div>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 真实姓名 -->
        <el-form-item label="真实姓名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入真实姓名"
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

        <!-- 注册按钮 -->
        <el-form-item>
          <div class="auth-submit-surface soft-action-surface">
            <el-button
              type="primary"
              :loading="isSubmitting"
              class="submit-btn soft-action-btn soft-action-btn--primary"
              @click="handleSubmit"
            >
              {{ isSubmitting ? '注册中...' : '注册' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <!-- 登录链接 -->
      <div class="login-link">
        已有账号？<router-link to="/login">去登录</router-link>
      </div>
    </div>

    <!-- 老师审核中弹窗 -->
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
          您的老师申请已提交，审核通过后将通过站内消息通知您。<br />
          当前您可以作为学生浏览和学习课程。
        </p>
      </div>
      <template #footer>
        <div class="dialog-action-surface soft-action-surface">
          <el-button
            type="primary"
            class="soft-action-btn soft-action-btn--primary"
            @click="handleTeacherDialogClose"
          >
            我知道了
          </el-button>
        </div>
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

.auth-submit-surface,
.dialog-action-surface {
  width: 100%;
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
}
</style>
