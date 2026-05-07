import type { FormItemRule } from 'element-plus'

// 密码正则：8-20位，至少包含字母和数字
export const PASSWORD_PATTERN = /^(?=.*[a-zA-Z])(?=.*\d).+$/

// 手机号正则：11位，以1开头，第二位为3-9
export const PHONE_PATTERN = /^1[3-9]\d{9}$/

// 用户名正则：4-20位，仅支持字母、数字和下划线
export const USERNAME_PATTERN = /^[a-zA-Z0-9_]{4,20}$/

// 邮箱验证码正则：6位数字
export const EMAIL_CODE_PATTERN = /^\d{6}$/

// 图形验证码正则：4位
export const CAPTCHA_PATTERN = /^[a-zA-Z0-9]{4}$/i

/**
 * 密码校验规则
 */
export const passwordRules: FormItemRule[] = [
  { required: true, message: '请输入密码', trigger: 'blur' },
  { min: 8, max: 20, message: '密码长度为 8-20 位', trigger: 'blur' },
  {
    pattern: PASSWORD_PATTERN,
    message: '密码需包含字母和数字',
    trigger: 'blur',
  },
]

/**
 * 创建确认密码校验规则
 * @param getPassword 获取密码值的函数
 */
export function createConfirmPasswordRules(getPassword: () => string): FormItemRule[] {
  return [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== getPassword()) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ]
}

/**
 * 手机号校验规则
 */
export const phoneRules: FormItemRule[] = [
  { required: true, message: '请输入手机号', trigger: 'blur' },
  { pattern: PHONE_PATTERN, message: '请输入正确的 11 位手机号', trigger: 'blur' },
]

/**
 * 邮箱校验规则
 */
export const emailRules: FormItemRule[] = [
  { required: true, message: '请输入邮箱', trigger: 'blur' },
  { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
]

/**
 * 用户名校验规则
 */
export const usernameRules: FormItemRule[] = [
  { required: true, message: '请输入用户名', trigger: 'blur' },
  { min: 4, max: 20, message: '用户名长度为 4-20 位', trigger: 'blur' },
  { pattern: USERNAME_PATTERN, message: '仅支持字母、数字和下划线', trigger: 'blur' },
]

/**
 * 邮箱验证码校验规则
 */
export const emailCodeRules: FormItemRule[] = [
  { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
  { len: 6, message: '验证码为 6 位', trigger: 'blur' },
  { pattern: EMAIL_CODE_PATTERN, message: '验证码为 6 位数字', trigger: 'blur' },
]

/**
 * 图形验证码校验规则
 */
export const captchaRules: FormItemRule[] = [
  { required: true, message: '请输入图形验证码', trigger: 'blur' },
  { len: 4, message: '验证码为 4 位', trigger: 'blur' },
]

/**
 * 创建动态校验规则（用于登录页的邮箱/手机号切换）
 * @param getType 获取当前类型的函数
 */
export function createLoginIdRules(getType: () => 'email' | 'phone'): FormItemRule[] {
  return [
    {
      required: true,
      validator: (_rule, value, callback) => {
        if (!value) {
          callback(new Error(getType() === 'email' ? '请输入邮箱' : '请输入手机号'))
        } else if (getType() === 'email') {
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            callback(new Error('请输入正确的邮箱地址'))
          } else {
            callback()
          }
        } else {
          if (!PHONE_PATTERN.test(value)) {
            callback(new Error('请输入正确的 11 位手机号'))
          } else {
            callback()
          }
        }
      },
      trigger: 'blur',
    },
  ]
}

/**
 * 判断输入是邮箱还是手机号
 */
export function detectLoginType(value: string): 'email' | 'phone' {
  if (PHONE_PATTERN.test(value)) {
    return 'phone'
  }
  return 'email'
}