/**
 * 邮箱地址脱敏展示
 * @param email 邮箱地址
 * @returns 脱敏后的邮箱
 * @example
 * maskEmail('zhangsan@example.com') // => 'z***n@example.com'
 * maskEmail('ab@example.com') // => 'a***b@example.com'
 */
export function maskEmail(email: string): string {
  if (!email || !email.includes('@')) {
    return email
  }

  const [local, domain] = email.split('@')

  if (local.length <= 2) {
    return `${local[0]}***@${domain}`
  }

  return `${local[0]}***${local[local.length - 1]}@${domain}`
}

/**
 * 手机号脱敏展示
 * @param phone 手机号
 * @returns 脱敏后的手机号
 * @example
 * maskPhone('13812345678') // => '138****5678'
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length !== 11) {
    return phone
  }

  return `${phone.slice(0, 3)}****${phone.slice(7)}`
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

/**
 * 格式化视频时长
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '0:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${m}:${String(s).padStart(2, '0')}`
}

/**
 * 格式化日期
 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 30) {
    return formatDate(dateStr)
  } else if (days > 0) {
    return `${days} 天前`
  } else if (hours > 0) {
    return `${hours} 小时前`
  } else if (minutes > 0) {
    return `${minutes} 分钟前`
  } else {
    return '刚刚'
  }
}