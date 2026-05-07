# 在线学习平台架构文档

## 1. 项目概述

### 1.1 项目简介
本项目是一个在线学习平台的后端 API 服务，提供用户管理、课程管理、学习进度跟踪、反馈消息等功能模块。

### 1.2 技术栈

| 类别 | 技术选型 | 版本要求 |
|------|---------|---------|
| Web框架 | FastAPI | >=0.110.0 |
| ASGI服务器 | Uvicorn | >=0.27.0 |
| ORM | SQLAlchemy (asyncio) | >=2.0.0 |
| 数据库驱动 | aiomysql / aiosqlite | >=0.2.0 |
| 数据迁移 | Alembic | >=1.13.0 |
| 数据验证 | Pydantic | >=2.6.0 |
| 配置管理 | pydantic-settings | >=2.1.0 |
| JWT认证 | python-jose | >=3.3.0 |
| 密码加密 | passlib[bcrypt] | >=1.7.4 |
| HTTP客户端 | httpx | >=0.26.0 |
| 缓存 | Redis | >=5.0.0 |
| 测试框架 | pytest + pytest-asyncio | >=8.0.0 |

## 2. 项目结构

```
backend/
├── app/                          # 应用主目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口
│   ├── config.py                 # 配置管理
│   ├── api/                      # API 路由层
│   │   ├── __init__.py
│   │   └── v1/                   # v1 版本 API
│   │       ├── __init__.py
│   │       ├── router.py         # 路由聚合
│   │       ├── health.py         # 健康检查
│   │       ├── auth.py           # 用户认证
│   │       ├── users.py          # 用户管理
│   │       ├── courses.py        # 课程管理
│   │       ├── content.py        # 课程内容
│   │       ├── learning.py       # 学习模块
│   │       ├── feedbacks.py      # 反馈管理
│   │       ├── messages.py       # 消息管理
│   │       ├── categories.py     # 分类管理
│   │       ├── tags.py           # 标签管理
│   │       └── announcements.py  # 公告管理
│   ├── core/                     # 核心模块
│   │   ├── __init__.py
│   │   ├── dependencies.py       # 依赖注入
│   │   ├── security.py           # 安全工具
│   │   ├── exceptions.py         # 自定义异常
│   │   └── logging.py            # 日志配置
│   ├── middleware/               # 中间件
│   │   ├── __init__.py
│   │   └── logging_middleware.py # 请求日志中间件
│   ├── models/                   # 数据库模型层
│   │   ├── __init__.py
│   │   ├── base.py               # 基础模型
│   │   ├── user.py               # 用户模型
│   │   ├── captcha.py            # 验证码模型
│   │   ├── email_code.py         # 邮箱验证码
│   │   ├── refresh_token.py      # 刷新令牌
│   │   ├── category.py           # 分类模型
│   │   ├── tag.py                # 标签模型
│   │   ├── announcement.py       # 公告模型
│   │   ├── teacher_audit.py      # 讲师审核
│   │   ├── admin_application.py  # 管理员申请
│   │   ├── learning_progress.py  # 学习进度
│   │   ├── course.py             # 课程模型
│   │   ├── content.py            # 章节内容
│   │   ├── learning.py           # 学习记录
│   │   ├── feedback.py           # 反馈模型
│   │   └── message.py            # 消息模型
│   ├── schemas/                  # Pydantic Schema层
│   │   ├── __init__.py
│   │   ├── common.py             # 通用响应模型
│   │   ├── auth.py               # 认证相关
│   │   ├── user.py               # 用户相关
│   │   ├── course.py             # 课程相关
│   │   ├── content.py            # 内容相关
│   │   ├── learning.py           # 学习相关
│   │   ├── feedback.py           # 反馈相关
│   │   ├── message.py            # 消息相关
│   │   └── system.py             # 系统相关
│   └── services/                 # 业务逻辑层
│       ├── __init__.py
│       ├── auth_service.py       # 认证服务
│       ├── user_service.py       # 用户服务
│       ├── course_service.py     # 课程服务
│       ├── content_service.py    # 内容服务
│       ├── learning_service.py   # 学习服务
│       ├── feedback_service.py   # 反馈服务
│       ├── message_service.py    # 消息服务
│       └── system_service.py     # 系统服务
├── tests/                        # 测试目录
│   └── __init__.py
└── requirements.txt              # 依赖清单
```

