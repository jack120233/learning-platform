"""pytest 配置和共享 fixtures

提供测试所需的基础设施，包括数据库、客户端、用户认证等。
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.dependencies import get_db
from app.models.base import Base

# 测试数据库 URL（使用内存 SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ==================== 事件循环配置 ====================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建会话级别的事件循环

    使用 session 作用域，确保所有异步测试共享同一个事件循环。

    Yields:
        asyncio.AbstractEventLoop: 事件循环实例
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ==================== 数据库配置 ====================

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎

    使用内存 SQLite 数据库进行测试，每次会话创建一次。
    在会话结束时自动清理所有表。

    Yields:
        AsyncEngine: 异步数据库引擎
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话

    每个测试用例使用独立的数据库会话。

    Args:
        test_engine: 测试数据库引擎

    Yields:
        AsyncSession: 异步数据库会话
    """
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        yield session
        # 测试结束后回滚任何未提交的更改
        await session.rollback()


# ==================== HTTP 客户端配置 ====================

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试 HTTP 客户端

    创建一个异步 HTTP 客户端，自动注入测试数据库会话。

    Args:
        db_session: 数据库会话

    Yields:
        AsyncClient: 异步 HTTP 客户端
    """
    async def override_get_db():
        yield db_session

    # 覆盖数据库依赖
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 清理依赖覆盖
    app.dependency_overrides.clear()


# ==================== 用户 Fixtures ====================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """创建测试普通用户

    创建一个学生角色的测试用户，用于普通用户权限测试。

    Args:
        db_session: 数据库会话

    Returns:
        User: 测试用户实例
    """
    from sqlalchemy import select
    from app.models.user import User
    from app.core.security import hash_password

    # 检查用户是否已存在
    result = await db_session.execute(
        select(User).where(User.username == "testuser")
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            username="testuser",
            email="testuser@example.com",
            password_hash=hash_password("Test123456"),
            nickname="测试用户",
            role="student",
            status="active",
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_teacher(db_session: AsyncSession):
    """创建测试讲师用户

    创建一个讲师角色的测试用户，用于讲师权限测试。

    Args:
        db_session: 数据库会话

    Returns:
        User: 测试讲师实例
    """
    from app.models.user import User
    from app.core.security import hash_password

    teacher = User(
        username="testteacher",
        email="teacher@example.com",
        password_hash=hash_password("Teacher123456"),
        nickname="测试讲师",
        role="teacher",
        status="active",
    )
    db_session.add(teacher)
    await db_session.flush()
    await db_session.refresh(teacher)
    return teacher


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession):
    """创建测试管理员用户

    创建一个管理员角色的测试用户，用于管理员权限测试。

    Args:
        db_session: 数据库会话

    Returns:
        User: 测试管理员实例
    """
    from app.models.user import User
    from app.core.security import hash_password

    admin = User(
        username="testadmin",
        email="admin@example.com",
        password_hash=hash_password("Admin123456"),
        nickname="测试管理员",
        role="admin",
        status="active",
    )
    db_session.add(admin)
    await db_session.flush()
    await db_session.refresh(admin)
    return admin


# ==================== 认证 Headers ====================

@pytest_asyncio.fixture
async def user_token(client: AsyncClient, test_user) -> str:
    """获取普通用户访问令牌

    Args:
        client: HTTP 客户端
        test_user: 测试用户

    Returns:
        str: 访问令牌
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Test123456"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def teacher_token(client: AsyncClient, test_teacher) -> str:
    """获取讲师访问令牌

    Args:
        client: HTTP 客户端
        test_teacher: 测试讲师

    Returns:
        str: 访问令牌
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testteacher", "password": "Teacher123456"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_admin) -> str:
    """获取管理员访问令牌

    Args:
        client: HTTP 客户端
        test_admin: 测试管理员

    Returns:
        str: 访问令牌
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "Admin123456"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
def auth_headers(user_token: str) -> dict:
    """获取普通用户认证头

    Args:
        user_token: 用户令牌

    Returns:
        dict: 包含 Authorization 头的字典
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest_asyncio.fixture
def teacher_headers(teacher_token: str) -> dict:
    """获取讲师认证头

    Args:
        teacher_token: 讲师令牌

    Returns:
        dict: 包含 Authorization 头的字典
    """
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest_asyncio.fixture
def admin_headers(admin_token: str) -> dict:
    """获取管理员认证头

    Args:
        admin_token: 管理员令牌

    Returns:
        dict: 包含 Authorization 头的字典
    """
    return {"Authorization": f"Bearer {admin_token}"}


# ==================== 课程相关 Fixtures ====================

@pytest_asyncio.fixture
async def test_category(db_session: AsyncSession):
    """创建测试分类

    Args:
        db_session: 数据库会话

    Returns:
        Category: 测试分类实例
    """
    from app.models.category import Category

    category = Category(
        name="测试分类",
        slug="test-category",
        description="这是一个测试分类",
        is_active=True,
        sort_order=1,
    )
    db_session.add(category)
    await db_session.flush()
    await db_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_course(db_session: AsyncSession, test_teacher, test_category):
    """创建测试课程

    Args:
        db_session: 数据库会话
        test_teacher: 测试讲师
        test_category: 测试分类

    Returns:
        Course: 测试课程实例
    """
    from app.models.course import Course

    course = Course(
        title="测试课程",
        subtitle="这是一个测试课程",
        description="测试课程描述",
        teacher_id=test_teacher.id,
        category_id=test_category.id,
        price=99.0,
        original_price=199.0,
        level="beginner",
        status="published",
        is_free=False,
        total_duration=3600,
        total_sections=10,
    )
    db_session.add(course)
    await db_session.flush()
    await db_session.refresh(course)
    return course


# ==================== 工具函数 ====================

def assert_success_response(response, message: str = None):
    """断言成功响应

    Args:
        response: HTTP 响应
        message: 可选的成功消息断言
    """
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    if message:
        assert data["message"] == message
    return data


def assert_error_response(response, expected_code: int = None):
    """断言错误响应

    Args:
        response: HTTP 响应
        expected_code: 预期的错误码
    """
    data = response.json()
    if expected_code:
        assert data["code"] == expected_code
    return data