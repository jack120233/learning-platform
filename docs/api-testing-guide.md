# API 接口手动测试指南

## 目录

1. [准备工作](#1-准备工作)
2. [启动服务](#2-启动服务)
3. [认证流程](#3-认证流程)
4. [各模块接口测试](#4-各模块接口测试)
5. [常见问题](#5-常见问题)

---

## 1. 准备工作

### 1.1 推荐工具

| 工具 | 说明 | 下载地址 |
|------|------|---------|
| **Apifox** | 国产神器，推荐使用 | https://apifox.com |
| Postman | 国际主流工具 | https://www.postman.com |
| curl | 命令行工具 | 系统自带 |

### 1.2 基础信息

```
服务地址: http://localhost:8000
API文档: http://localhost:8000/docs
API文档(备): http://localhost:8000/redoc
```

---

## 2. 启动服务

### 2.1 启动后端服务

```bash
# 进入项目目录
cd E:\video_project\project_code\backend

# 激活虚拟环境
..\\.venv\Scripts\activate

# 启动服务
uvicorn app.main:app --reload --port 8000
```

启动成功后看到：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2.2 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

这是 FastAPI 自带的交互式 API 文档，可以直接在网页上测试接口！

---

## 3. 认证流程

### 3.1 获取验证码（第一步）

**接口**: `GET /api/v1/auth/captcha`

**请求示例**:
```
GET http://localhost:8000/api/v1/auth/captcha
```

**响应示例**:
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "captcha_key": "abc123...",
    "captcha_image": "data:image/svg+xml;base64,..."
  }
}
```

**操作步骤**:
1. 复制 `captcha_key` 值
2. 打开 `captcha_image` 的链接（或在浏览器新标签页打开base64内容）
3. 查看验证码图片上的文字

> ⚠️ 注意：测试环境验证码图片中显示的文字就是验证码内容

### 3.2 发送邮箱验证码（注册用）

**接口**: `POST /api/v1/auth/send-email-code`

**请求体**:
```json
{
  "email": "test@example.com",
  "purpose": "register",
  "captcha_key": "上一步获取的captcha_key",
  "captcha_text": "验证码文字"
}
```

### 3.3 用户注册

**接口**: `POST /api/v1/auth/register`

**请求体**:
```json
{
  "username": "mytest",
  "email": "test@example.com",
  "password": "Test123456",
  "captcha_key": "验证码key",
  "captcha_text": "验证码",
  "role": "student"
}
```

**密码要求**: 至少6位，必须包含大写字母或数字

### 3.4 用户登录

**接口**: `POST /api/v1/auth/login`

**请求体**:
```json
{
  "username": "mytest",
  "password": "Test123456",
  "captcha_key": "验证码key",
  "captcha_text": "验证码",
  "remember_me": false
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "mytest",
      "email": "test@example.com",
      "role": "student"
    }
  }
}
```

**重要**: 复制 `access_token`，后续所有需要认证的接口都要用到！

### 3.5 使用 Token

在需要认证的接口请求头中添加：

```
Authorization: Bearer <你的access_token>
```

---

## 4. 各模块接口测试

### 4.1 用户模块

#### 获取当前用户信息

```
GET /api/v1/users/me
Headers: Authorization: Bearer <token>
```

#### 更新个人信息

```
POST /api/v1/users/me
Headers: Authorization: Bearer <token>
Body:
{
  "nickname": "我的昵称",
  "avatar": "头像URL"
}
```

#### 修改密码

```
POST /api/v1/users/me/change-password
Headers: Authorization: Bearer <token>
Body:
{
  "old_password": "Test123456",
  "new_password": "NewTest123"
}
```

---

### 4.2 课程模块

#### 获取课程列表（无需登录）

```
GET /api/v1/courses?page=1&page_size=10
```

#### 搜索课程

```
GET /api/v1/courses/search?keyword=Python
```

#### 创建课程（需要讲师权限）

```
POST /api/v1/courses
Headers: Authorization: Bearer <讲师token>
Body:
{
  "title": "我的第一门课",
  "subtitle": "课程副标题",
  "description": "课程描述",
  "category_id": 1,
  "price": 99.0,
  "level": "beginner"
}
```

#### 获取课程详情

```
GET /api/v1/courses/{课程ID}
```

---

### 4.3 课程内容模块

#### 获取章节列表

```
GET /api/v1/courses/{课程ID}/chapters
```

#### 创建章节

```
POST /api/v1/courses/{课程ID}/chapters
Headers: Authorization: Bearer <讲师token>
Body:
{
  "title": "第一章",
  "sort_order": 1
}
```

#### 获取小节列表

```
GET /api/v1/courses/{课程ID}/chapters/{章节ID}/sections
```

---

### 4.4 学习模块

#### 开始学习

```
POST /api/v1/learning/courses/{课程ID}/start
Headers: Authorization: Bearer <token>
```

#### 获取学习进度

```
GET /api/v1/learning/progress
Headers: Authorization: Bearer <token>
```

---

### 4.5 反馈模块

#### 提交反馈

```
POST /api/v1/feedbacks
Headers: Authorization: Bearer <token>
Body:
{
  "type": "suggestion",
  "title": "功能建议",
  "content": "希望能添加..."
}
```

#### 获取我的反馈列表

```
GET /api/v1/feedbacks
Headers: Authorization: Bearer <token>
```

---

### 4.6 消息模块

#### 获取消息列表

```
GET /api/v1/messages
Headers: Authorization: Bearer <token>
```

#### 获取未读数量

```
GET /api/v1/messages/unread-count
Headers: Authorization: Bearer <token>
```

#### 全部标记已读

```
POST /api/v1/messages/mark-all-read
Headers: Authorization: Bearer <token>
```

---

### 4.7 系统模块

#### 获取分类列表（无需登录）

```
GET /api/v1/categories
```

#### 获取标签列表（无需登录）

```
GET /api/v1/tags
```

#### 获取公告列表（无需登录）

```
GET /api/v1/announcements
```

---

## 5. Apifox 使用教程

### 5.1 创建项目

1. 打开 Apifox，点击「新建项目」
2. 项目名称：在线学习平台
3. 点击「确定」

### 5.2 导入接口

1. 点击「项目设置」→「导入数据」
2. 选择「OpenAPI/Swagger」
3. 输入地址：`http://localhost:8000/openapi.json`
4. 点击「确定导入」

### 5.3 设置全局认证

1. 点击「环境管理」→「全局参数」
2. 添加请求头参数：
   - 参数名：`Authorization`
   - 参数值：`Bearer {{access_token}}`
3. 保存

### 5.4 测试流程

1. 先调用「获取验证码」接口
2. 再调用「登录」接口
3. 将返回的 `access_token` 填入全局参数
4. 后续接口会自动带上认证信息

---

## 6. 使用 curl 命令测试

### 6.1 获取验证码

```bash
curl -X GET "http://localhost:8000/api/v1/auth/captcha"
```

### 6.2 登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mytest",
    "password": "Test123456",
    "captcha_key": "你的验证码key",
    "captcha_text": "验证码"
  }'
