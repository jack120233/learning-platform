# pytest+httpx 测试计划

## 1. 测试概述

### 1.1 测试目标
使用 pytest + httpx + pytest-asyncio 对在线学习平台后端 API 进行全面测试，确保各功能模块的正确性和稳定性。

### 1.2 测试范围
覆盖所有已实现的 API 接口（共 68 个端点），包括：
- 用户认证模块 (7个接口)
- 用户管理模块 (11个接口)
- 课程管理模块 (12个接口)
- 课程内容模块 (10个接口)
- 学习模块 (6个接口)
- 反馈管理模块 (4个接口)
- 消息管理模块 (7个接口)
- 系统管理模块 (9个接口)
- 健康检查模块 (2个接口)

### 1.3 技术栈
- **测试框架**: pytest >= 8.0.0
- **异步支持**: pytest-asyncio >= 0.23.0
- **HTTP客户端**: httpx >= 0.26.0
- **测试覆盖率**: pytest-cov

## 2. 测试目录结构

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置和共享 fixtures
│   ├── test_health.py           # 健康检查测试
│   ├── test_auth.py             # 认证模块测试
│   ├── test_users.py            # 用户管理测试
│   ├── test_courses.py          # 课程管理测试
│   ├── test_content.py          # 课程内容测试
│   ├── test_learning.py         # 学习模块测试
│   ├── test_feedbacks.py        # 反馈管理测试
│   ├── test_messages.py         # 消息管理测试
│   ├── test_categories.py       # 分类管理测试
│   ├── test_tags.py             # 标签管理测试
│   ├── test_announcements.py    # 公告管理测试
│   └── fixtures/
│       ├── __init__.py
│       ├── db.py                # 数据库 fixtures
│       ├── users.py             # 用户测试数据
│       ├── courses.py           # 课程测试数据
│       └── auth.py              # 认证 fixtures
```

## 3. 测试基础设施

### 3.1 conftest.py 核心配置

```python
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.dependencies import get_db
from app.models.base import Base

# 测试数据库 URL（使用内存 SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

### 3.2 用户认证 Fixtures

```python
# tests/fixtures/auth.py

import pytest_asyncio
from httpx import AsyncClient
from app.models.user import User
from app.core.security import hash_password


@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("Test123456"),
        role="student",
        status="active",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session) -> User:
    """创建测试管理员"""
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("Admin123456"),
        role="admin",
        status="active",
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """获取认证头"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Test123456"},
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, test_admin: User) -> dict:
    """获取管理员认证头"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123456"},
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## 4. 测试用例设计

### 4.1 测试优先级

| 优先级 | 说明 | 测试类型 |
|-------|------|---------|
| P0 | 核心功能，必须通过 | 正向流程测试 |
| P1 | 重要功能 | 边界条件测试 |
| P2 | 一般功能 | 异常场景测试 |
| P3 | 可选功能 | 性能/并发测试 |

### 4.2 测试用例清单

#### 4.2.1 健康检查模块 (test_health.py)

| 用例ID | 用例名称 | 优先级 | 测试步骤 |
|--------|---------|-------|---------|
| H001 | 健康检查成功 | P0 | GET /health，验证返回200 |
| H002 | Ping检查成功 | P0 | GET /ping，验证返回pong |

```python
class TestHealthCheck:
    """健康检查测试"""

    async def test_health_check(self, client: AsyncClient):
        """测试健康检查接口"""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "服务运行正常"

    async def test_ping(self, client: AsyncClient):
        """测试Ping接口"""
        response = await client.get("/api/v1/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"
```

#### 4.2.2 用户认证模块 (test_auth.py)

| 用例ID | 用例名称 | 优先级 | 测试场景 |
|--------|---------|-------|---------|
| A001 | 用户注册成功 | P0 | 正确信息注册 |
| A002 | 注册用户名重复 | P1 | 已存在用户名 |
| A003 | 注册邮箱重复 | P1 | 已存在邮箱 |
| A004 | 注册参数验证 | P1 | 缺少必填字段 |
| A005 | 用户登录成功 | P0 | 正确凭证登录 |
| A006 | 登录密码错误 | P1 | 错误密码 |
| A007 | 登录用户不存在 | P1 | 不存在的用户 |
| A008 | 账户锁定测试 | P2 | 连续5次错误 |
| A009 | 获取验证码 | P0 | 获取图形验证码 |
| A010 | 发送邮箱验证码 | P1 | 发送验证邮件 |
| A011 | 刷新令牌 | P0 | 使用refresh_token |
| A012 | 退出登录 | P0 | 注销用户 |
| A013 | 密码重置 | P1 | 通过邮箱重置 |

```python
class TestAuth:
    """用户认证测试"""

    async def test_register_success(self, client: AsyncClient):
        """测试用户注册成功"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewUser123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "newuser"

    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """测试用户名重复"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "Test123456",
            },
        )
        assert response.status_code == 409

    async def test_login_success(self, client: AsyncClient, test_user):
        """测试登录成功"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "Test123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """测试密码错误"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "WrongPassword"},
        )
        assert response.status_code == 401

    async def test_get_captcha(self, client: AsyncClient):
        """测试获取验证码"""
        response = await client.get("/api/v1/auth/captcha")
        assert response.status_code == 200
        data = response.json()
        assert "captcha_id" in data["data"]
        assert "captcha_image" in data["data"]

    async def test_refresh_token(self, client: AsyncClient, test_user):
        """测试刷新令牌"""
        # 先登录获取 refresh_token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "Test123456"},
        )
        refresh_token = login_response.json()["data"]["refresh_token"]

        # 使用 refresh_token 获取新 token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    async def test_logout(self, client: AsyncClient, auth_headers):
        """测试退出登录"""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
