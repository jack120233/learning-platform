# 实际已挂载 API 接口清单

## 1. 文档目的

本文档仅用于盘点当前后端**已经挂载并可调用**的 FastAPI 业务接口，供前后端逐项核对。

## 2. 统计口径

### 2.1 事实来源

- 应用挂载入口：`backend/app/main.py:87-88`
- 统一前缀来源：`backend/app/config.py:33-35`
- v1 路由聚合：`backend/app/api/v1/router.py:17-27`
- 认证判定依据：`backend/app/core/dependencies.py:61-163`
- 统一响应包装：`backend/app/schemas/common.py:15-75`

### 2.2 纳入范围

仅统计 `backend/app/api/v1/router.py:17-27` 中实际 `include_router(...)` 挂载的 12 个业务模块：

- 健康检查
- 用户认证
- 分类管理
- 标签管理
- 公告管理
- 用户管理
- 课程管理
- 文件上传
- 课程内容
- 学习模块
- 反馈管理
- 消息管理

### 2.3 不纳入范围

以下接口或文档端点不计入业务接口总数：

- `GET /`
- `/docs`
- `/redoc`
- `/openapi.json`

### 2.4 认证判定规则

- 使用 `CurrentUserId`：需要 `Bearer Token`
- 使用 `OptionalUserId`：可选登录
- 未使用认证依赖：无需登录

当前已挂载的 v1 业务路由中，**未发现 `OptionalUserId` 用例**。

## 3. 当前总览

### 3.1 总体统计

- 已挂载业务模块：**12 个**
- 已挂载业务接口：**81 个**
- 公共接口：**24 个**
- 需登录接口：**57 个**

### 3.2 模块总览表

| 模块 | 接口数 | 公开接口 | 需登录接口 | 主要路由文件 | 对应测试文件 |
|---|---:|---:|---:|---|---|
| 健康检查 | 2 | 2 | 0 | `backend/app/api/v1/health.py` | `backend/tests/test_health.py` |
| 用户认证 | 7 | 6 | 1 | `backend/app/api/v1/auth.py` | `backend/tests/test_auth.py` |
| 分类管理 | 4 | 4 | 0 | `backend/app/api/v1/categories.py` | `backend/tests/test_system.py` |
| 标签管理 | 2 | 2 | 0 | `backend/app/api/v1/tags.py` | `backend/tests/test_system.py` |
| 公告管理 | 3 | 3 | 0 | `backend/app/api/v1/announcements.py` | `backend/tests/test_system.py` |
| 用户管理 | 11 | 0 | 11 | `backend/app/api/v1/users.py` | `backend/tests/test_users.py` |
| 课程管理 | 13 | 5 | 8 | `backend/app/api/v1/courses.py` | `backend/tests/test_courses.py` |
| 文件上传 | 6 | 0 | 6 | `backend/app/api/v1/uploads.py` | `backend/tests/test_uploads.py` |
| 课程内容 | 17 | 2 | 15 | `backend/app/api/v1/content.py` | `backend/tests/test_content.py` |
| 学习模块 | 6 | 0 | 6 | `backend/app/api/v1/learning.py` | `backend/tests/test_learning.py` |
| 反馈管理 | 4 | 0 | 4 | `backend/app/api/v1/feedbacks.py` | `backend/tests/test_feedbacks.py` |
| 消息管理 | 7 | 0 | 7 | `backend/app/api/v1/messages.py` | `backend/tests/test_feedbacks.py` |

### 3.3 统计复核

```text
2 + 7 + 4 + 2 + 3 + 11 + 13 + 6 + 17 + 6 + 4 + 7 = 82
```

## 4. 特殊说明

### 4.1 路由层权限与说明文案不是一回事

多个接口的 `summary` 或 `description` 写有“管理员权限”“讲师权限”等表述，但在路由层只看到了 `CurrentUserId` 依赖，**未见显式角色 RBAC 依赖**。因此本文档会区分：

- **登录要求**：按依赖注入代码直接判定
- **权限备注**：保留描述文本中的角色语义，并明确标注“路由层未见显式 RBAC”

### 4.2 存在用 `POST` 承担更新/删除/状态流转语义的接口

以下类型接口未采用标准 REST 的 `PUT/PATCH/DELETE` 语义，而是使用了 `POST`：

- 用户信息更新：`POST /api/v1/users/me`
- 用户状态变更：`POST /api/v1/users/{target_user_id}/status`
- 用户删除：`POST /api/v1/users/{target_user_id}`
- 课程更新：`POST /api/v1/courses/{course_id}`
- 课程发布/下架：`POST /api/v1/courses/{course_id}/publish`、`POST /api/v1/courses/{course_id}/archive`
- 章节/小节更新：`POST /api/v1/courses/{course_id}/chapters/{chapter_id}`、`POST /api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}`
- 反馈处理：`POST /api/v1/feedbacks/{feedback_id}/process`
- 消息已读/批量已读/发送：`POST /api/v1/messages/{message_id}/read`、`POST /api/v1/messages/mark-all-read`、`POST /api/v1/messages/send`

### 4.3 `content.py` 没有统一模块前缀

`backend/app/api/v1/content.py` 没有像其他模块那样声明统一 `prefix`，而是把路径直接写成 `/courses/...`。由于它仍由 `backend/app/api/v1/router.py:24` 挂载并统一套上 `/api/v1` 前缀，所以最终完整路径仍然属于 `/api/v1/courses/...`。

### 4.4 学习模块中的依赖写法不够一致

