# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个在线学习平台的需求文档项目，包含完整的技术规格说明和API设计文档。项目目前处于规划阶段，文档可作为后续开发的指导依据。

## 技术栈

- **后端框架**: Python + FastAPI 0.110+
- **ORM**: SQLAlchemy 2.0+（支持异步操作）
- **数据验证**: Pydantic 2.6+
- **认证**: JWT（python-jose），bcrypt密码加密
- **缓存**: Redis（会话管理、验证码、频率限制）
- **搜索**: Meilisearch（课程全文搜索）
- **文件存储**: OSS/S3兼容存储

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

### 文件组织建议
```
backend/app/
├── api/v1/           # API路由
├── schemas/          # Pydantic模型
├── services/         # 业务逻辑
├── models/           # 数据库模型
└── core/             # 核心配置、安全、依赖
```

## 模块文档索引

| 文档 | 模块 | API数量 |
|------|------|---------|
| 2.用户认证模块详情文档.md | 注册、登录、令牌管理、验证码 | 7 |
| 3.用户管理模块详情.md | 用户信息、密码修改、学习记录 | 11 |
| 4.课程管理模块详情.md | 课程CRUD、发布、归档、搜索 | 12 |
| 5.课程内容模块详情.md | 章节、小节、资源管理 | 10 |
| 6.学习模块详情.md | 学习进度、视频播放 | 6 |
| 7.反馈消息模块详情.md | 反馈、通知、消息 | 11 |
| 8.系统管理模块详情.md | 分类、标签、公告管理 | - |

## 关键安全配置

- 密码加密: bcrypt（rounds=12）
- access_token有效期: 24小时
- refresh_token有效期: 7天（记住我: 30天）
- 图形验证码: 5分钟有效期
- 邮箱验证码: 10分钟有效期
- 登录失败锁定: 连续5次错误锁定30分钟

## Spec Workflow

项目使用 `.spec-workflow/` 目录管理工作流文档：
- `specs/` - 规格文档
- `approvals/` - 审批记录
- `archive/` - 归档文档
- `templates/` - 文档模板（需求、设计、技术、任务等）