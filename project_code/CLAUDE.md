# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个在线学习平台的后端 API 服务，提供用户管理、课程管理、学习进度跟踪、反馈消息等功能模块。项目已完成核心 API 实现，包含完整的测试套件。

## 根级协作入口

如果 Claude 是从工作区根目录 `E:\video_project\proj_ui` 启动的，必须先遵循根级 `E:\video_project\proj_ui\CLAUDE.md` 的目录路由规则，再下钻到本文件。

本文件只负责 `E:\video_project\proj_ui\project_code` 后端目录内的实现规则，不负责前端目录定位。

## 技术栈

- **后端框架**: Python + FastAPI 0.110+
- **ORM**: SQLAlchemy 2.0+（支持异步操作）
- **数据验证**: Pydantic 2.6+
- **认证**: JWT（python-jose），bcrypt密码加密
- **缓存**: Redis（会话管理、验证码、频率限制）
- **搜索**: Meilisearch（课程全文搜索）
- **文件存储**: OSS/S3兼容存储
- **测试**: pytest + pytest-asyncio + httpx

## 架构约定

### API规范
- 统一前缀: `/api/v1/`
- 响应格式: `{ "code": int, "message": str, "data": object }`
- 认证方式: Bearer Token（Authorization头）

### 权限模型
- 三种角色: student（学员）、teacher（讲师）、admin（管理员）
- RBAC权限控制，角色决定可访问的API范围

### 课程结构
四级层次: Course → Chapter → Section → Resource

### 项目结构
```
E:\video_project\proj_ui\project_code\backend\
├── app/                    # 应用主目录
│   ├── api/v1/             # API路由（12个模块，80个端点）
│   ├── schemas/            # Pydantic模型
│   ├── services/           # 业务逻辑
│   ├── models/             # 数据库模型
│   └── core/               # 核心配置、安全、依赖
├── tests/                  # 测试目录
│   ├── conftest.py         # 测试配置和fixtures
│   ├── test_auth.py        # 认证模块测试
│   ├── test_courses.py     # 课程管理测试
│   ├── test_content.py     # 课程内容测试
│   ├── test_feedbacks.py   # 反馈消息测试
│   ├── test_health.py      # 健康检查测试
│   ├── test_learning.py    # 学习模块测试
│   ├── test_system.py      # 系统管理测试
│   ├── test_uploads.py     # 上传模块测试
│   └── test_users.py       # 用户管理测试
└── requirements.txt        # 依赖清单
```

## 文档索引

### 核心文档
| 文档 | 说明 |
|------|------|
| [architecture.md](docs/architecture.md) | 项目架构文档（位于 `E:\video_project\proj_ui\project_code\docs\architecture.md`） |
| [api-endpoint-inventory.md](docs/api-endpoint-inventory.md) | 实际已挂载 API 接口清单（80个端点，位于 `E:\video_project\proj_ui\project_code\docs\api-endpoint-inventory.md`） |
| [test-plan.md](docs/test-plan.md) | pytest+httpx 测试计划（位于 `E:\video_project\proj_ui\project_code\docs\test-plan.md`） |
| [api-testing-guide.md](docs/api-testing-guide.md) | API 手动测试指南（位于 `E:\video_project\proj_ui\project_code\docs\api-testing-guide.md`） |
| [worktree-guide.md](docs/worktree-guide.md) | Git Worktree 使用指南（位于 `E:\video_project\proj_ui\project_code\docs\worktree-guide.md`） |

### 需求文档
| 文档 | 模块 | API数量 |
|------|------|---------|
| 2.用户认证模块详情文档.md | 注册、登录、令牌管理、验证码 | 7 |
| 3.用户管理模块详情.md | 用户信息、密码修改、学习记录 | 11 |
| 4.课程管理模块详情.md | 课程CRUD、发布、归档、搜索 | 12 |
| 5.课程内容模块详情.md | 章节、小节、资源管理 | 10 |
| 6.学习模块详情.md | 学习进度、视频播放 | 6 |
| 7.反馈消息模块详情.md | 反馈、通知、消息 | 11 |
| 8.系统管理模块详情.md | 分类、标签、公告管理 | - |