`learning.py` 中的 `get_progress` 写法带有 `user_id: CurrentUserId = None` 这样的默认值形式，但本质上仍然使用了 `CurrentUserId` 依赖，因此本文档仍按“需要 Bearer Token”标注。

### 4.5 2026-04-09 教师端资源上传补齐说明

本次后端已补齐教师端页面依赖的以下能力：

- 通用小文件上传：`POST /api/v1/upload/file`
- 大文件分片上传：`POST /api/v1/upload/init`、`POST /api/v1/upload/chunk`、`POST /api/v1/upload/complete`
- 课程资料双模式绑定：`POST /api/v1/courses/{course_id}/materials`
  - 支持 JSON 绑定已上传文件
  - 支持 `multipart/form-data` 直接上传并自动落库
- 章节级资源：`POST /api/v1/courses/{course_id}/chapters/{chapter_id}/resources`
- 旧前端兼容删除路由：
  - `POST /api/v1/courses/{course_id}/materials/{material_id}/delete`
  - `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/delete`
  - `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}/delete`
  - `POST /api/v1/courses/{course_id}/sections/{section_id}/resources/{resource_id}/delete`
  - `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/resources/{resource_id}/delete`

## 5. 接口明细

> 说明：以下每一行都以“HTTP 方法 + 完整路径”为唯一标识；完整路径均已包含 `/api/v1` 前缀。

### 5.1 健康检查

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/health` | 健康检查 | 无需登录 | 无 | 无 | 无 | 无；仅返回 `code/message` | `health_check` | `backend/app/api/v1/health.py:13` | `backend/tests/test_health.py` |
| 2 | GET | `/api/v1/ping` | Ping 连通性检查 | 无需登录 | 无 | 无 | 无 | 无；仅返回 `code/message` | `ping` | `backend/app/api/v1/health.py:25` | `backend/tests/test_health.py` |

### 5.2 用户认证

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | POST | `/api/v1/auth/register` | 用户注册 | 无需登录 | 无 | 无 | `RegisterRequest`：`username`、`email`、`password`、`role`、`captcha_key?`、`captcha_text?` | `auth.UserResponse`：`id`、`username`、`email`、`nickname?`、`avatar?`、`role`、`status`、`created_at` | `register` | `backend/app/api/v1/auth.py:27` | `backend/tests/test_auth.py` |
| 2 | POST | `/api/v1/auth/login` | 用户登录 | 无需登录 | 无 | 无 | `LoginRequest`：`username`、`password`、`remember_me`、`captcha_key?`、`captcha_text?` | `LoginResponse`：`access_token`、`refresh_token`、`token_type`、`expires_in`、`user` | `login` | `backend/app/api/v1/auth.py:53` | `backend/tests/test_auth.py` |
| 3 | POST | `/api/v1/auth/logout` | 退出登录并撤销刷新令牌 | 需要 Bearer Token | 无 | 查询参数：`refresh_token?` | 无 | 无；仅返回 `code/message` | `logout` | `backend/app/api/v1/auth.py:91` | `backend/tests/test_auth.py` |
| 4 | POST | `/api/v1/auth/refresh` | 刷新访问令牌 | 无需登录 | 无 | 无 | `RefreshTokenRequest`：`refresh_token` | `TokenResponse`：`access_token`、`token_type`、`expires_in` | `refresh_token` | `backend/app/api/v1/auth.py:116` | `backend/tests/test_auth.py` |
| 5 | GET | `/api/v1/auth/captcha` | 获取图形验证码 | 无需登录 | 无 | 无 | 无 | `CaptchaResponse`：`captcha_key`、`captcha_image` | `get_captcha` | `backend/app/api/v1/auth.py:142` | `backend/tests/test_auth.py` |
| 6 | POST | `/api/v1/auth/send-email-code` | 发送邮箱验证码 | 无需登录 | 无 | 无 | `SendEmailCodeRequest`：`email`、`purpose`、`captcha_key?`、`captcha_text?` | 无；仅返回 `code/message` | `send_email_code` | `backend/app/api/v1/auth.py:166` | `backend/tests/test_auth.py` |
| 7 | POST | `/api/v1/auth/reset-password` | 通过邮箱验证码重置密码 | 无需登录 | 无 | 无 | `ResetPasswordRequest`：`email`、`code`、`new_password` | 无；仅返回 `code/message` | `reset_password` | `backend/app/api/v1/auth.py:189` | `backend/tests/test_auth.py` |

### 5.3 分类管理

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/categories` | 分类列表 | 无需登录 | 无 | 查询参数：`parent_id?`、`is_active?` | 无 | `list[CategoryResponse]`：`id`、`name`、`slug`、`description?`、`icon?`、`sort_order`、`parent_id?`、`is_active`、`created_at` | `get_categories` | `backend/app/api/v1/categories.py:21` | `backend/tests/test_system.py` |
| 2 | POST | `/api/v1/categories` | 创建分类 | 无需登录 | 无 | 无 | `CategoryCreate`：`name`、`slug`、`description?`、`icon?`、`parent_id?`、`sort_order` | `CategoryResponse` | `create_category` | `backend/app/api/v1/categories.py:43` | `backend/tests/test_system.py` |
| 3 | PUT | `/api/v1/categories/{category_id}` | 更新分类 | 无需登录 | 无 | 路径参数：`category_id` | `CategoryUpdate`：`name?`、`slug?`、`description?`、`icon?`、`parent_id?`、`sort_order?`、`is_active?` | `CategoryResponse` | `update_category` | `backend/app/api/v1/categories.py:61` | `backend/tests/test_system.py` |
| 4 | DELETE | `/api/v1/categories/{category_id}` | 删除分类 | 无需登录 | 无 | 路径参数：`category_id` | 无 | 无；仅返回 `code/message` | `delete_category` | `backend/app/api/v1/categories.py:80` | `backend/tests/test_system.py` |