## 3. 架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                     API 路由层                           │
│  (api/v1/*.py)                                          │
│  - 接收HTTP请求                                          │
│  - 参数验证（Pydantic）                                   │
│  - 调用服务层                                            │
│  - 返回统一响应格式                                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     服务层                               │
│  (services/*.py)                                        │
│  - 业务逻辑处理                                          │
│  - 数据组装与转换                                        │
│  - 事务管理                                              │
│  - 异常处理                                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     模型层                               │
│  (models/*.py)                                          │
│  - 数据库表映射                                          │
│  - ORM关系定义                                           │
│  - 基础CRUD操作                                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     数据库                               │
│  MySQL / SQLite                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

#### 3.2.1 配置管理 (config.py)
- 使用 `pydantic-settings` 管理环境变量
- 支持 `.env` 文件加载
- 包含数据库、JWT、Redis、CORS 等配置

#### 3.2.2 依赖注入 (core/dependencies.py)
- `get_db()`: 数据库会话管理
- `get_current_user_id()`: 获取当前登录用户
- `get_optional_user_id()`: 可选认证支持

#### 3.2.3 安全工具 (core/security.py)
- `hash_password()`: 密码哈希
- `verify_password()`: 密码验证
- `create_access_token()`: 创建访问令牌
- `create_refresh_token()`: 创建刷新令牌
- `decode_token()`: 令牌解码验证

#### 3.2.4 异常处理 (core/exceptions.py)
- `AppException`: 应用基础异常
- `UnauthorizedException`: 未授权异常
- `ForbiddenException`: 禁止访问异常
- `NotFoundException`: 资源未找到异常
- `ValidationException`: 数据验证异常
- `ConflictException`: 冲突异常
- `AuthenticationException`: 认证失败异常
- `AccountLockedException`: 账户锁定异常

#### 3.2.5 日志配置 (core/logging.py)
- `setup_logging()`: 初始化日志配置
- `get_logger()`: 获取指定名称的日志器
- `ColoredFormatter`: 彩色日志格式化器（控制台）
- `RequestFormatter`: 请求日志格式化器
- 支持控制台输出和文件输出
- 支持按日期轮转日志文件
- 错误日志单独存储到 `*_error.log` 文件

#### 3.2.6 请求日志中间件 (middleware/logging_middleware.py)
- `RequestLoggingMiddleware`: 自动记录所有 HTTP 请求
- 记录请求方法、路径、状态码、耗时
- 为每个请求生成唯一请求ID
- 在响应头中返回 `X-Request-ID` 和 `X-Response-Time`

### 3.3 数据模型设计

#### 3.3.1 基础模型 (models/base.py)
- `Base`: SQLAlchemy 声明式基类
- `IDMixin`: 自增主键混入
- `TimestampMixin`: 时间戳混入
- `SoftDeleteMixin`: 软删除混入
- `BaseModel`: 完整基础模型（ID + 时间戳）

#### 3.3.2 模型关系图

```
User (用户)
  ├── RefreshToken (刷新令牌) [1:N]
  ├── TeacherAudit (讲师审核) [1:N]
  ├── AdminApplication (管理员申请) [1:N]
  ├── LearningProgress (学习进度) [1:N]
  ├── Feedback (反馈) [1:N]
  └── Message (消息) [1:N]

Course (课程)
  ├── Chapter (章节) [1:N]
  │   └── Section (小节) [1:N]
  │       └── Resource (资源) [1:N]
  ├── CourseTag (课程标签) [1:N]
  └── CourseMaterial (配套资料) [1:N]

Category (分类)
  └── Category (子分类) [自关联]

Tag (标签)
  └── CourseTag (课程标签关联)

Announcement (公告)
```

#### 3.3.3 Course 核心字段

| 字段名 | 类型 | 可空 | 说明 |
|-------|------|------|------|
| id | INTEGER | 否 | 课程主键ID |
| title | VARCHAR(200) | 否 | 课程标题 |
| subtitle | VARCHAR(300) | 是 | 课程副标题 |
| summary | VARCHAR(500) | 是 | 课程简介 |
| description | TEXT | 是 | 课程详细描述 |
| cover_url | VARCHAR(500) | 是 | 课程封面地址 |
| teacher_id | INTEGER | 否 | 创建讲师ID |
| category_id | INTEGER | 是 | 课程分类ID |
| price | FLOAT | 否 | 课程价格 |
| original_price | FLOAT | 是 | 原价 |
| level | VARCHAR(20) | 否 | 难度等级 |
| status | VARCHAR(20) | 否 | 课程状态 |
| is_free | BOOLEAN | 否 | 是否免费 |
| total_duration | INTEGER | 否 | 总时长（秒） |
| total_sections | INTEGER | 否 | 小节数量 |
| student_count | INTEGER | 否 | 学员数量 |
| rating | FLOAT | 否 | 评分 |
| rating_count | INTEGER | 否 | 评分人数 |
| published_at | DATETIME | 是 | 发布时间 |

### 3.4 API 响应格式

#### 3.4.1 统一响应结构
```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... }
}
```

#### 3.4.2 分页响应结构
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10
  }
}
```

#### 3.4.3 业务状态码
| 状态码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证错误 |
| 1001 | 用户不存在 |
| 1002 | 用户已存在 |
| 1003 | 凭证无效 |
| 1004 | 账户锁定 |
| 1005 | 验证码无效 |
| 1006 | 令牌过期 |
| 1007 | 令牌无效 |
| 2001-2005 | 课程相关错误 |
| 500 | 服务器内部错误 |

## 4. 功能模块

### 4.1 模块清单

| 模块 | 路由前缀 | API数量 | 状态 |
|------|---------|--------|------|
| 健康检查 | /health, /ping | 2 | ✅ 完成 |
| 用户认证 | /auth | 7 | ✅ 完成 |
| 用户管理 | /users | 11 | ✅ 完成 |
| 课程管理 | /courses | 12 | ✅ 完成 |
| 课程内容 | /courses/{id}/chapters... | 10 | ✅ 完成 |
| 学习模块 | /learning | 6 | ✅ 完成 |
| 反馈管理 | /feedbacks | 4 | ✅ 完成 |
| 消息管理 | /messages | 7 | ✅ 完成 |
| 分类管理 | /categories | 4 | ✅ 完成 |
| 标签管理 | /tags | 2 | ✅ 完成 |
| 公告管理 | /announcements | 3 | ✅ 完成 |

### 4.2 模块详情

#### 4.2.1 用户认证模块 (auth.py)
| 接口 | 方法 | 路径 | 认证 |
|------|------|------|------|
| 用户注册 | POST | /auth/register | 否 |
| 用户登录 | POST | /auth/login | 否 |
| 退出登录 | POST | /auth/logout | 是 |
| 刷新令牌 | POST | /auth/refresh | 否 |
| 获取验证码 | GET | /auth/captcha | 否 |
| 发送邮箱验证码 | POST | /auth/send-email-code | 否 |
| 密码找回 | POST | /auth/reset-password | 否 |

#### 4.2.2 用户管理模块 (users.py)
| 接口 | 方法 | 路径 | 认证 |
|------|------|------|------|
| 获取当前用户 | GET | /users/me | 是 |
| 更新个人信息 | POST | /users/me | 是 |
| 修改密码 | POST | /users/me/change-password | 是 |
| 学习记录 | GET | /users/me/learning-records | 是 |
| 用户列表 | GET | /users | 是(管理员) |
| 更新用户状态 | POST | /users/{id}/status | 是(管理员) |
| 删除用户 | POST | /users/{id} | 是(管理员) |
| 讲师审核列表 | GET | /users/teacher-audits | 是(管理员) |
| 审核讲师 | POST | /users/teacher-audits/{id}/review | 是(管理员) |
| 管理员申请列表 | GET | /users/admin-applications | 是(管理员) |
| 审核管理员申请 | POST | /users/admin-applications/{id}/review | 是(管理员) |

#### 4.2.3 课程管理模块 (courses.py)
| 接口 | 方法 | 路径 | 认证 |
|------|------|------|------|
| 课程列表 | GET | /courses | 否 |
| 课程搜索 | GET | /courses/search | 否 |
| 首页课程 | GET | /courses/homepage | 否 |
| 我的课程 | GET | /courses/my-courses | 是 |
| 课程详情 | GET | /courses/{id} | 否 |
| 创建课程 | POST | /courses | 是 |
| 更新课程 | POST | /courses/{id} | 是 |
| 发布课程 | POST | /courses/{id}/publish | 是 |
| 下架课程 | POST | /courses/{id}/archive | 是 |
| 删除课程 | DELETE | /courses/{id} | 是 |
| 上传资料 | POST | /courses/{id}/materials | 是 |
| 删除资料 | DELETE | /courses/{id}/materials/{mid} | 是 |

#### 4.2.4 课程内容模块 (content.py)
| 接口 | 方法 | 路径 | 认证 |
|------|------|------|------|
| 章节列表 | GET | /courses/{id}/chapters | 否 |
| 创建章节 | POST | /courses/{id}/chapters | 是 |
| 更新章节 | POST | /courses/{id}/chapters/{cid} | 是 |
| 删除章节 | DELETE | /courses/{id}/chapters/{cid} | 是 |
| 小节列表 | GET | /courses/{id}/chapters/{cid}/sections | 否 |
| 创建小节 | POST | /courses/{id}/chapters/{cid}/sections | 是 |
| 更新小节 | POST | /courses/{id}/chapters/{cid}/sections/{sid} | 是 |
| 删除小节 | DELETE | /courses/{id}/chapters/{cid}/sections/{sid} | 是 |
| 上传资源 | POST | /courses/{id}/sections/{sid}/resources | 是 |
| 删除资源 | DELETE | /courses/{id}/sections/{sid}/resources/{rid} | 是 |

#### 4.2.5 学习模块 (learning.py)
| 接口 | 方法 | 路径 | 认证 |
|------|------|------|------|
| 开始学习 | POST | /learning/courses/{id}/start | 是 |
| 保存进度 | POST | /learning/progress | 是 |
| 获取进度 | GET | /learning/progress | 是 |
| 继续学习 | GET | /learning/courses/{id}/continue | 是 |
| 获取播放地址 | GET | /learning/resources/{id}/play | 是 |
| 文档预览 | GET | /learning/resources/{id}/preview | 是 |

#### 4.2.6 反馈管理模块 (feedbacks.py)
| 接口 | 方法 | 路径 | 认证 |
|------|------|------|------|
| 提交反馈 | POST | /feedbacks | 是 |
| 反馈列表 | GET | /feedbacks | 是 |
| 反馈详情 | GET | /feedbacks/{id} | 是 |
| 处理反馈 | POST | /feedbacks/{id}/process | 是(管理员) |

#### 4.2.7 消息管理模块 (messages.py)
| 接口 | 方法 | 路径 | 认证 |
|------|------|------|------|
| 消息列表 | GET | /messages | 是 |
| 消息详情 | GET | /messages/{id} | 是 |
| 标记已读 | POST | /messages/{id}/read | 是 |
| 批量已读 | POST | /messages/mark-all-read | 是 |
| 删除消息 | DELETE | /messages/{id} | 是 |
| 未读数量 | GET | /messages/unread-count | 是 |
| 发送消息 | POST | /messages/send | 是(管理员) |

#### 4.2.8 系统管理模块
| 模块 | 接口数量 | 说明 |
|------|---------|------|
| 分类管理 (categories.py) | 4 | 分类CRUD |
| 标签管理 (tags.py) | 2 | 标签列表、创建 |
| 公告管理 (announcements.py) | 3 | 公告列表、详情、有效公告 |

## 5. 安全设计

### 5.1 认证机制
- JWT Bearer Token 认证
- access_token 有效期: 24小时
- refresh_token 有效期: 7天（记住我: 30天）

### 5.2 密码安全
- bcrypt 加密（rounds=12）
- 登录失败锁定机制（5次错误锁定30分钟）

### 5.3 验证码
- 图形验证码: 5分钟有效期
- 邮箱验证码: 10分钟有效期

## 6. 部署配置

### 6.1 环境变量
```bash
# 应用配置
APP_NAME=在线学习平台
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# 数据库
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_FILE_PREFIX=app
LOG_BACKUP_COUNT=30
```

### 6.2 启动命令
```bash
# 开发环境
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 7. API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
