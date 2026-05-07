# 个人中心模块与反馈提交功能实施计划

## 概述
- **方案**：方案 B - 状态保持的高交互流（keep-alive 缓存列表页）
- **参考文档**：
  - `前端页面详细设计说明书-6.7-个人中心.md`
  - `前端页面详细设计说明书-6.8-反馈提交.md`

## 实施清单

### 阶段 1：基础设施层

#### 1.1 API 接口层 (`src/api/profile.ts`)
```typescript
// 用户信息
fetchProfile()                    // GET /users/me
updateProfile(data)               // POST /users/me
changePassword(data)              // POST /users/me/change-password
sendEmailCode(data)               // POST /auth/send-email-code

// 学习记录
fetchLearningRecords(params)      // GET /users/me/learning-records

// 消息中心
fetchMessages(params)             // GET /messages
fetchMessageDetail(id)            // GET /messages/{id}
markAsRead(id)                    // POST /messages/{id}/read
markAllRead()                     // POST /messages/mark-all-read
deleteMessage(id)                 // POST /messages/{id}
fetchUnreadCount()                // GET /messages/unread-count

// 反馈
fetchMyFeedbacks(params)          // GET /users/me/feedbacks
```

#### 1.2 可复用 Composables
- `src/composables/usePagination.ts` - 分页逻辑
- `src/composables/usePasswordStrength.ts` - 密码强度校验

---

### 阶段 2：布局与路由

#### 2.1 ProfileLayout.vue
- 左侧菜单 220px（el-menu + router 模式）
- 右侧内容区（keep-alive 缓存 records、messages 页面）
- 未读消息 Badge 集成

#### 2.2 路由配置更新
```typescript
{
  path: '/profile',
  component: ProfileLayout,
  meta: { requiresAuth: true },
  children: [
    { path: '', name: 'Profile', component: ProfileInfoPage },
    { path: 'password', name: 'ProfilePassword', component: ChangePasswordPage },
    { path: 'records', name: 'ProfileRecords', component: LearningRecordsPage },
    { path: 'messages', name: 'ProfileMessages', component: MessagesPage },
    { path: 'feedbacks', name: 'ProfileFeedbacks', component: MyFeedbacksPage },
  ]
}
```

---

### 阶段 3：子页面实现

#### 3.1 ProfileInfoPage.vue - 个人基本信息
- 头像上传（el-upload + uploadFile API）
- 只读信息展示（用户名、角色、状态、注册时间）
- 可编辑表单（昵称、邮箱、手机号）
- 邮箱修改需验证码（useCountdown）

#### 3.2 ChangePasswordPage.vue - 修改密码
- 表单验证（原密码、新密码、确认密码）
- 密码强度指示器（usePasswordStrength）
- 成功后强制重新登录

#### 3.3 LearningRecordsPage.vue - 学习记录
- 时间范围筛选（近7天/近30天/全部）
- 记录卡片列表（封面、课程名、上次学习、继续学习按钮）
- 课程下架状态处理
- 分页组件

#### 3.4 MessagesPage.vue - 消息中心
- 类型筛选（全部/系统通知/公告）
- 状态筛选（全部/未读/已读）
- 消息卡片列表（未读标记、类型标签、标题、摘要、时间）
- 详情抽屉（MessageDetailDrawer）
- 批量已读、删除功能

#### 3.5 MyFeedbacksPage.vue - 我的反馈
- 反馈卡片列表（类型、内容、图片预览、状态、关联课程）
- 图片预览（el-image preview）
- 分页组件

---

### 阶段 4：反馈组件

#### 4.1 FeedbackForm.vue - 反馈表单核心组件
**Props:**
- `mode: 'inline' | 'dialog'`
- `defaultType?: 'system' | 'course'`
- `typeLocked?: boolean`
- `courseId?: number`
- `courseName?: string`

**功能:**
- 反馈类型选择（系统问题/课程问题）
- 关联课程展示（课程问题时）
- 内容输入（10-500字符）
- 图片上传（最多8张，JPG/PNG，5MB限制）

#### 4.2 FeedbackDialog.vue - 反馈弹窗封装
- el-dialog 包裹 FeedbackForm
- v-model:visible 控制显示

---

## 文件清单

### 新建文件
```
src/api/profile.ts
src/composables/usePagination.ts
src/composables/usePasswordStrength.ts
src/views/profile/ProfileLayout.vue
src/views/profile/ProfileInfoPage.vue
src/views/profile/ChangePasswordPage.vue
src/views/profile/LearningRecordsPage.vue
src/views/profile/MessagesPage.vue
src/views/profile/MyFeedbacksPage.vue
src/components/feedback/FeedbackForm.vue
src/components/feedback/FeedbackDialog.vue
```

### 修改文件
```
src/router/index.ts          # 更新路由配置
src/store/user.ts            # 新增方法（可选）
```

### 删除文件
```
src/views/profile/ProfilePage.vue  # 替换为 ProfileLayout
```