### 5.4 标签管理

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/tags` | 标签列表 | 无需登录 | 无 | 查询参数：`keyword?`、`page`、`page_size` | 无 | `PageData[TagResponse]`：`items[{id,name,slug,color?,use_count,created_at}]`、`total`、`page`、`page_size`、`total_pages` | `get_tags` | `backend/app/api/v1/tags.py:17` | `backend/tests/test_system.py` |
| 2 | POST | `/api/v1/tags` | 创建标签 | 无需登录 | 无 | 无 | `TagCreate`：`name`、`slug`、`color?` | `TagResponse`：`id`、`name`、`slug`、`color?`、`use_count`、`created_at` | `create_tag` | `backend/app/api/v1/tags.py:46` | `backend/tests/test_system.py` |

### 5.5 公告管理

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/announcements` | 公告列表 | 无需登录 | 无 | 查询参数：`is_published?`、`type?`、`page`、`page_size` | 无 | `PageData[AnnouncementResponse]`：`items[{id,title,content,type,is_top,is_published,publish_at?,expire_at?,view_count,author_id?,created_at}]`、分页信息 | `get_announcements` | `backend/app/api/v1/announcements.py:17` | `backend/tests/test_system.py` |
| 2 | GET | `/api/v1/announcements/active` | 当前有效公告列表 | 无需登录 | 无 | 查询参数：`limit` | 无 | `list[AnnouncementResponse]` | `get_active_announcements` | `backend/app/api/v1/announcements.py:48` | `backend/tests/test_system.py` |
| 3 | GET | `/api/v1/announcements/{announcement_id}` | 公告详情 | 无需登录 | 无 | 路径参数：`announcement_id` | 无 | `AnnouncementResponse` | `get_announcement` | `backend/app/api/v1/announcements.py:65` | `backend/tests/test_system.py` |

