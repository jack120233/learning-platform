import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchMyPermissions } from '@/api/profile'

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

type UserInfoInput = Partial<UserInfo> & {
  user_id?: unknown
  avatar_url?: unknown
}

const STORAGE_KEYS = {
  accessToken: 'access_token',
  refreshToken: 'refresh_token',
  userInfo: 'user_info',
  permissionCodes: 'permission_codes',
  rememberedLoginId: 'edu_remember_login_id',
} as const

const EMPTY_USER_INFO: UserInfo = {
  userId: null,
  username: '',
  email: '',
  nickname: '',
  avatarUrl: '',
  role: null,
  status: null,
}

const ADMIN_ENTRY_PERMISSION_CODES = [
  'admin',
  'admin.user',
  'admin.teacher_audit',
  'admin.admin_application',
  'admin.announcement',
  'admin.feedback',
  'admin.message',
  'admin.category',
  'admin.tag',
]

function normalizePermissionCodes(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }

  return Array.from(
    new Set(
      value
        .filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
        .map(item => item.trim())
    )
  ).sort()
}

function normalizeUserId(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }

  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }

  return null
}

function normalizeString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function normalizeRole(value: unknown): UserRole {
  return value === 'student' || value === 'teacher' || value === 'admin' ? value : null
}

function normalizeStatus(value: unknown): UserStatus {
  return value === 'active' || value === 'disabled' || value === 'pending' ? value : null
}

