# 前端联调 API 速查表

## 1. 使用说明

本文档是 `docs/api-endpoint-inventory.md` 的压缩版，只保留前端联调最常用的信息：`方法`、`路径`、`登录`、`核心请求`、`核心返回`、`备注`。

如果需要查看精确代码位置、处理函数、测试文件或完整模型字段，请回到：`docs/api-endpoint-inventory.md`。

## 2. 基线与共识

- 统计范围：仅包含已在 `backend/app/api/v1/router.py` 挂载的业务接口
- 业务模块：**11 个**
- 业务接口：**68 个**
- 公开接口：**23 个**
- 需登录接口：**45 个**
- 统一前缀：`/api/v1`
- 登录判定：使用 `CurrentUserId` 的接口统一视为需要 `Authorization: Bearer <token>`
- 当前已挂载业务路由中：**未发现 `OptionalUserId` 用例**

## 3. 联调前先看这 4 条

### 3.1 统一响应外层

所有接口默认外层都是：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

分页接口的 `data` 统一是：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10,
  "total_pages": 0
}
```

### 3.2 文案权限不等于路由强校验

部分接口描述里写了“管理员权限”“讲师权限”，但当前路由层可直接看到的依赖主要只有 `CurrentUserId`，**未见显式 RBAC 依赖**。前端联调时应把这类接口视为：

- 已知事实：需要登录
- 待业务确认：是否还存在服务层/后续补充的角色限制

### 3.3 这些接口虽然是更新/状态变更，但用的是 `POST`

- `POST /api/v1/users/me`
- `POST /api/v1/users/{target_user_id}/status`
- `POST /api/v1/users/{target_user_id}`
- `POST /api/v1/courses/{course_id}`
- `POST /api/v1/courses/{course_id}/publish`
- `POST /api/v1/courses/{course_id}/archive`
- `POST /api/v1/courses/{course_id}/chapters/{chapter_id}`
- `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}`
- `POST /api/v1/feedbacks/{feedback_id}/process`
- `POST /api/v1/messages/{message_id}/read`
- `POST /api/v1/messages/mark-all-read`
- `POST /api/v1/messages/send`

### 3.4 少数接口 `data` 不是固定 Schema

- `POST /api/v1/learning/courses/{course_id}/start` → `data` 为 `dict`
- `POST /api/v1/messages/mark-all-read` → `data.count`
- 标注“仅返回 `code/message`”的接口 → `data` 为空或未声明业务载荷

## 4. 模块总览

| 模块 | 接口数 | 公开 | 需登录 |
|---|---:|---:|---:|
| 健康检查 | 2 | 2 | 0 |
| 用户认证 | 7 | 6 | 1 |
| 分类管理 | 4 | 4 | 0 |
| 标签管理 | 2 | 2 | 0 |
| 公告管理 | 3 | 3 | 0 |
| 用户管理 | 11 | 0 | 11 |
| 课程管理 | 12 | 4 | 8 |
| 课程内容 | 10 | 2 | 8 |
| 学习模块 | 6 | 0 | 6 |
| 反馈管理 | 4 | 0 | 4 |
| 消息管理 | 7 | 0 | 7 |

## 5. 模块速查

### 5.1 健康检查

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/health` | 否 | 无 | 仅 `code/message` | 健康检查 |
| GET | `/api/v1/ping` | 否 | 无 | 仅 `code/message` | 连通性检查 |

### 5.2 用户认证

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| POST | `/api/v1/auth/register` | 否 | `username,email,password,role,captcha_key?,captcha_text?` | `id,username,email,nickname?,avatar?,role,status,created_at` | 注册 |
| POST | `/api/v1/auth/login` | 否 | `username,password,remember_me,captcha_key?,captcha_text?` | `access_token,refresh_token,token_type,expires_in,user` | 登录 |
| POST | `/api/v1/auth/logout` | 是 | 查询：`refresh_token?` | 仅 `code/message` | 退出登录 |
| POST | `/api/v1/auth/refresh` | 否 | `refresh_token` | `access_token,token_type,expires_in` | 刷新令牌 |
| GET | `/api/v1/auth/captcha` | 否 | 无 | `captcha_key,captcha_image` | 获取图形验证码 |
| POST | `/api/v1/auth/send-email-code` | 否 | `email,purpose,captcha_key?,captcha_text?` | 仅 `code/message` | 发送邮箱验证码 |
| POST | `/api/v1/auth/reset-password` | 否 | `email,code,new_password` | 仅 `code/message` | 重置密码 |

