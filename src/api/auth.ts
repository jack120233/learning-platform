import request from './index'

// ==================== 类型定义 ====================

/** 注册请求参数 */
export interface RegisterRequest {
  username: string
  email: string
  phone: string
  password: string
  confirm_password: string
  role: 'student' | 'teacher' | 'admin'
  captcha: string
  captcha_id: string
  email_code: string
  referrer_email?: string
}

/** 注册响应 */
export interface RegisterResponse {
  user_id: number
  username: string
  email: string
  role: string
  status: 'active' | 'pending'
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

/** 登录请求参数 */
export interface LoginRequest {
  username: string
  password: string
  remember_me: boolean
}

/** 登录响应中的用户信息 */
export interface LoginUser {
  id: number
  username: string
  email: string
  nickname: string
  avatar: string | null
  role: 'student' | 'teacher' | 'admin'
  status: 'active' | 'pending' | 'disabled'
  created_at: string
}

/** 登录响应 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: LoginUser
}

/** 图形验证码响应 */
export interface CaptchaResponse {
  captcha_id: string
  captcha_image: string // Base64 data URL
}

/** 发送邮箱验证码请求 */
export interface SendEmailCodeRequest {
  email: string
  purpose: 'register' | 'reset_password'
}

/** 发送邮箱验证码响应 */
export interface SendEmailCodeResponse {
  expires_in: number // 秒
}

/** 密码重置请求参数 */
export interface ResetPasswordRequest {
  username: string
  email_code: string
  new_password: string
  confirm_password: string
}

/** 刷新令牌请求 */
export interface RefreshTokenRequest {
  refresh_token: string
}

/** 刷新令牌响应 */
export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// ==================== API 函数 ====================

/**
 * 用户登录
 */
export function login(data: LoginRequest): Promise<LoginResponse> {
  return request.post('/auth/login', data)
}

/**
 * 用户注册
 */
export function register(data: RegisterRequest): Promise<RegisterResponse> {
  return request.post('/auth/register', data)
}

/**
 * 获取图形验证码
 */
export function getCaptcha(): Promise<CaptchaResponse> {
  return request.get('/auth/captcha')
}

/**
 * 发送邮箱验证码
 */
export function sendEmailCode(data: SendEmailCodeRequest): Promise<SendEmailCodeResponse> {
  return request.post('/auth/send-email-code', data)
}

/**
 * 密码重置
 */
export function resetPassword(data: ResetPasswordRequest): Promise<void> {
  return request.post('/auth/reset-password', data)
}

/**
 * 刷新令牌
 */
export function refreshToken(data: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  return request.post('/auth/refresh', data)
}

/**
 * 退出登录
 */
export function logout(): Promise<void> {
  return request.post('/auth/logout')
}