### 5.6 用户管理

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/users/me` | 获取当前用户信息 | 需要 Bearer Token | 无 | 无 | 无 | `user.UserResponse`：`id`、`username`、`email`、`phone?`、`nickname?`、`avatar?`、`bio?`、`role`、`status`、`created_at`、`last_login_at?` | `get_current_user` | `backend/app/api/v1/users.py:38` | `backend/tests/test_users.py` |
| 2 | POST | `/api/v1/users/me` | 更新个人信息 | 需要 Bearer Token | 无 | 无 | `UserProfileUpdate`：`nickname?`、`avatar?`、`bio?`、`phone?` | `user.UserResponse` | `update_profile` | `backend/app/api/v1/users.py:53` | `backend/tests/test_users.py` |
| 3 | POST | `/api/v1/users/me/change-password` | 修改当前用户密码 | 需要 Bearer Token | 无 | 无 | `ChangePasswordRequest`：`old_password`、`new_password` | 无；仅返回 `code/message` | `change_password` | `backend/app/api/v1/users.py:72` | `backend/tests/test_users.py` |
| 4 | GET | `/api/v1/users/me/learning-records` | 获取当前用户学习记录 | 需要 Bearer Token | 无 | 查询参数：`page`、`page_size` | 无 | `PageData[LearningRecordResponse]`：`items[{id,course_id,course_name?,progress,total_duration,last_section_id?,completed_at?,created_at,updated_at}]`、分页信息 | `get_learning_records` | `backend/app/api/v1/users.py:93` | `backend/tests/test_users.py` |
| 5 | GET | `/api/v1/users` | 用户列表 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 查询参数：`keyword?`、`role?`、`status?`、`page`、`page_size` | 无 | `PageData[UserListResponse]`：`items[{id,username,email,nickname?,role,status,created_at,last_login_at?}]`、分页信息 | `get_user_list` | `backend/app/api/v1/users.py:124` | `backend/tests/test_users.py` |
| 6 | POST | `/api/v1/users/{target_user_id}/status` | 更新用户状态 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 路径参数：`target_user_id` | `UserStatusUpdate`：`status` | `user.UserResponse` | `update_user_status` | `backend/app/api/v1/users.py:158` | `backend/tests/test_users.py` |
| 7 | POST | `/api/v1/users/{target_user_id}` | 删除用户 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 路径参数：`target_user_id` | 无 | 无；仅返回 `code/message` | `delete_user` | `backend/app/api/v1/users.py:178` | `backend/tests/test_users.py` |
| 8 | GET | `/api/v1/users/teacher-audits` | 讲师审核列表 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 查询参数：`status?`、`page`、`page_size` | 无 | `PageData[TeacherAuditResponse]`：`items[{id,user_id,username?,real_name,phone,email,organization?,title?,introduction?,certificate_urls?,status,review_comment?,created_at,reviewed_at?}]`、分页信息 | `get_teacher_audits` | `backend/app/api/v1/users.py:196` | `backend/tests/test_users.py` |
| 9 | POST | `/api/v1/users/teacher-audits/{audit_id}/review` | 审核讲师申请 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 路径参数：`audit_id` | `TeacherAuditReview`：`approve`、`comment?` | `TeacherAuditResponse` | `review_teacher_audit` | `backend/app/api/v1/users.py:256` | `backend/tests/test_users.py` |
| 10 | GET | `/api/v1/users/admin-applications` | 管理员申请列表 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 查询参数：`status?`、`page`、`page_size` | 无 | `PageData[AdminApplicationResponse]`：`items[{id,user_id,username?,reason,department?,status,review_comment?,created_at,reviewed_at?}]`、分页信息 | `get_admin_applications` | `backend/app/api/v1/users.py:278` | `backend/tests/test_users.py` |
| 11 | POST | `/api/v1/users/admin-applications/{application_id}/review` | 审核管理员申请 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 路径参数：`application_id` | `AdminApplicationReview`：`approve`、`comment?` | `AdminApplicationResponse` | `review_admin_application` | `backend/app/api/v1/users.py:324` | `backend/tests/test_users.py` |

### 5.7 课程管理

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/courses` | 课程列表 | 无需登录 | 无 | 查询参数：`category_id?`、`is_free?`、`page`、`page_size` | 无 | `PageData[CourseListResponse]`：`items[{id,title,subtitle?,cover_url?,teacher_name?,price,original_price?,level,is_free,total_duration,student_count,rating}]`、分页信息 | `get_courses` | `backend/app/api/v1/courses.py:27` | `backend/tests/test_courses.py` |
| 2 | GET | `/api/v1/courses/search` | 课程搜索 | 无需登录 | 无 | 查询参数：`keyword?`、`category_id?`、`level?`、`is_free?`、`min_price?`、`max_price?`、`sort_by`、`sort_order`、`page`、`page_size` | 无 | `PageData[CourseListResponse]` | `search_courses` | `backend/app/api/v1/courses.py:79` | `backend/tests/test_courses.py` |
| 3 | GET | `/api/v1/courses/homepage` | 首页课程 | 无需登录 | 无 | 查询参数：`limit` | 无 | `list[CourseListResponse]` | `get_homepage_courses` | `backend/app/api/v1/courses.py:124` | `backend/tests/test_courses.py` |
| 4 | GET | `/api/v1/courses/my-courses` | 我的课程 | 需要 Bearer Token | 无 | 查询参数：`status?`、`page`、`page_size` | 无 | `PageData[CourseListResponse]` | `get_my_courses` | `backend/app/api/v1/courses.py:140` | `backend/tests/test_courses.py` |
| 5 | GET | `/api/v1/courses/{course_id}` | 课程详情 | 无需登录 | 无 | 路径参数：`course_id` | 无 | `CourseResponse`：`id`、`title`、`subtitle?`、`description?`、`cover_url?`、`teacher_id`、`teacher_name?`、`category_id?`、`category_name?`、`price`、`original_price?`、`level`、`status`、`is_free`、`total_duration`、`total_sections`、`student_count`、`rating`、`rating_count`、`tags?`、`created_at`、`published_at?` | `get_course` | `backend/app/api/v1/courses.py:172` | `backend/tests/test_courses.py` |
| 6 | POST | `/api/v1/courses` | 创建课程 | 需要 Bearer Token | 无 | 无 | `CourseCreate`：`title`、`subtitle?`、`description?`、`cover_url?`、`category_id?`、`price`、`original_price?`、`level`、`is_free`、`tag_ids?` | `CourseResponse` | `create_course` | `backend/app/api/v1/courses.py:222` | `backend/tests/test_courses.py` |
| 7 | POST | `/api/v1/courses/{course_id}` | 更新课程 | 需要 Bearer Token | 无 | 路径参数：`course_id` | `CourseUpdate`：`title?`、`subtitle?`、`description?`、`cover_url?`、`category_id?`、`price?`、`original_price?`、`level?`、`is_free?`、`tag_ids?` | `CourseResponse` | `update_course` | `backend/app/api/v1/courses.py:241` | `backend/tests/test_courses.py` |
| 8 | POST | `/api/v1/courses/{course_id}/publish` | 发布课程 | 需要 Bearer Token | 无 | 路径参数：`course_id` | 无 | `CourseResponse` | `publish_course` | `backend/app/api/v1/courses.py:261` | `backend/tests/test_courses.py` |
| 9 | POST | `/api/v1/courses/{course_id}/archive` | 下架课程 | 需要 Bearer Token | 无 | 路径参数：`course_id` | 无 | `CourseResponse` | `archive_course` | `backend/app/api/v1/courses.py:280` | `backend/tests/test_courses.py` |
| 10 | DELETE | `/api/v1/courses/{course_id}` | 删除课程 | 需要 Bearer Token | 无 | 路径参数：`course_id` | 无 | 无；仅返回 `code/message` | `delete_course` | `backend/app/api/v1/courses.py:299` | `backend/tests/test_courses.py` |
| 11 | POST | `/api/v1/courses/{course_id}/materials` | 上传配套资料 | 需要 Bearer Token | 无 | 路径参数：`course_id` | 支持两种模式：1）`MaterialCreate`：`name`、`file_url`、`file_size`、`file_type?`；2）`multipart/form-data`：`file` | `MaterialResponse`：`id`、`material_id`、`course_id`、`name`、`file_name`、`file_url`、`file_size`、`file_type?`、`download_count`、`created_at` | `create_material` | `backend/app/api/v1/courses.py:317` | `backend/tests/test_courses.py` |
| 12 | DELETE | `/api/v1/courses/{course_id}/materials/{material_id}` | 删除配套资料 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`material_id` | 无 | 无；仅返回 `code/message` | `delete_material` | `backend/app/api/v1/courses.py:337` | `backend/tests/test_courses.py` |
| 13 | POST | `/api/v1/courses/{course_id}/materials/{material_id}/delete` | 删除配套资料（兼容旧前端） | 需要 Bearer Token | 无 | 路径参数：`course_id`、`material_id` | 无 | 无；仅返回 `code/message` | `delete_material_legacy` | `backend/app/api/v1/courses.py:351` | `backend/tests/test_courses.py` |

