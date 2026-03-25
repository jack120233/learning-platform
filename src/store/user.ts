import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type UserRole = 'student' | 'teacher' | 'admin' | null
export type UserStatus = 'active' | 'disabled' | 'pending' | null

export interface UserInfo {
  userId: number | null
  username: string
  email: string
  nickname: string
  avatarUrl: string
  role: UserRole
  status: UserStatus
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref<UserInfo>({
    userId: null,
    username: '',
    email: '',
    nickname: '',
    avatarUrl: '',
    role: null,
    status: null,
  })

  const accessToken = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const unreadMessageCount = ref<number>(0)

  // 计算属性
  const isLoggedIn = computed(() => !!accessToken.value && !!userInfo.value.userId)
  const isTeacher = computed(() => userInfo.value.role === 'teacher')
  const isAdmin = computed(() => userInfo.value.role === 'admin')
  const isPendingTeacher = computed(() => userInfo.value.status === 'pending' && userInfo.value.role === 'teacher')

  // 设置用户信息
  function setUserInfo(info: Partial<UserInfo>) {
    Object.assign(userInfo.value, info)
    if (info.userId) {
      localStorage.setItem('user_info', JSON.stringify(userInfo.value))
    }
  }

  // 设置Token
  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  // 设置未读消息数
  function setUnreadCount(count: number) {
    unreadMessageCount.value = count
  }

  // 从localStorage恢复用户信息
  function restoreFromStorage() {
    const storedUserInfo = localStorage.getItem('user_info')
    if (storedUserInfo) {
      try {
        const parsed = JSON.parse(storedUserInfo)
        Object.assign(userInfo.value, parsed)
      } catch {
        // 解析失败，忽略
      }
    }
    const storedAccessToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    if (storedAccessToken) accessToken.value = storedAccessToken
    if (storedRefreshToken) refreshToken.value = storedRefreshToken
  }

  // 登出
  function logout() {
    userInfo.value = {
      userId: null,
      username: '',
      email: '',
      nickname: '',
      avatarUrl: '',
      role: null,
      status: null,
    }
    accessToken.value = ''
    refreshToken.value = ''
    unreadMessageCount.value = 0
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('edu_remember_login_id')
  }

  // 设置登录信息（登录/注册成功后调用）
  interface LoginInfo {
    user_id: number
    username: string
    email: string
    nickname?: string
    avatar_url?: string
    role: UserRole
    status?: UserStatus
    access_token: string
    refresh_token: string
  }

  function setLoginInfo(data: LoginInfo) {
    // 设置用户信息
    userInfo.value = {
      userId: data.user_id,
      username: data.username,
      email: data.email,
      nickname: data.nickname || data.username,
      avatarUrl: data.avatar_url || '',
      role: data.role,
      status: data.status || 'active',
    }
    localStorage.setItem('user_info', JSON.stringify(userInfo.value))

    // 设置 Token
    setTokens(data.access_token, data.refresh_token)
  }

  // 初始化时恢复状态
  restoreFromStorage()

  return {
    userInfo,
    accessToken,
    refreshToken,
    unreadMessageCount,
    isLoggedIn,
    isTeacher,
    isAdmin,
    isPendingTeacher,
    setUserInfo,
    setTokens,
    setUnreadCount,
    setLoginInfo,
    logout,
    restoreFromStorage,
  }
})