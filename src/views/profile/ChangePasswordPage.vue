<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { usePasswordStrength } from '@/composables/usePasswordStrength'
import { changePassword } from '@/api/profile'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

// 密码强度
const { message, color, percentage } = usePasswordStrength(
  computed(() => form.new_password)
)

// 提交状态
const isSubmitting = ref(false)

// 密码强度提示
const strengthText = computed(() => {
  if (!form.new_password) return ''
  return `密码强度：${message.value}`
})

// 确认密码校验
const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value !== form.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 新旧密码不能相同
const validateNewPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value === form.old_password) {
    callback(new Error('新密码不能与原密码相同'))
  } else if (value.length < 8) {
    callback(new Error('密码长度不能少于 8 位'))
  } else if (!/[a-zA-Z]/.test(value) || !/\d/.test(value)) {
    callback(new Error('密码必须包含字母和数字'))
  } else {
    callback()
  }
}

// 表单校验规则
const rules: FormRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { validator: validateNewPassword, trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// 提交修改
async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  isSubmitting.value = true
  try {
    await changePassword({
      old_password: form.old_password,
      new_password: form.new_password,
      confirm_password: form.confirm_password,
    })

    ElMessage.success('密码修改成功，请重新登录')

    // 清除登录态
    userStore.logout()

    // 跳转登录页
    router.replace('/login')
  } catch (error) {
    // 错误已由拦截器处理
  } finally {
    isSubmitting.value = false
  }
}

// 重置表单
function handleReset() {
  formRef.value?.resetFields()
}
</script>

<template>
  <div class="change-password-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">修改密码</h2>
      <p class="page-desc">修改密码后需要重新登录</p>
    </div>

    <!-- 表单 -->
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      class="password-form"
    >
      <el-form-item label="原密码" prop="old_password">
        <el-input
          v-model="form.old_password"
          type="password"
          placeholder="请输入原密码"
          show-password
          maxlength="32"
        />
      </el-form-item>

      <el-form-item label="新密码" prop="new_password">
        <el-input
          v-model="form.new_password"
          type="password"
          placeholder="请输入新密码（至少 8 位，包含字母和数字）"
          show-password
          maxlength="32"
        />
        <!-- 密码强度指示器 -->
        <div class="password-strength" v-if="form.new_password">
          <el-progress
            :percentage="percentage"
            :color="color"
            :stroke-width="6"
            :show-text="false"
          />
          <span class="strength-text" :style="{ color }">
            {{ strengthText }}
          </span>
        </div>
      </el-form-item>

      <el-form-item label="确认新密码" prop="confirm_password">
        <el-input
          v-model="form.confirm_password"
          type="password"
          placeholder="请再次输入新密码"
          show-password
          maxlength="32"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">
          确认修改
        </el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 密码安全提示 -->
    <div class="password-tips">
      <h4>密码安全提示</h4>
      <ul>
        <li>密码长度至少 8 位</li>
        <li>密码必须包含字母和数字</li>
        <li>建议包含大小写字母和特殊字符</li>
        <li>不要使用与用户名相同的密码</li>
        <li>定期更换密码，保障账户安全</li>
      </ul>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.change-password-page {
  .page-header {
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #333;
    margin: 0 0 8px;
  }

  .page-desc {
    font-size: 14px;
    color: #666;
    margin: 0;
  }
}

.password-form {
  max-width: 500px;
}

.password-strength {
  margin-top: 8px;

  .el-progress {
    width: 200px;
  }

  .strength-text {
    font-size: 12px;
    margin-left: 12px;
  }
}

.password-tips {
  margin-top: 32px;
  padding: 16px;
  background: #fffbe6;
  border-radius: 8px;
  border: 1px solid #ffe58f;
  max-width: 500px;

  h4 {
    font-size: 14px;
    font-weight: 500;
    color: #d48806;
    margin: 0 0 8px;
  }

  ul {
    margin: 0;
    padding-left: 20px;

    li {
      font-size: 13px;
      color: #666;
      line-height: 1.8;
    }
  }
}
</style>