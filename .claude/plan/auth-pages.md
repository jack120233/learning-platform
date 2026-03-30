# 认证页面实现计划

> 创建时间：2026-03-25
> 任务：实现注册页、登录页、找回密码页

## 实施顺序

按照 Gemini 建议的 **登录 → 找回密码 → 注册** 顺序，从简单到复杂。

---

## Phase 1: 基础设施（共用组件和工具）

### 1.1 AuthLayout.vue - 认证页通用布局
- 路径：`src/layouts/AuthLayout.vue`
- 功能：
  - 左侧品牌区（Logo + 标语 + 背景渐变）
  - 右侧表单区（slot）
  - 响应式：≥1280px 分栏，<1280px 隐藏品牌区

### 1.2 useCountdown.ts - 倒计时 Composable
- 路径：`src/composables/useCountdown.ts`
- 功能：
  - 返回 `{ countdown, isActive, start, stop }`
  - 组件卸载时自动清理

### 1.3 auth.ts - 认证相关 API
- 路径：`src/api/auth.ts`
- 接口：
  - `login(data)` - 登录
  - `register(data)` - 注册
  - `getCaptcha()` - 获取图形验证码
  - `sendEmailCode(data)` - 发送邮箱验证码
  - `resetPassword(data)` - 密码重置

### 1.4 validators.ts - 表单校验规则
- 路径：`src/utils/validators.ts`
- 功能：
  - 密码校验规则（8-20位，字母+数字）
  - 手机号校验规则
  - 邮箱校验规则
  - 用户名校验规则

### 1.5 format.ts - 格式化工具函数
- 路径：`src/utils/format.ts`
- 功能：
  - `maskEmail(email)` - 邮箱脱敏

---

## Phase 2: 登录页实现

### 2.1 LoginPage.vue
- 路径：`src/views/auth/LoginPage.vue`
- 功能：
  - 使用 AuthLayout
  - 登录方式 Tab 切换（邮箱/手机号）
  - 账号、密码输入
  - 记住我 checkbox
  - 忘记密码链接
  - 登录按钮 + loading 状态
  - 注册链接

### 2.2 路由更新
- 已登录用户访问登录页 → 重定向到首页
- 登录成功后角色跳转逻辑

### 2.3 UserStore 扩展
- 添加 `setLoginInfo(data)` 方法

---

## Phase 3: 找回密码页实现

### 3.1 ForgotPasswordPage.vue
- 路径：`src/views/auth/ForgotPasswordPage.vue`
- 功能：
  - 使用 AuthLayout
  - 步骤条（验证身份 → 输入验证码 → 设置新密码 → 成功）
  - 邮箱/手机号找回切换
  - 验证码发送 + 倒计时
  - 新密码设置 + 确认
  - 成功结果页

### 3.2 路由添加
- 路由：`/forgot-password`
- 公开页面，已登录用户重定向

---

## Phase 4: 注册页实现

### 4.1 RegisterPage.vue
- 路径：`src/views/auth/RegisterPage.vue`
- 功能：
  - 使用 AuthLayout
  - 角色选择器（学员/讲师/管理员）
  - 用户名、密码、确认密码
  - 手机号、邮箱
  - 图形验证码（点击刷新，4s 冷却）
  - 邮箱验证码（60s 倒计时）
  - 推荐管理员邮箱（管理员专用）
  - 讲师审核中弹窗

### 4.2 路由守卫更新
- 已登录用户访问注册页 → 重定向到首页

---

## 文件清单

### 新建文件
| 文件路径 | 说明 |
|---------|------|
| `src/layouts/AuthLayout.vue` | 认证页通用布局 |
| `src/composables/useCountdown.ts` | 倒计时 Composable |
| `src/api/auth.ts` | 认证 API |
| `src/utils/validators.ts` | 表单校验规则 |
| `src/utils/format.ts` | 格式化工具函数 |
| `src/views/auth/ForgotPasswordPage.vue` | 找回密码页 |

### 修改文件
| 文件路径 | 说明 |
|---------|------|
| `src/views/auth/LoginPage.vue` | 完整实现登录页 |
| `src/views/auth/RegisterPage.vue` | 完整实现注册页 |
| `src/store/user.ts` | 添加 setLoginInfo 方法 |
| `src/router/index.ts` | 添加找回密码路由、更新守卫 |

---

## 验收标准

1. **功能完整性**：所有设计文档中的功能均已实现
2. **响应式布局**：≥1280px 分栏，<1280px 居中表单
3. **表单校验**：所有字段校验规则正确
4. **交互流程**：验证码倒计时、步骤跳转等正常工作
5. **风格一致性**：与现有页面风格保持一致