```

#### 4.2.3 用户管理模块 (test_users.py)

| 用例ID | 用例名称 | 优先级 | 测试场景 |
|--------|---------|-------|---------|
| U001 | 获取当前用户信息 | P0 | 认证用户获取信息 |
| U002 | 更新个人信息 | P0 | 修改昵称/头像 |
| U003 | 修改密码成功 | P0 | 正确旧密码 |
| U004 | 修改密码失败 | P1 | 错误旧密码 |
| U005 | 获取学习记录 | P0 | 分页查询 |
| U006 | 用户列表查询 | P1 | 管理员权限 |
| U007 | 用户搜索 | P1 | 关键词搜索 |
| U008 | 禁用用户 | P1 | 管理员操作 |
| U009 | 删除用户 | P2 | 管理员操作 |
| U010 | 讲师审核列表 | P1 | 管理员权限 |
| U011 | 审核讲师申请 | P1 | 通过/拒绝 |

#### 4.2.4 课程管理模块 (test_courses.py)

| 用例ID | 用例名称 | 优先级 | 测试场景 |
|--------|---------|-------|---------|
| C001 | 课程列表查询 | P0 | 分页获取 |
| C002 | 课程搜索 | P0 | 关键词搜索 |
| C003 | 首页课程推荐 | P0 | 获取推荐 |
| C004 | 我的课程列表 | P0 | 讲师查看 |
| C005 | 课程详情 | P0 | 获取详情 |
| C006 | 创建课程 | P0 | 讲师创建 |
| C007 | 更新课程 | P0 | 讲师更新 |
| C008 | 发布课程 | P0 | 草稿发布 |
| C009 | 下架课程 | P1 | 已发布下架 |
| C010 | 删除课程 | P1 | 草稿删除 |
| C011 | 上传配套资料 | P1 | 文件上传 |
| C012 | 删除配套资料 | P1 | 文件删除 |

#### 4.2.5 课程内容模块 (test_content.py)

| 用例ID | 用例名称 | 优先级 | 测试场景 |
|--------|---------|-------|---------|
| CT001 | 章节列表 | P0 | 获取章节 |
| CT002 | 创建章节 | P0 | 新增章节 |
| CT003 | 更新章节 | P0 | 修改章节 |
| CT004 | 删除章节 | P1 | 删除空章节 |
| CT005 | 删除非空章节 | P2 | 存在小节 |
| CT006 | 小节列表 | P0 | 获取小节 |
| CT007 | 创建小节 | P0 | 新增小节 |
| CT008 | 更新小节 | P0 | 修改小节 |
| CT009 | 删除小节 | P1 | 删除空小节 |
| CT010 | 上传资源 | P0 | 上传视频/文档 |
| CT011 | 删除资源 | P1 | 删除资源 |

#### 4.2.6 学习模块 (test_learning.py)

| 用例ID | 用例名称 | 优先级 | 测试场景 |
|--------|---------|-------|---------|
| L001 | 开始学习 | P0 | 首次学习课程 |
| L002 | 保存进度 | P0 | 保存学习进度 |
| L003 | 获取进度 | P0 | 查询进度 |
| L004 | 继续学习 | P0 | 获取上次位置 |
| L005 | 获取播放地址 | P0 | 视频播放 |
| L006 | 文档预览 | P0 | 在线预览 |

#### 4.2.7 反馈管理模块 (test_feedbacks.py)

| 用例ID | 用例名称 | 优先级 | 测试场景 |
|--------|---------|-------|---------|
| F001 | 提交反馈 | P0 | 用户提交 |
| F002 | 反馈列表 | P0 | 用户查看 |
| F003 | 反馈详情 | P0 | 查看详情 |
| F004 | 处理反馈 | P1 | 管理员回复 |

#### 4.2.8 消息管理模块 (test_messages.py)

| 用例ID | 用例名称 | 优先级 | 测试场景 |
|--------|---------|-------|---------|
| M001 | 消息列表 | P0 | 分页获取 |
| M002 | 消息详情 | P0 | 查看详情 |
| M003 | 标记已读 | P0 | 单条已读 |
| M004 | 批量已读 | P0 | 全部已读 |
| M005 | 删除消息 | P1 | 删除单条 |
| M006 | 未读数量 | P0 | 统计未读 |
| M007 | 发送系统消息 | P1 | 管理员发送 |

#### 4.2.9 系统管理模块

**分类管理 (test_categories.py)**

| 用例ID | 用例名称 | 优先级 |
|--------|---------|-------|
| CA001 | 分类列表 | P0 |
| CA002 | 创建分类 | P0 |
| CA003 | 更新分类 | P0 |
| CA004 | 删除分类 | P1 |

**标签管理 (test_tags.py)**

| 用例ID | 用例名称 | 优先级 |
|--------|---------|-------|
| T001 | 标签列表 | P0 |
| T002 | 创建标签 | P0 |

**公告管理 (test_announcements.py)**

| 用例ID | 用例名称 | 优先级 |
|--------|---------|-------|
| AN001 | 公告列表 | P0 |
| AN002 | 有效公告 | P0 |
| AN003 | 公告详情 | P0 |

## 5. 测试执行计划

### 5.1 阶段划分

| 阶段 | 内容 | 预计工作量 |
|------|------|-----------|
| 第一阶段 | 基础设施搭建（conftest.py, fixtures） | 1天 |
| 第二阶段 | 认证模块测试（test_auth.py） | 1天 |
| 第三阶段 | 用户管理测试（test_users.py） | 1天 |
| 第四阶段 | 课程模块测试（test_courses.py, test_content.py） | 2天 |
| 第五阶段 | 学习模块测试（test_learning.py） | 1天 |
| 第六阶段 | 其他模块测试（feedbacks, messages, system） | 1天 |
| 第七阶段 | 集成测试与覆盖率优化 | 1天 |

### 5.2 运行命令

```bash
# 运行所有测试
pytest

