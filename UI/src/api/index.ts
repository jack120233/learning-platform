import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

declare module 'axios' {
  interface AxiosRequestConfig {
    skipErrorMessage?: boolean
    _retry?: boolean
  }

  interface InternalAxiosRequestConfig {
    skipErrorMessage?: boolean
    _retry?: boolean
  }
}

// API响应结构
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 分页响应结构
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token刷新状态
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

// 订阅Token刷新
function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

// 通知所有订阅者
function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token))
  refreshSubscribers = []
}

function shouldShowErrorMessage(config?: { skipErrorMessage?: boolean }) {
  return !config?.skipErrorMessage
}

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    if (response.config.responseType === 'blob') {
      return response.data as any
    }

    const { code, message, data } = response.data

    if (code === 200) {
      return data as any
    }

    // 业务错误
    if (shouldShowErrorMessage(response.config)) {
      ElMessage.error(message || '请求失败')
    }
    return Promise.reject(new Error(message || '请求失败'))
  },
  async (error) => {
    const { response, config } = error

    if (response?.status === 401 && !config._retry) {
      config._retry = true

      if (!isRefreshing) {
        isRefreshing = true
        try {
          const refreshToken = localStorage.getItem('refresh_token')
          if (!refreshToken) {
            throw new Error('无刷新令牌')
          }

          const res = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })

          const { access_token } = res.data.data
          localStorage.setItem('access_token', access_token)

          onTokenRefreshed(access_token)
          isRefreshing = false

          // 重试原请求
          if (config.headers) {
            config.headers.Authorization = `Bearer ${access_token}`
          }
          return service(config)
        } catch (refreshError) {
          // 刷新失败，清除登录态
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_info')
          localStorage.removeItem('permission_codes')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }

      // 正在刷新，等待刷新完成
      return new Promise((resolve) => {
        subscribeTokenRefresh((token) => {
          if (config.headers) {
            config.headers.Authorization = `Bearer ${token}`
          }
          resolve(service(config))
        })
      })
    }

    // 其他错误
    const errorMessage = response?.data?.message || '网络错误，请稍后重试'
    error.message = errorMessage
    if (shouldShowErrorMessage(config)) {
      ElMessage.error(errorMessage)
    }
    return Promise.reject(error)
  }
)

export default service