### 5.3 分类管理

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/categories` | 否 | 查询：`parent_id?,is_active?` | `list[id,name,slug,description?,icon?,sort_order,parent_id?,is_active,created_at]` | 分类列表 |
| POST | `/api/v1/categories` | 否 | `name,slug,description?,icon?,parent_id?,sort_order` | `CategoryResponse` | 创建分类 |
| PUT | `/api/v1/categories/{category_id}` | 否 | 路径：`category_id`；体：`name?,slug?,description?,icon?,parent_id?,sort_order?,is_active?` | `CategoryResponse` | 更新分类 |
| DELETE | `/api/v1/categories/{category_id}` | 否 | 路径：`category_id` | 仅 `code/message` | 删除分类 |

### 5.4 标签管理

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/tags` | 否 | 查询：`keyword?,page,page_size` | 分页 `items[id,name,slug,color?,use_count,created_at]` | 标签列表 |
| POST | `/api/v1/tags` | 否 | `name,slug,color?` | `id,name,slug,color?,use_count,created_at` | 创建标签 |

### 5.5 公告管理

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/announcements` | 否 | 查询：`is_published?,type?,page,page_size` | 分页 `items[id,title,content,type,is_top,is_published,publish_at?,expire_at?,view_count,author_id?,created_at]` | 公告列表 |
| GET | `/api/v1/announcements/active` | 否 | 查询：`limit` | `list[AnnouncementResponse]` | 当前有效公告 |
| GET | `/api/v1/announcements/{announcement_id}` | 否 | 路径：`announcement_id` | `AnnouncementResponse` | 公告详情 |

### 5.6 用户管理

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/users/me` | 是 | 无 | `id,username,email,phone?,nickname?,avatar?,bio?,role,status,created_at,last_login_at?` | 当前用户 |
| POST | `/api/v1/users/me` | 是 | `nickname?,avatar?,bio?,phone?` | `UserResponse` | 非标准更新 `POST` |
| POST | `/api/v1/users/me/change-password` | 是 | `old_password,new_password` | 仅 `code/message` | 修改密码 |
| GET | `/api/v1/users/me/learning-records` | 是 | 查询：`page,page_size` | 分页 `items[id,course_id,course_name?,progress,total_duration,last_section_id?,completed_at?,created_at,updated_at]` | 学习记录 |
| GET | `/api/v1/users` | 是 | 查询：`keyword?,role?,status?,page,page_size` | 分页 `items[id,username,email,nickname?,role,status,created_at,last_login_at?]` | 文案写管理员权限，路由层未见显式 RBAC |
| POST | `/api/v1/users/{target_user_id}/status` | 是 | 路径：`target_user_id`；体：`status` | `UserResponse` | 非标准更新 `POST`；文案写管理员权限 |
| POST | `/api/v1/users/{target_user_id}` | 是 | 路径：`target_user_id` | 仅 `code/message` | 非标准删除 `POST`；文案写管理员权限 |
| GET | `/api/v1/users/teacher-audits` | 是 | 查询：`status?,page,page_size` | 分页 `items[id,user_id,username?,real_name,phone,email,organization?,title?,introduction?,certificate_urls?,status,review_comment?,created_at,reviewed_at?]` | 文案写管理员权限 |
| POST | `/api/v1/users/teacher-audits/{audit_id}/review` | 是 | 路径：`audit_id`；体：`approve,comment?` | `TeacherAuditResponse` | 文案写管理员权限 |
| GET | `/api/v1/users/admin-applications` | 是 | 查询：`status?,page,page_size` | 分页 `items[id,user_id,username?,reason,department?,status,review_comment?,created_at,reviewed_at?]` | 文案写管理员权限 |
| POST | `/api/v1/users/admin-applications/{application_id}/review` | 是 | 路径：`application_id`；体：`approve,comment?` | `AdminApplicationResponse` | 文案写管理员权限 |