```

### 6.3 获取用户信息

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer 你的token"
```

---

## 7. 常见问题

### Q1: 提示 "验证码无效"

**原因**: 验证码过期或输入错误

**解决**: 重新调用获取验证码接口

### Q2: 提示 "未授权访问"

**原因**: 没有登录或 token 过期

**解决**:
1. 确认请求头带了 `Authorization: Bearer <token>`
2. 重新登录获取新 token

### Q3: 提示 "无权访问"

**原因**: 权限不足

**解决**:
- 学生账号只能访问学生权限的接口
- 讲师账号可以访问讲师权限的接口
- 管理员可以访问所有接口

### Q4: 422 错误

**原因**: 请求参数格式不对

**解决**:
1. 检查请求体格式是否正确
2. 检查必填字段是否都填了
3. 查看响应中的 `details` 字段了解具体错误

### Q5: 服务器内部错误 500

**原因**: 后端代码问题

**解决**: 查看终端的日志输出

---

## 8. 测试账号

如果数据库中有测试数据，可以使用以下账号：

| 角色 | 用户名 | 密码 |
|------|-------|------|
| 学生 | testuser | Test123456 |
| 讲师 | testteacher | Teacher123456 |
| 管理员 | testadmin | Admin123456 |

---

## 9. 快速测试清单

按顺序测试以下流程：

### 9.1 完整注册流程
- [ ] 获取验证码
- [ ] 发送邮箱验证码
- [ ] 用户注册
- [ ] 用户登录

### 9.2 用户管理流程
- [ ] 获取当前用户信息
- [ ] 更新个人信息
- [ ] 获取学习记录

### 9.3 课程浏览流程
- [ ] 获取课程列表
- [ ] 搜索课程
- [ ] 获取课程详情
- [ ] 获取章节列表

### 9.4 学习流程
- [ ] 开始学习
- [ ] 保存进度
- [ ] 获取进度

### 9.5 反馈消息流程
- [ ] 提交反馈
- [ ] 获取消息列表
- [ ] 获取未读数量

---

**祝你测试顺利！有问题随时问~**