### 5.8 课程内容

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/courses/{course_id}/chapters` | 章节列表 | 无需登录 | 无 | 路径参数：`course_id` | 无 | `list[ChapterResponse]`：`[{id,course_id,title,description?,sort_order,is_free,total_duration,section_count,created_at}]` | `get_chapters` | `backend/app/api/v1/content.py:33` | `backend/tests/test_content.py` |
| 2 | POST | `/api/v1/courses/{course_id}/chapters` | 创建章节 | 需要 Bearer Token | 无 | 路径参数：`course_id` | `ChapterCreate`：`title`、`description?`、`sort_order`、`is_free` | `ChapterResponse` | `create_chapter` | `backend/app/api/v1/content.py:50` | `backend/tests/test_content.py` |
| 3 | POST | `/api/v1/courses/{course_id}/chapters/{chapter_id}` | 更新章节 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`chapter_id` | `ChapterUpdate`：`title?`、`description?`、`sort_order?`、`is_free?` | `ChapterResponse` | `update_chapter` | `backend/app/api/v1/content.py:71` | `backend/tests/test_content.py` |
| 4 | DELETE | `/api/v1/courses/{course_id}/chapters/{chapter_id}` | 删除章节 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`chapter_id` | 无 | 无；仅返回 `code/message` | `delete_chapter` | `backend/app/api/v1/content.py:92` | `backend/tests/test_content.py` |
| 5 | GET | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections` | 小节列表 | 无需登录 | 无 | 路径参数：`course_id`、`chapter_id` | 无 | `list[SectionResponse]`：`[{id,course_id,chapter_id,title,description?,sort_order,is_free,duration,resource_count,created_at}]` | `get_sections` | `backend/app/api/v1/content.py:111` | `backend/tests/test_content.py` |
| 6 | POST | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections` | 创建小节 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`chapter_id` | `SectionCreate`：`title`、`description?`、`sort_order`、`is_free` | `SectionResponse` | `create_section` | `backend/app/api/v1/content.py:129` | `backend/tests/test_content.py` |
| 7 | POST | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}` | 更新小节 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`chapter_id`、`section_id` | `SectionUpdate`：`title?`、`description?`、`sort_order?`、`is_free?` | `SectionResponse` | `update_section` | `backend/app/api/v1/content.py:150` | `backend/tests/test_content.py` |
| 8 | DELETE | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}` | 删除小节 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`chapter_id`、`section_id` | 无 | 无；仅返回 `code/message` | `delete_section` | `backend/app/api/v1/content.py:172` | `backend/tests/test_content.py` |
| 9 | POST | `/api/v1/courses/{course_id}/sections/{section_id}/resources` | 上传小节资源 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`section_id` | `ResourceCreate` 兼容前端字段：`title?`、`type?`、`resource_type?`、`file_name?`、`file_url`、`file_size`、`duration`、`sort_order`、`is_free` | `ResourceResponse`：`id`、`resource_id`、`course_id`、`chapter_id`、`section_id`、`title`、`file_name`、`type`、`resource_type`、`file_url`、`file_size`、`duration`、`sort_order`、`is_free`、`view_count`、`created_at` | `create_resource` | `backend/app/api/v1/content.py:213` | `backend/tests/test_content.py` |
| 10 | DELETE | `/api/v1/courses/{course_id}/sections/{section_id}/resources/{resource_id}` | 删除小节资源 | 需要 Bearer Token | 无 | 路径参数：`course_id`、`section_id`、`resource_id` | 无 | 无；仅返回 `code/message` | `delete_resource` | `backend/app/api/v1/content.py:242` | `backend/tests/test_content.py` |

补充说明：

- 已新增章节级资源创建接口：`POST /api/v1/courses/{course_id}/chapters/{chapter_id}/resources`
- 已新增兼容删除路由：
  - `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/delete`
  - `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}/delete`
  - `POST /api/v1/courses/{course_id}/sections/{section_id}/resources/{resource_id}/delete`
  - `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/resources/{resource_id}/delete`

### 5.12 文件上传

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | POST | `/api/v1/upload/file` | 上传通用文件 | 需要 Bearer Token | 当前仅允许讲师/管理员调用 | 无 | `multipart/form-data`：`file` | `UploadFileResponse`：`file_name`、`file_url`、`url`、`file_size`、`content_type?` | `upload_file` | `backend/app/api/v1/uploads.py` | `backend/tests/test_uploads.py` |
| 2 | POST | `/api/v1/upload/avatar` | 上传头像 | 需要 Bearer Token | 允许 active 状态的当前登录用户调用，不限制角色 | 无 | `multipart/form-data`：`file` | `UploadFileResponse`：`file_name`、`file_url`、`url`、`file_size`、`content_type?` | `upload_avatar` | `backend/app/api/v1/uploads.py` | `backend/tests/test_uploads.py` |
| 3 | POST | `/api/v1/upload/feedback-image` | 上传反馈截图 | 需要 Bearer Token | 允许 active 状态的当前登录用户调用，不限制角色 | 无 | `multipart/form-data`：`file` | `UploadFileResponse`：`file_name`、`file_url`、`url`、`file_size`、`content_type?` | `upload_feedback_image` | `backend/app/api/v1/uploads.py` | `backend/tests/test_uploads.py` |
| 4 | POST | `/api/v1/upload/init` | 初始化分片上传 | 需要 Bearer Token | 当前仅允许讲师/管理员调用 | 无 | `ChunkUploadInitRequest`：`file_name`、`file_size`、`chunk_size`、`content_type?`、`biz_type?` | `ChunkUploadInitResponse`：`upload_id`、`chunk_size`、`total_chunks` | `init_chunk_upload` | `backend/app/api/v1/uploads.py` | `backend/tests/test_uploads.py` |
| 5 | POST | `/api/v1/upload/chunk` | 上传分片 | 需要 Bearer Token | 当前仅允许讲师/管理员调用 | 无 | `multipart/form-data`：`upload_id`、`chunk_index`、`chunk` | `ChunkUploadChunkResponse`：`chunk_index` | `upload_chunk` | `backend/app/api/v1/uploads.py` | `backend/tests/test_uploads.py` |
| 6 | POST | `/api/v1/upload/complete` | 完成分片上传 | 需要 Bearer Token | 当前仅允许讲师/管理员调用 | 无 | `ChunkUploadCompleteRequest`：`upload_id`、`file_name`、`total_chunks` | `UploadFileResponse`：`file_name`、`file_url`、`url`、`file_size`、`content_type?` | `complete_chunk_upload` | `backend/app/api/v1/uploads.py` | `backend/tests/test_uploads.py` |

### 5.9 学习模块

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | POST | `/api/v1/learning/courses/{course_id}/start` | 开始学习 | 需要 Bearer Token | 无 | 路径参数：`course_id` | 无 | `dict`：开始学习结果；路由层未声明固定字段结构 | `start_learning` | `backend/app/api/v1/learning.py:24` | `backend/tests/test_learning.py` |
| 2 | POST | `/api/v1/learning/progress` | 保存进度 | 需要 Bearer Token | 无 | 无 | `SaveProgressRequest`：`course_id`、`chapter_id`、`section_id`、`resource_id`、`position`、`progress` | `ProgressResponse`：`course_id`、`chapter_id`、`section_id`、`resource_id`、`progress`、`position`、`is_completed`、`last_play_at?` | `save_progress` | `backend/app/api/v1/learning.py:40` | `backend/tests/test_learning.py` |
| 3 | GET | `/api/v1/learning/progress` | 获取进度 | 需要 Bearer Token | 无 | 查询参数：`course_id` | 无 | `list[ProgressResponse]` | `get_progress` | `backend/app/api/v1/learning.py:59` | `backend/tests/test_learning.py` |
| 4 | GET | `/api/v1/learning/courses/{course_id}/continue` | 继续学习 | 需要 Bearer Token | 无 | 路径参数：`course_id` | 无 | `ContinueLearningResponse`：`course_id`、`chapter_id?`、`section_id?`、`resource_id?`、`position` | `continue_learning` | `backend/app/api/v1/learning.py:77` | `backend/tests/test_learning.py` |
| 5 | GET | `/api/v1/learning/resources/{resource_id}/play` | 获取播放地址 | 需要 Bearer Token | 无 | 路径参数：`resource_id` | 无 | `PlayUrlResponse`：`resource_id`、`title`、`play_url`、`duration`、`is_free` | `get_play_url` | `backend/app/api/v1/learning.py:93` | `backend/tests/test_learning.py` |
| 6 | GET | `/api/v1/learning/resources/{resource_id}/preview` | 文档预览 | 需要 Bearer Token | 无 | 路径参数：`resource_id` | 无 | `PreviewResponse`：`resource_id`、`title`、`preview_url`、`file_type` | `get_preview_url` | `backend/app/api/v1/learning.py:109` | `backend/tests/test_learning.py` |

### 5.10 反馈管理

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | POST | `/api/v1/feedbacks` | 提交反馈 | 需要 Bearer Token | 无 | 无 | `FeedbackCreate`：`type`、`title`、`content`、`contact?`、`images?` | `FeedbackResponse`：`id`、`user_id`、`type`、`title`、`content`、`contact?`、`images?`、`status`、`reply?`、`replied_at?`、`created_at` | `create_feedback` | `backend/app/api/v1/feedbacks.py:23` | `backend/tests/test_feedbacks.py` |
| 2 | GET | `/api/v1/feedbacks` | 反馈列表 | 需要 Bearer Token | 描述声明为“用户查看自己的反馈，管理员查看所有”，路由层未见显式 RBAC | 查询参数：`status?`、`page`、`page_size` | 无 | `PageData[FeedbackResponse]`：`items[{id,user_id,type,title,content,contact?,images?,status,reply?,replied_at?,created_at}]`、分页信息 | `get_feedbacks` | `backend/app/api/v1/feedbacks.py:42` | `backend/tests/test_feedbacks.py` |
| 3 | GET | `/api/v1/feedbacks/{feedback_id}` | 反馈详情 | 需要 Bearer Token | 无 | 路径参数：`feedback_id` | 无 | `FeedbackResponse` | `get_feedback` | `backend/app/api/v1/feedbacks.py:92` | `backend/tests/test_feedbacks.py` |
| 4 | POST | `/api/v1/feedbacks/{feedback_id}/process` | 标记已处理 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 路径参数：`feedback_id` | `FeedbackProcess`：`reply` | `FeedbackResponse` | `process_feedback` | `backend/app/api/v1/feedbacks.py:125` | `backend/tests/test_feedbacks.py` |

### 5.11 消息管理

| 序号 | 方法 | 路径 | 接口说明 | 登录要求 | 权限备注 | 路径/查询参数 | 请求体字段摘要 | 返回 data 字段摘要 | 处理函数 | 代码位置 | 测试文件 |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/v1/messages` | 消息列表 | 需要 Bearer Token | 无 | 查询参数：`type?`、`is_read?`、`page`、`page_size` | 无 | `PageData[MessageResponse]`：`items[{id,type,title,content,link?,is_read,read_at?,created_at}]`、分页信息 | `get_messages` | `backend/app/api/v1/messages.py:21` | `backend/tests/test_feedbacks.py` |
| 2 | GET | `/api/v1/messages/{message_id}` | 消息详情 | 需要 Bearer Token | 无 | 路径参数：`message_id` | 无 | `MessageResponse`：`id`、`type`、`title`、`content`、`link?`、`is_read`、`read_at?`、`created_at` | `get_message` | `backend/app/api/v1/messages.py:54` | `backend/tests/test_feedbacks.py` |
| 3 | POST | `/api/v1/messages/{message_id}/read` | 标记已读 | 需要 Bearer Token | 无 | 路径参数：`message_id` | 无 | `MessageResponse` | `mark_message_read` | `backend/app/api/v1/messages.py:73` | `backend/tests/test_feedbacks.py` |
| 4 | POST | `/api/v1/messages/mark-all-read` | 批量已读 | 需要 Bearer Token | 无 | 无 | 无 | `dict`：`count`（本次标记为已读的消息数量） | `mark_all_read` | `backend/app/api/v1/messages.py:92` | `backend/tests/test_feedbacks.py` |
| 5 | DELETE | `/api/v1/messages/{message_id}` | 删除消息 | 需要 Bearer Token | 无 | 路径参数：`message_id` | 无 | 无；仅返回 `code/message` | `delete_message` | `backend/app/api/v1/messages.py:110` | `backend/tests/test_feedbacks.py` |
| 6 | GET | `/api/v1/messages/unread-count` | 未读数量 | 需要 Bearer Token | 无 | 无 | 无 | `UnreadCountResponse`：`total`、`system`、`course`、`interaction` | `get_unread_count` | `backend/app/api/v1/messages.py:126` | `backend/tests/test_feedbacks.py` |
| 7 | POST | `/api/v1/messages/send` | 发送系统消息 | 需要 Bearer Token | 描述声明为管理员权限，路由层未见显式 RBAC | 无 | `MessageSend`：`user_id`、`type`、`title`、`content`、`link?` | `MessageResponse` | `send_message` | `backend/app/api/v1/messages.py:141` | `backend/tests/test_feedbacks.py` |