# 运行指定模块测试
pytest tests/test_auth.py -v

# 运行并生成覆盖率报告
pytest --cov=app --cov-report=html

# 只运行 P0 优先级测试
pytest -m p0

# 并行运行测试
pytest -n auto
```

### 5.3 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| API路由层 | >= 90% |
| 服务层 | >= 85% |
| 核心模块 | >= 80% |
| 总体 | >= 80% |

## 6. 持续集成配置

### 6.1 GitHub Actions 配置示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: learning_platform_test
        ports:
          - 3306:3306

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
```

## 7. 测试数据准备

### 7.1 用户测试数据

```python
# tests/fixtures/users.py

TEST_USERS = [
    {"username": "student1", "email": "student1@test.com", "password": "Test123456", "role": "student"},
    {"username": "student2", "email": "student2@test.com", "password": "Test123456", "role": "student"},
    {"username": "teacher1", "email": "teacher1@test.com", "password": "Test123456", "role": "teacher"},
    {"username": "admin1", "email": "admin1@test.com", "password": "Admin123456", "role": "admin"},
]
```

### 7.2 课程测试数据

```python
# tests/fixtures/courses.py

TEST_COURSES = [
    {
        "title": "Python入门",
        "subtitle": "零基础学Python",
        "description": "适合初学者的Python课程",
        "price": 99.0,
        "level": "beginner",
        "is_free": False,
    },
    {
        "title": "FastAPI实战",
        "subtitle": "现代Python Web开发",
        "description": "FastAPI框架完整教程",
        "price": 199.0,
        "level": "intermediate",
        "is_free": False,
    },
]
```

## 8. 注意事项

1. **异步测试**: 所有数据库操作和API调用都需要使用 `async/await`
2. **测试隔离**: 每个测试用例应该独立，不依赖其他测试的结果
3. **数据清理**: 测试后清理创建的数据，或使用事务回滚
4. **Mock外部服务**: 邮件发送、文件存储等外部服务应该Mock
5. **敏感信息**: 测试中不要使用真实的生产数据或密钥