## 测试

在 `E:\video_project\proj_ui\project_code\backend` 目录下执行：

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定模块
pytest tests/test_auth.py -v

# 运行单个测试用例
pytest tests/test_auth.py::test_register -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
# 报告位置: E:\video_project\proj_ui\project_code\backend\htmlcov\index.html
```

测试使用内存 SQLite 数据库，无需额外配置。详见 `E:\video_project\proj_ui\project_code\backend\tests\conftest.py`。

## 关键安全配置

- 密码加密: bcrypt（rounds=12）
- access_token有效期: 24小时
- refresh_token有效期: 7天（记住我: 30天）
- 图形验证码: 5分钟有效期
- 邮箱验证码: 10分钟有效期
- 登录失败锁定: 连续5次错误锁定30分钟

## Spec Workflow

项目使用 `E:\video_project\proj_ui\project_code\.spec-workflow\` 目录管理工作流文档：
- `E:\video_project\proj_ui\project_code\.spec-workflow\specs\` - 规格文档
- `E:\video_project\proj_ui\project_code\.spec-workflow\approvals\` - 审批记录
- `E:\video_project\proj_ui\project_code\.spec-workflow\archive\` - 归档文档
- `E:\video_project\proj_ui\project_code\.spec-workflow\templates\` - 文档模板（需求、设计、技术、任务等）

## 开发命令

在 `E:\video_project\proj_ui\project_code\backend` 目录下执行：

```bash
# 激活虚拟环境（项目根目录）
..\\.venv\\Scripts\\activate

# 启动开发服务
uvicorn app.main:app --reload --port 8000

# 查看 API 文档
# http://localhost:8000/docs

# 运行所有测试
pytest tests/ -v

# 运行指定模块测试
pytest tests/test_auth.py -v

# 运行单个测试用例
pytest tests/test_auth.py::test_register -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 初始化数据库表结构
python scripts/init_db.py

# 导入种子数据（测试账号）
python scripts/seed_data.py
```

### 测试账号

种子数据导入后可用，AI 联调和浏览器测试应直接使用以下账号，不要再要求用户手动输入账号密码：

| 角色 | 用户名 | 密码 | 邮箱 |
|------|--------|------|------|
| 管理员 | `admin1` | `Admin123456` | `admin1@example.com` |
| 教师 | `teacher1` | `Test123456` | `teacher1@example.com` |
| 教师 | `teacher2` | `Test123456` | `teacher2@example.com` |
| 教师 | `teacher3` | `Test123456` | `teacher3@example.com` |
| 教师 | `teacher4` | `Test123456` | `teacher4@example.com` |
| 教师 | `teacher5` | `Test123456` | `teacher5@example.com` |
| 教师 | `teacher6` | `Test123456` | `teacher6@example.com` |
| 学生 | `student1` | `Test123456` | `student1@example.com` |
| 学生 | `student2` | `Test123456` | `student2@example.com` |

## 文件写入规范

- 每次只写入 100～200 行，然后使用 edits 自动接收模式完成编写。
- 在新增文件或修改现有文件前，先确认是否需要同步更新 `E:\video_project\proj_ui\project_code\operations-log.md`。
- 只要本次工作产生了文件新增或文件变更，必须在 `E:\video_project\proj_ui\project_code\operations-log.md` 追加一条记录。
- 记录内容至少包含：变更时间、变更原因、涉及文件、核心改动、验证结果（如未验证需明确说明）。
- `E:\video_project\proj_ui\project_code\operations-log.md` 的记录要与实际落盘文件保持一致，后续若继续追加修改，同一任务也要补充到日志中。
