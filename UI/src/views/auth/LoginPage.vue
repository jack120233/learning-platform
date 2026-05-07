<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Message, Phone, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/store/user'
import { login } from '@/api/auth'
import { createLoginIdRules, detectLoginType } from '@/utils/validators'
import AuthLayout from '@/layouts/AuthLayout.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 表单引用
const formRef = ref<FormInstance>()

// 登录方式
const loginMethod = ref<'email' | 'phone'>('email')

// 表单数据
const formData = ref({
  loginId: '',
  password: '',
  rememberMe: false,
})

// 提交状态
const isSubmitting = ref(false)

// 登录失败计数
const loginErrorCount = ref(0)

// 重定向 URL
const redirectUrl = computed(() => route.query.redirect as string || null)

// 表单校验规则
const formRules = computed<FormRules>(() => ({
  loginId: createLoginIdRules(() => loginMethod.value),
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度为 8-20 位', trigger: 'blur' },
  ],
}))

// 切换登录方式
const handleMethodChange = () => {
  formData.value.loginId = ''
  formRef.value?.clearValidate('loginId')
}

// 处理登录
const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  isSubmitting.value = true

  try {
    const response = await login({
      username: formData.value.loginId,
      password: formData.value.password,
      remember_me: formData.value.rememberMe,
    })

    // 存储登录信息（后端返回 user 对象嵌套结构）
    userStore.setLoginInfo({
      user_id: response.user.id,
      username: response.user.username,
      email: response.user.email,
      nickname: response.user.nickname,
      avatar_url: response.user.avatar || '',
      role: response.user.role,
      status: response.user.status,
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    })

    if (!userStore.isLoggedIn || userStore.userInfo.role !== response.user.role) {
      throw new Error('登录状态初始化失败，请重试')
    }

    await userStore.loadMyPermissions(true).catch(() => [])

    // 处理"记住我"
    if (formData.value.rememberMe) {
      localStorage.setItem('edu_remember_login_id', formData.value.loginId)
    } else {
      localStorage.removeItem('edu_remember_login_id')
    }

    ElMessage.success('登录成功')

    // 角色跳转
    if (redirectUrl.value) {
      router.replace(redirectUrl.value)
    } else if (userStore.canAccessAdminCenter) {
      router.replace('/admin')
    } else {
      router.replace('/')
    }
  } catch (error: any) {
    loginErrorCount.value++

    // 根据错误信息显示不同提示
    const message = error.message || '登录失败，请稍后重试'

    if (message.includes('不存在') || message.includes('密码错误')) {
      ElMessage.error('账号不存在或密码错误')
      if (loginErrorCount.value >= 3) {
        ElMessage.warning('密码连续错误 5 次将锁定账号')
      }
    } else if (message.includes('锁定')) {
      ElMessage.error('账号已锁定，请 30 分钟后重试')
    } else if (message.includes('禁用')) {
      ElMessage.error('账号已被禁用，请联系管理员')
    } else {
      ElMessage.error(message)
    }
  } finally {
    isSubmitting.value = false
  }
}

// 回车键处理
const handleLoginIdEnter = () => {
  const passwordInput = document.querySelector('input[type="password"]') as HTMLInputElement
  passwordInput?.focus()
}

const handlePasswordEnter = () => {
  handleLogin()
}

// 初始化
onMounted(() => {
  // 检查登录态
  if (userStore.isLoggedIn) {
    router.replace('/')
    return
  }

  // 恢复"记住我"状态
  const rememberedLoginId = localStorage.getItem('edu_remember_login_id')
  if (rememberedLoginId) {
    formData.value.loginId = rememberedLoginId
    formData.value.rememberMe = true
    // 自动判断登录方式
    loginMethod.value = detectLoginType(rememberedLoginId)
  }
})
</script>

<template>
  <AuthLayout title="欢迎回来" sub-title="登录您的账号，继续学习之旅">
    <div class="login-form">
      <h2 class="form-title">登录</h2>

      <!-- 登录方式切换 -->
      <el-tabs v-model="loginMethod" class="login-tabs" @tab-change="handleMethodChange">
        <el-tab-pane label="邮箱登录" name="email" />
        <el-tab-pane label="手机号登录" name="phone" />
      </el-tabs>

      <!-- 登录表单 -->
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
        size="large"
      >
        <!-- 账号输入 -->
        <el-form-item prop="loginId">
          <el-input
            v-model="formData.loginId"
            :placeholder="loginMethod === 'email' ? '请输入邮箱' : '请输入手机号'"
            :prefix-icon="loginMethod === 'email' ? Message : Phone"
            clearable
            @keyup.enter="handleLoginIdEnter"
          />
        </el-form-item>

        <!-- 密码输入 -->
        <el-form-item prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handlePasswordEnter"
          />
        </el-form-item>

        <!-- 辅助操作行 -->
        <div class="options-row">
          <el-checkbox v-model="formData.rememberMe">记住我</el-checkbox>
          <router-link to="/forgot-password" class="forgot-link">忘记密码？</router-link>
        </div>

        <!-- 登录按钮 -->
        <el-form-item>
          <div class="auth-submit-surface soft-action-surface">
            <el-button
              type="primary"
              :loading="isSubmitting"
              class="submit-btn soft-action-btn soft-action-btn--primary"
              @click="handleLogin"
            >
              {{ isSubmitting ? '登录中...' : '登录' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <!-- 注册链接 -->
      <div class="register-link">
        还没有账号？<router-link to="/register">去注册</router-link>
      </div>
    </div>
  </AuthLayout>
</template>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.login-form {
  width: 100%;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 24px;
  text-align: center;
}

.login-tabs {
  margin-bottom: 24px;

  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }

  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }

  :deep(.el-tabs__item) {
    font-size: 15px;
    color: $text-secondary;

    &.is-active {
      color: $primary-color;
      font-weight: 500;
    }
  }

  :deep(.el-tabs__active-bar) {
    background-color: $primary-color;
  }
}

.options-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  :deep(.el-checkbox__label) {
    color: $text-secondary;
    font-size: 14px;
  }
}

.forgot-link {
  color: $primary-color;
  font-size: 14px;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}

.auth-submit-surface {
  width: 100%;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.register-link {
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
</style>
