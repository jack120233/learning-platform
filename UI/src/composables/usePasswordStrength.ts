import { computed, type Ref, type ComputedRef } from 'vue'

/**
 * 密码强度等级
 */
export type PasswordStrength = 'weak' | 'medium' | 'strong'

/**
 * 密码强度状态
 */
export interface PasswordStrengthState {
  strength: ComputedRef<PasswordStrength>
  score: ComputedRef<number>
  message: ComputedRef<string>
  color: ComputedRef<string>
  percentage: ComputedRef<number>
}

/**
 * 密码强度校验 Composable
 * @param password 密码响应式引用
 */
export function usePasswordStrength(password: Ref<string>): PasswordStrengthState {
  /**
   * 计算密码得分（0-100）
   * - 长度 >= 8: +25分
   * - 包含小写字母: +15分
   * - 包含大写字母: +15分
   * - 包含数字: +15分
   * - 包含特殊字符: +20分
   * - 长度 >= 12: +10分
   */
  const score = computed(() => {
    const pwd = password.value
    if (!pwd) return 0

    let s = 0

    // 长度检查
    if (pwd.length >= 8) s += 25
    if (pwd.length >= 12) s += 10

    // 包含小写字母
    if (/[a-z]/.test(pwd)) s += 15

    // 包含大写字母
    if (/[A-Z]/.test(pwd)) s += 15

    // 包含数字
    if (/\d/.test(pwd)) s += 15

    // 包含特殊字符
    if (/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'`~]/.test(pwd)) s += 20

    return Math.min(s, 100)
  })

  /**
   * 密码强度等级
   */
  const strength = computed<PasswordStrength>(() => {
    const s = score.value
    if (s < 40) return 'weak'
    if (s < 70) return 'medium'
    return 'strong'
  })

  /**
   * 强度提示信息
   */
  const message = computed(() => {
    const s = strength.value
    if (!password.value) return ''
    switch (s) {
      case 'weak':
        return '弱'
      case 'medium':
        return '中'
      case 'strong':
        return '强'
    }
  })

  /**
   * 进度条颜色
   */
  const color = computed(() => {
    const s = strength.value
    switch (s) {
      case 'weak':
        return '#f5222d' // 红色
      case 'medium':
        return '#faad14' // 黄色
      case 'strong':
        return '#52c41a' // 绿色
    }
  })

  /**
   * 进度条百分比
   */
  const percentage = computed(() => {
    const s = score.value
    // 映射到 0-100
    return s
  })

  return {
    strength,
    score,
    message,
    color,
    percentage,
  }
}