## 6. 模型字段附录

> 说明：以下仅汇总高频请求/响应模型的关键字段，便于前后端快速对照；是否实际使用仍以第 5 节对应接口为准。

### 6.1 认证与用户相关模型

- `RegisterRequest`：`username`、`email`、`password`、`role`、`captcha_key?`、`captcha_text?`
- `LoginRequest`：`username`、`password`、`remember_me`、`captcha_key?`、`captcha_text?`
- `LoginResponse`：`access_token`、`refresh_token`、`token_type`、`expires_in`、`user`
- `RefreshTokenRequest`：`refresh_token`
- `TokenResponse`：`access_token`、`token_type`、`expires_in`
- `CaptchaResponse`：`captcha_key`、`captcha_image`
- `SendEmailCodeRequest`：`email`、`purpose`、`captcha_key?`、`captcha_text?`
- `ResetPasswordRequest`：`email`、`code`、`new_password`
- `UserProfileUpdate`：`nickname?`、`avatar?`、`bio?`、`phone?`
- `ChangePasswordRequest`：`old_password`、`new_password`
- `UserStatusUpdate`：`status`
- `TeacherAuditReview`：`approve`、`comment?`
- `AdminApplicationReview`：`approve`、`comment?`
- `user.UserResponse`：`id`、`username`、`email`、`phone?`、`nickname?`、`avatar?`、`bio?`、`role`、`status`、`created_at`、`last_login_at?`
- `UserListResponse`：`id`、`username`、`email`、`nickname?`、`role`、`status`、`created_at`、`last_login_at?`
- `TeacherAuditResponse`：`id`、`user_id`、`username?`、`real_name`、`phone`、`email`、`organization?`、`title?`、`introduction?`、`certificate_urls?`、`status`、`review_comment?`、`created_at`、`reviewed_at?`
- `AdminApplicationResponse`：`id`、`user_id`、`username?`、`reason`、`department?`、`status`、`review_comment?`、`created_at`、`reviewed_at?`