function normalizeUserInfo(info?: UserInfoInput | null): UserInfo {
  const userId = normalizeUserId(info?.userId ?? info?.user_id)
  const username = normalizeString(info?.username)

  return {
    userId,
    username,
    email: normalizeString(info?.email),
    nickname: normalizeString(info?.nickname) || username,
    avatarUrl: normalizeString(info?.avatarUrl ?? info?.avatar_url ?? (info as any)?.avatar),
    role: normalizeRole(info?.role),
    status: normalizeStatus(info?.status),
  }
}

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UserInfo>({ ...EMPTY_USER_INFO })
  const accessToken = ref<string>(localStorage.getItem(STORAGE_KEYS.accessToken) || '')
  const refreshToken = ref<string>(localStorage.getItem(STORAGE_KEYS.refreshToken) || '')
  const permissionCodes = ref<string[]>([])
  const permissionsLoaded = ref(false)
  const permissionsLoading = ref(false)
  const unreadMessageCount = ref<number>(0)
  let permissionLoadPromise: Promise<string[]> | null = null

  const isLoggedIn = computed(() => !!accessToken.value && !!userInfo.value.userId)
  const isStudent = computed(() => userInfo.value.role === 'student')
  const isTeacher = computed(() => userInfo.value.role === 'teacher')
  const isAdmin = computed(() => userInfo.value.role === 'admin')
  const isPendingTeacher = computed(() => userInfo.value.status === 'pending' && userInfo.value.role === 'teacher')
  const canAccessTeacherCenter = computed(() => hasPermission('teacher.course'))
  const canAccessAdminCenter = computed(() => hasAnyPermission(ADMIN_ENTRY_PERMISSION_CODES))

  function persistUserInfo() {
    localStorage.setItem(STORAGE_KEYS.userInfo, JSON.stringify(userInfo.value))
  }

  function persistPermissionCodes() {
    localStorage.setItem(STORAGE_KEYS.permissionCodes, JSON.stringify(permissionCodes.value))
  }

  function setUserInfo(info: Partial<UserInfo>) {
    userInfo.value = normalizeUserInfo({ ...userInfo.value, ...info })
    persistUserInfo()
  }

  function setPermissionCodes(codes: string[]) {
    permissionCodes.value = normalizePermissionCodes(codes)
    permissionsLoaded.value = true
    persistPermissionCodes()
  }

  function clearPermissionCodes(removeStorage = true) {
    permissionCodes.value = []
    permissionsLoaded.value = false
    permissionsLoading.value = false
    permissionLoadPromise = null

    if (removeStorage) {
      localStorage.removeItem(STORAGE_KEYS.permissionCodes)
    }
  }

  function hasPermission(code: string) {
    return permissionCodes.value.includes(code)
  }

  function hasAnyPermission(codes: string[]) {
    return codes.some(code => hasPermission(code))
  }

  async function loadMyPermissions(force = false) {
    if (!isLoggedIn.value) {
      clearPermissionCodes()
      return []
    }

    if (!force && permissionsLoaded.value) {
      return permissionCodes.value
    }

    if (permissionLoadPromise) {
      return permissionLoadPromise
    }

    permissionsLoading.value = true
    permissionLoadPromise = fetchMyPermissions()
      .then((codes) => {
        setPermissionCodes(codes)
        return permissionCodes.value
      })
      .catch((error) => {
        permissionsLoaded.value = permissionCodes.value.length > 0
        throw error
      })
      .finally(() => {
        permissionsLoading.value = false
        permissionLoadPromise = null
      })

    return permissionLoadPromise
  }

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh

    if (access) {
      localStorage.setItem(STORAGE_KEYS.accessToken, access)
    } else {
      localStorage.removeItem(STORAGE_KEYS.accessToken)
    }

    if (refresh) {
      localStorage.setItem(STORAGE_KEYS.refreshToken, refresh)
    } else {
      localStorage.removeItem(STORAGE_KEYS.refreshToken)
    }
  }

  function setUnreadCount(count: number) {
    unreadMessageCount.value = count
  }

  function restoreFromStorage() {
    const storedUserInfo = localStorage.getItem(STORAGE_KEYS.userInfo)
    if (storedUserInfo) {
      try {
        userInfo.value = normalizeUserInfo(JSON.parse(storedUserInfo) as UserInfoInput)
        persistUserInfo()
      } catch {
        userInfo.value = { ...EMPTY_USER_INFO }
        localStorage.removeItem(STORAGE_KEYS.userInfo)
      }
    } else {
      userInfo.value = { ...EMPTY_USER_INFO }
    }

    accessToken.value = localStorage.getItem(STORAGE_KEYS.accessToken) || ''
    refreshToken.value = localStorage.getItem(STORAGE_KEYS.refreshToken) || ''

    const storedPermissionCodes = localStorage.getItem(STORAGE_KEYS.permissionCodes)
    if (storedPermissionCodes) {
      try {
        permissionCodes.value = normalizePermissionCodes(JSON.parse(storedPermissionCodes) as unknown)
        permissionsLoaded.value = permissionCodes.value.length > 0
      } catch {
        clearPermissionCodes()
      }
    } else {
      clearPermissionCodes(false)
    }

    if (!accessToken.value || !userInfo.value.userId) {
      clearPermissionCodes()
      return
    }

    void loadMyPermissions()
  }

  function logout() {
    userInfo.value = { ...EMPTY_USER_INFO }
    accessToken.value = ''
    refreshToken.value = ''
    unreadMessageCount.value = 0
    clearPermissionCodes()
    localStorage.removeItem(STORAGE_KEYS.accessToken)
    localStorage.removeItem(STORAGE_KEYS.refreshToken)
    localStorage.removeItem(STORAGE_KEYS.userInfo)
    localStorage.removeItem(STORAGE_KEYS.permissionCodes)
    localStorage.removeItem(STORAGE_KEYS.rememberedLoginId)
  }

  function setLoginInfo(data: LoginInfo) {
    userInfo.value = normalizeUserInfo({
      user_id: data.user_id,
      username: data.username,
      email: data.email,
      nickname: data.nickname,
      avatar_url: data.avatar_url,
      role: data.role,
      status: data.status || 'active',
    })
    persistUserInfo()
    clearPermissionCodes()
    setTokens(data.access_token, data.refresh_token)
  }

  restoreFromStorage()

  return {
    userInfo,
    accessToken,
    refreshToken,
    permissionCodes,
    permissionsLoaded,
    permissionsLoading,
    unreadMessageCount,
    isLoggedIn,
    isStudent,
    isTeacher,
    isAdmin,
    isPendingTeacher,
    canAccessTeacherCenter,
    canAccessAdminCenter,
    setUserInfo,
    setPermissionCodes,
    setTokens,
    setUnreadCount,
    setLoginInfo,
    logout,
    restoreFromStorage,
    clearPermissionCodes,
    hasPermission,
    hasAnyPermission,
    loadMyPermissions,
  }
})