### 5.7 课程管理

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/courses` | 否 | 查询：`category_id?,is_free?,page,page_size` | 分页 `items[id,title,subtitle?,cover_url?,teacher_name?,price,original_price?,level,is_free,total_duration,student_count,rating]` | 课程列表 |
| GET | `/api/v1/courses/search` | 否 | 查询：`keyword?,category_id?,level?,is_free?,min_price?,max_price?,sort_by,sort_order,page,page_size` | 分页 `CourseListResponse` | 搜索 |
| GET | `/api/v1/courses/homepage` | 否 | 查询：`limit` | `list[CourseListResponse]` | 首页课程 |
| GET | `/api/v1/courses/my-courses` | 是 | 查询：`status?,page,page_size` | 分页 `CourseListResponse` | 我的课程 |
| GET | `/api/v1/courses/{course_id}` | 否 | 路径：`course_id` | `CourseResponse` | 课程详情 |
| POST | `/api/v1/courses` | 是 | `title,subtitle?,description?,cover_url?,category_id?,price,original_price?,level,is_free,tag_ids?` | `CourseResponse` | 创建课程 |
| POST | `/api/v1/courses/{course_id}` | 是 | 路径：`course_id`；体：`title?,subtitle?,description?,cover_url?,category_id?,price?,original_price?,level?,is_free?,tag_ids?` | `CourseResponse` | 非标准更新 `POST` |
| POST | `/api/v1/courses/{course_id}/publish` | 是 | 路径：`course_id` | `CourseResponse` | 非标准状态流转 `POST` |
| POST | `/api/v1/courses/{course_id}/archive` | 是 | 路径：`course_id` | `CourseResponse` | 非标准状态流转 `POST` |
| DELETE | `/api/v1/courses/{course_id}` | 是 | 路径：`course_id` | 仅 `code/message` | 删除课程 |
| POST | `/api/v1/courses/{course_id}/materials` | 是 | 路径：`course_id`；体：`name,file_url,file_size,file_type?` | `id,course_id,name,file_url,file_size,file_type?,download_count,created_at` | 上传资料 |
| DELETE | `/api/v1/courses/{course_id}/materials/{material_id}` | 是 | 路径：`course_id,material_id` | 仅 `code/message` | 删除资料 |

### 5.8 课程内容

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/courses/{course_id}/chapters` | 否 | 路径：`course_id` | `list[ChapterResponse]` | 章节列表 |
| POST | `/api/v1/courses/{course_id}/chapters` | 是 | 路径：`course_id`；体：`title,description?,sort_order,is_free` | `ChapterResponse` | 创建章节 |
| POST | `/api/v1/courses/{course_id}/chapters/{chapter_id}` | 是 | 路径：`course_id,chapter_id`；体：`title?,description?,sort_order?,is_free?` | `ChapterResponse` | 非标准更新 `POST` |
| DELETE | `/api/v1/courses/{course_id}/chapters/{chapter_id}` | 是 | 路径：`course_id,chapter_id` | 仅 `code/message` | 删除章节 |
| POST | `/api/v1/courses/{course_id}/chapters/{chapter_id}/resources` | 是 | 路径：`course_id,chapter_id`；体：`resource_type,title?,file_name,file_url,file_size,duration?,resolution?,thumbnail_url?,sort_order?,is_free?` | `ResourceResponse` | 上传章节资源 |
| DELETE | `/api/v1/courses/{course_id}/chapters/{chapter_id}/resources/{resource_id}` | 是 | 路径：`course_id,chapter_id,resource_id` | 仅 `code/message` | 删除章节资源 |
| GET | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections` | 否 | 路径：`course_id,chapter_id` | `list[SectionResponse]` | 小节列表 |
| POST | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections` | 是 | 路径：`course_id,chapter_id`；体：`title,description?,sort_order,is_free` | `SectionResponse` | 创建小节 |
| POST | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}` | 是 | 路径：`course_id,chapter_id,section_id`；体：`title?,description?,sort_order?,is_free?` | `SectionResponse` | 非标准更新 `POST` |
| DELETE | `/api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}` | 是 | 路径：`course_id,chapter_id,section_id` | 仅 `code/message` | 删除小节 |
| POST | `/api/v1/courses/{course_id}/sections/{section_id}/resources` | 是 | 路径：`course_id,section_id`；体：`title,type,file_url,file_size,duration,sort_order,is_free` | `ResourceResponse` | 上传资源 |
| DELETE | `/api/v1/courses/{course_id}/sections/{section_id}/resources/{resource_id}` | 是 | 路径：`course_id,section_id,resource_id` | 仅 `code/message` | 删除资源 |

`ChapterResponse` 需新增 `resources?: ResourceResponse[]` 字段，供章节级资源管理、编辑页回显和发布校验使用。

### 5.9 学习模块

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| POST | `/api/v1/learning/courses/{course_id}/start` | 是 | 路径：`course_id` | `dict` | 返回结构未固定 |
| POST | `/api/v1/learning/progress` | 是 | `course_id,chapter_id,section_id,resource_id,position,progress` | `course_id,chapter_id,section_id,resource_id,progress,position,is_completed,last_play_at?` | 保存进度 |
| GET | `/api/v1/learning/progress` | 是 | 查询：`course_id` | `list[ProgressResponse]` | 获取进度 |
| GET | `/api/v1/learning/courses/{course_id}/continue` | 是 | 路径：`course_id` | `course_id,chapter_id?,section_id?,resource_id?,position` | 继续学习 |
| GET | `/api/v1/learning/resources/{resource_id}/play` | 是 | 路径：`resource_id` | `resource_id,title,play_url,duration,is_free` | 获取播放地址 |
| GET | `/api/v1/learning/resources/{resource_id}/preview` | 是 | 路径：`resource_id` | `resource_id,title,preview_url,file_type` | 文档预览 |

### 5.10 反馈管理

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| POST | `/api/v1/feedbacks` | 是 | `type,title,content,contact?,images?` | `id,user_id,type,title,content,contact?,images?,status,reply?,replied_at?,created_at` | 提交反馈 |
| GET | `/api/v1/feedbacks` | 是 | 查询：`status?,page,page_size` | 分页 `items[id,user_id,type,title,content,contact?,images?,status,reply?,replied_at?,created_at]` | 文案写“用户/管理员视角”，路由层未见显式 RBAC |
| GET | `/api/v1/feedbacks/{feedback_id}` | 是 | 路径：`feedback_id` | `FeedbackResponse` | 反馈详情 |
| POST | `/api/v1/feedbacks/{feedback_id}/process` | 是 | 路径：`feedback_id`；体：`reply` | `FeedbackResponse` | 非标准处理 `POST`；文案写管理员权限 |

### 5.11 消息管理

| 方法 | 路径 | 登录 | 核心请求 | 核心返回 | 备注 |
|---|---|---|---|---|---|
| GET | `/api/v1/messages` | 是 | 查询：`type?,is_read?,page,page_size` | 分页 `items[id,type,title,content,link?,is_read,read_at?,created_at]` | 消息列表 |
| GET | `/api/v1/messages/{message_id}` | 是 | 路径：`message_id` | `id,type,title,content,link?,is_read,read_at?,created_at` | 消息详情 |
| POST | `/api/v1/messages/{message_id}/read` | 是 | 路径：`message_id` | `MessageResponse` | 非标准状态流转 `POST` |
| POST | `/api/v1/messages/mark-all-read` | 是 | 无 | `count` | `data.count` 为本次已读数量 |
| DELETE | `/api/v1/messages/{message_id}` | 是 | 路径：`message_id` | 仅 `code/message` | 删除消息 |
| GET | `/api/v1/messages/unread-count` | 是 | 无 | `total,system,course,interaction` | 未读数 |
| POST | `/api/v1/messages/send` | 是 | `user_id,type,title,content,link?` | `MessageResponse` | 非标准发送 `POST`；文案写管理员权限 |

## 6. 高频模型速记

### 6.1 认证与用户

- `RegisterRequest`：`username,email,password,role,captcha_key?,captcha_text?`
- `LoginRequest`：`username,password,remember_me,captcha_key?,captcha_text?`
- `LoginResponse`：`access_token,refresh_token,token_type,expires_in,user`
- `TokenResponse`：`access_token,token_type,expires_in`
- `UserProfileUpdate`：`nickname?,avatar?,bio?,phone?`
- `ChangePasswordRequest`：`old_password,new_password`

### 6.2 课程与内容

- `CourseCreate`：`title,subtitle?,description?,cover_url?,category_id?,price,original_price?,level,is_free,tag_ids?`
- `CourseUpdate`：`title?,subtitle?,description?,cover_url?,category_id?,price?,original_price?,level?,is_free?,tag_ids?`
- `ChapterCreate`：`title,description?,sort_order,is_free`
- `SectionCreate`：`title,description?,sort_order,is_free`
- `ResourceCreate`：`title,type,file_url,file_size,duration,sort_order,is_free`

### 6.3 学习、反馈、消息

- `SaveProgressRequest`：`course_id,chapter_id,section_id,resource_id,position,progress`
- `FeedbackCreate`：`type,title,content,contact?,images?`
- `FeedbackProcess`：`reply`
- `MessageSend`：`user_id,type,title,content,link?`

## 7. 前端联调建议顺序

### 7.1 游客态

1. `GET /api/v1/auth/captcha`
2. `POST /api/v1/auth/send-email-code`
3. `POST /api/v1/auth/register`
4. `POST /api/v1/auth/login`
5. `GET /api/v1/courses`
6. `GET /api/v1/courses/{course_id}`
7. `GET /api/v1/announcements/active`

### 7.2 登录后常用链路

1. `GET /api/v1/users/me`
2. `GET /api/v1/courses/my-courses`
3. `GET /api/v1/messages`
4. `GET /api/v1/messages/unread-count`
5. `POST /api/v1/learning/progress`
6. `GET /api/v1/learning/courses/{course_id}/continue`
7. `POST /api/v1/feedbacks`

## 8. 对照关系

- 完整事实版：`docs/api-endpoint-inventory.md`
- 本文定位：联调速查
- 如果路由代码有新增/删除，应先更新事实版，再同步更新本速查表