### 6.2 系统管理相关模型

- `CategoryCreate`：`name`、`slug`、`description?`、`icon?`、`parent_id?`、`sort_order`
- `CategoryUpdate`：`name?`、`slug?`、`description?`、`icon?`、`parent_id?`、`sort_order?`、`is_active?`
- `CategoryResponse`：`id`、`name`、`slug`、`description?`、`icon?`、`sort_order`、`parent_id?`、`is_active`、`created_at`
- `TagCreate`：`name`、`slug`、`color?`
- `TagResponse`：`id`、`name`、`slug`、`color?`、`use_count`、`created_at`
- `AnnouncementResponse`：`id`、`title`、`content`、`type`、`is_top`、`is_published`、`publish_at?`、`expire_at?`、`view_count`、`author_id?`、`created_at`

### 6.3 课程与内容相关模型

- `CourseCreate`：`title`、`subtitle?`、`description?`、`cover_url?`、`category_id?`、`price`、`original_price?`、`level`、`is_free`、`tag_ids?`
- `CourseUpdate`：`title?`、`subtitle?`、`description?`、`cover_url?`、`category_id?`、`price?`、`original_price?`、`level?`、`is_free?`、`tag_ids?`
- `CourseListResponse`：`id`、`title`、`subtitle?`、`cover_url?`、`teacher_name?`、`price`、`original_price?`、`level`、`is_free`、`total_duration`、`student_count`、`rating`
- `CourseResponse`：`id`、`title`、`subtitle?`、`description?`、`cover_url?`、`teacher_id`、`teacher_name?`、`category_id?`、`category_name?`、`price`、`original_price?`、`level`、`status`、`is_free`、`total_duration`、`total_sections`、`student_count`、`rating`、`rating_count`、`tags?`、`created_at`、`published_at?`
- `CourseResponse` 现已包含：`chapters[]`、`materials[]`
- `MaterialCreate`：`name`、`file_url`、`file_size`、`file_type?`
- `MaterialResponse`：`id`、`material_id`、`course_id`、`name`、`file_name`、`file_url`、`file_size`、`file_type?`、`download_count`、`created_at`
- `ChapterCreate`：`title`、`description?`、`sort_order`、`is_free`
- `ChapterUpdate`：`title?`、`description?`、`sort_order?`、`is_free?`
- `ChapterResponse`：`id`、`course_id`、`title`、`description?`、`sort_order`、`is_free`、`total_duration`、`section_count`、`created_at`
- `SectionCreate`：`title`、`description?`、`sort_order`、`is_free`
- `SectionUpdate`：`title?`、`description?`、`sort_order?`、`is_free?`
- `SectionResponse`：`id`、`section_id`、`course_id`、`chapter_id`、`title`、`description?`、`sort_order`、`is_free`、`duration`、`resource_count`、`created_at`、`resources[]`
- `ResourceCreate`：`title?`、`type?`、`resource_type?`、`file_name?`、`file_url`、`file_size`、`duration`、`sort_order`、`is_free`
- `ResourceResponse`：`id`、`resource_id`、`course_id`、`chapter_id`、`section_id?`、`title`、`file_name`、`type`、`resource_type`、`file_url`、`file_size`、`duration`、`sort_order`、`is_free`、`view_count`、`created_at`
- `CourseContentResponse`：`chapters[list[ChapterWithSections]]`
- `UploadFileResponse`：`file_name`、`file_url`、`url`、`file_size`、`content_type?`
- `ChunkUploadInitRequest`：`file_name`、`file_size`、`chunk_size`、`content_type?`、`biz_type?`
- `ChunkUploadInitResponse`：`upload_id`、`chunk_size`、`total_chunks`
- `ChunkUploadChunkResponse`：`chunk_index`
- `ChunkUploadCompleteRequest`：`upload_id`、`file_name`、`total_chunks`

### 6.4 学习、反馈与消息相关模型

- `SaveProgressRequest`：`course_id`、`chapter_id`、`section_id`、`resource_id`、`position`、`progress`
- `ProgressResponse`：`course_id`、`chapter_id`、`section_id`、`resource_id`、`progress`、`position`、`is_completed`、`last_play_at?`
- `ContinueLearningResponse`：`course_id`、`chapter_id?`、`section_id?`、`resource_id?`、`position`
- `PlayUrlResponse`：`resource_id`、`title`、`play_url`、`duration`、`is_free`
- `PreviewResponse`：`resource_id`、`title`、`preview_url`、`file_type`
- `FeedbackCreate`：`type`、`title`、`content`、`contact?`、`images?`
- `FeedbackProcess`：`reply`
- `FeedbackResponse`：`id`、`user_id`、`type`、`title`、`content`、`contact?`、`images?`、`status`、`reply?`、`replied_at?`、`created_at`
- `MessageSend`：`user_id`、`type`、`title`、`content`、`link?`
- `MessageResponse`：`id`、`type`、`title`、`content`、`link?`、`is_read`、`read_at?`、`created_at`
- `UnreadCountResponse`：`total`、`system`、`course`、`interaction`

### 6.5 通用响应包装

- `ApiResponse[T]`：统一外层结构为 `code`、`message`、`data`
- `PageData[T]`：分页结构为 `items`、`total`、`page`、`page_size`、`total_pages`
- 文档中提到的“仅返回 `code/message`”表示该接口 `data` 为空或未声明业务载荷
- 文档中提到的 `dict` 表示路由 `response_model` 未对 `data` 内部结构做固定 Schema 约束

## 7. 结论

- 当前实际已挂载业务模块共 **12 个**。
- 当前实际已挂载业务接口共 **81 个**。
- 其中公开接口 **24 个**，需登录接口 **57 个**。
- 多个接口文案包含“管理员权限”“讲师权限”等角色语义，但路由层统一只看到了 `CurrentUserId`，**未见显式 RBAC 依赖**；前后端联调时应以此差异为前提。
- 若后续代码新增/删除路由，应优先更新本清单，而不是仅更新需求文档或手动测试文档。
