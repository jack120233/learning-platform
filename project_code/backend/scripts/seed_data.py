"""SQLite 演示种子数据脚本。

用于在标准表结构已存在时导入基础数据与演示数据。

用法:
    cd backend
    python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from typing import Any
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import AsyncSessionLocal
from app.core.security import hash_password
from app.models import (
    Announcement,
    Category,
    Chapter,
    Course,
    CourseTag,
    Resource,
    Section,
    Tag,
    User,
)


DEMO_DOCUMENT_SUBDIR = "demo-documents"
DEMO_DOCUMENT_SOURCE_DIR = Path(__file__).resolve().parent.parent / "demo_assets" / "documents"
DEMO_COURSE_CONTENT_SPECS: dict[str, tuple[dict[str, Any], ...]] = {
    "Python入门": (
        {
            "title": "第一章：Python入门基础",
            "description": "基础概念和环境搭建",
            "sort_order": 1,
            "sections": (
                {
                    "title": "第1节：理论讲解",
                    "description": "理论知识讲解",
                    "sort_order": 1,
                    "duration": 0,
                    "resource_title": "Python入门 第一章 理论讲义",
                    "document_file_name": "python-intro-ch1-theory.md",
                },
                {
                    "title": "第1节：实践练习",
                    "description": "动手实践",
                    "sort_order": 2,
                    "duration": 0,
                    "resource_title": "Python入门 第一章 实践讲义",
                    "document_file_name": "python-intro-ch1-practice.md",
                },
            ),
        },
        {
            "title": "第二章：核心知识",
            "description": "核心概念和基本操作",
            "sort_order": 2,
            "sections": (
                {
                    "title": "第2节：理论讲解",
                    "description": "理论知识讲解",
                    "sort_order": 1,
                    "duration": 0,
                    "resource_title": "Python入门 第二章 理论讲义",
                    "document_file_name": "python-intro-ch2-theory.md",
                },
                {
                    "title": "第2节：实践练习",
                    "description": "动手实践",
                    "sort_order": 2,
                    "duration": 0,
                    "resource_title": "Python入门 第二章 实践讲义",
                    "document_file_name": "python-intro-ch2-practice.md",
                },
            ),
        },
    ),
    "FastAPI实战": (
        {
            "title": "第一章：FastAPI实战基础",
            "description": "基础概念和环境搭建",
            "sort_order": 1,
            "sections": (
                {
                    "title": "第1节：理论讲解",
                    "description": "理论知识讲解",
                    "sort_order": 1,
                    "duration": 0,
                    "resource_title": "FastAPI实战 第一章 理论讲义",
                    "document_file_name": "fastapi-ch1-theory.md",
                },
                {
                    "title": "第1节：实践练习",
                    "description": "动手实践",
                    "sort_order": 2,
                    "duration": 0,
                    "resource_title": "FastAPI实战 第一章 实践讲义",
                    "document_file_name": "fastapi-ch1-practice.md",
                },
            ),
        },
        {
            "title": "第二章：核心知识",
            "description": "核心概念和基本操作",
            "sort_order": 2,
            "sections": (
                {
                    "title": "第2节：理论讲解",
                    "description": "理论知识讲解",
                    "sort_order": 1,
                    "duration": 0,
                    "resource_title": "FastAPI实战 第二章 理论讲义",
                    "document_file_name": "fastapi-ch2-theory.md",
                },
                {
                    "title": "第2节：实践练习",
                    "description": "动手实践",
                    "sort_order": 2,
                    "duration": 0,
                    "resource_title": "FastAPI实战 第二章 实践讲义",
                    "document_file_name": "fastapi-ch2-practice.md",
                },
            ),
        },
    ),
}
EXPECTED_DEMO_DOCUMENT_FILE_NAMES: tuple[str, ...] = tuple(
    str(section_spec["document_file_name"])
    for course_specs in DEMO_COURSE_CONTENT_SPECS.values()
    for chapter_spec in course_specs
    for section_spec in chapter_spec["sections"]
)


def get_demo_document_source_dir() -> Path:
    """返回仓库内演示文档源目录。"""
    return DEMO_DOCUMENT_SOURCE_DIR


def get_demo_document_runtime_dir() -> Path:
    """返回运行时演示文档目录。"""
    return settings.resolved_upload_dir / DEMO_DOCUMENT_SUBDIR


def get_expected_demo_document_file_names() -> tuple[str, ...]:
    """返回标准演示文档文件名列表。"""
    return EXPECTED_DEMO_DOCUMENT_FILE_NAMES


def get_demo_document_runtime_paths() -> list[Path]:
    """返回运行时演示文档绝对路径列表。"""
    runtime_dir = get_demo_document_runtime_dir()
    return [runtime_dir / file_name for file_name in EXPECTED_DEMO_DOCUMENT_FILE_NAMES]


def get_demo_document_runtime_url(file_name: str) -> str:
    """将演示文档文件名映射为上传访问地址。"""
    return f"{settings.upload_url_prefix.rstrip('/')}/{DEMO_DOCUMENT_SUBDIR}/{file_name}"


def resolve_demo_document_runtime_path(file_url: str) -> Path:
    """将演示文档访问地址映射为运行时文件路径。"""
    prefix = f"{settings.upload_url_prefix.rstrip('/')}/{DEMO_DOCUMENT_SUBDIR}/"
    if not file_url.startswith(prefix):
        raise ValueError(f"不是演示文档地址: {file_url}")
    return get_demo_document_runtime_dir() / file_url.removeprefix(prefix)


def ensure_demo_document_assets() -> list[Path]:
    """将仓库内演示文档复制到运行时上传目录。"""
    source_dir = get_demo_document_source_dir()
    runtime_dir = get_demo_document_runtime_dir()
    runtime_dir.mkdir(parents=True, exist_ok=True)

    copied_paths: list[Path] = []
    for file_name in EXPECTED_DEMO_DOCUMENT_FILE_NAMES:
        source_path = source_dir / file_name
        if not source_path.is_file():
            raise FileNotFoundError(f"缺少演示文档源文件: {source_path}")
        target_path = runtime_dir / file_name
        shutil.copy2(source_path, target_path)
        copied_paths.append(target_path)
    return copied_paths


async def _get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_category_by_slug(session: AsyncSession, slug: str) -> Category | None:
    result = await session.execute(select(Category).where(Category.slug == slug))
    return result.scalar_one_or_none()


async def _get_tag_by_slug(session: AsyncSession, slug: str) -> Tag | None:
    result = await session.execute(select(Tag).where(Tag.slug == slug))
    return result.scalar_one_or_none()


async def _get_course_by_title(session: AsyncSession, title: str) -> Course | None:
    result = await session.execute(select(Course).where(Course.title == title))
    return result.scalar_one_or_none()


async def _get_announcement_by_title(session: AsyncSession, title: str) -> Announcement | None:
    result = await session.execute(select(Announcement).where(Announcement.title == title))
    return result.scalar_one_or_none()


async def seed_users(session: AsyncSession) -> list[User]:
    """创建演示账号。"""
    print("  创建演示账号...")

    seed_users_data = [
        {
            "username": "admin1",
            "email": "admin1@example.com",
            "password": "Admin123456",
            "nickname": "管理员",
            "role": "admin",
        },
        {
            "username": "teacher1",
            "email": "teacher1@example.com",
            "password": "Test123456",
            "nickname": "张老师",
            "role": "teacher",
        },
        {
            "username": "student1",
            "email": "student1@example.com",
            "password": "Test123456",
            "nickname": "学生1",
            "role": "student",
        },
    ]

    users: list[User] = []
    created_count = 0
    for item in seed_users_data:
        user = await _get_user_by_username(session, item["username"])
        if user is None:
            user = User(
                username=item["username"],
                original_username=item["username"],
                email=item["email"],
                password_hash=hash_password(item["password"]),
                nickname=item["nickname"],
                role=item["role"],
                status="active",
            )
            session.add(user)
            await session.flush()
            created_count += 1
        users.append(user)

    print(f"    新增 {created_count} 个账号，当前共 {len(users)} 个演示账号")
    return users


async def seed_categories(session: AsyncSession) -> list[Category]:
    """创建基础分类。"""
    print("  创建基础分类...")

    seeds = [
        {"name": "编程开发", "slug": "programming", "description": "软件开发相关课程", "sort_order": 1},
        {"name": "人工智能", "slug": "ai", "description": "AI和机器学习课程", "sort_order": 2},
        {"name": "数据分析", "slug": "data-analysis", "description": "数据分析和可视化课程", "sort_order": 3},
        {"name": "设计创意", "slug": "design", "description": "UI/UX设计课程", "sort_order": 4},
        {"name": "语言学习", "slug": "language", "description": "外语学习课程", "sort_order": 5},
        {"name": "智能网联", "slug": "intelligent-connected", "description": "智能网联与车路协同课程", "sort_order": 6},
    ]

    categories: list[Category] = []
    created_count = 0
    for item in seeds:
        category = await _get_category_by_slug(session, item["slug"])
        if category is None:
            category = Category(**item)
            session.add(category)
            await session.flush()
            created_count += 1
        categories.append(category)

    print(f"    新增 {created_count} 个分类")
    return categories


async def seed_tags(session: AsyncSession) -> list[Tag]:
    """创建基础标签。"""
    print("  创建基础标签...")

    seeds = [
        {"name": "Python", "slug": "python"},
        {"name": "JavaScript", "slug": "javascript"},
        {"name": "Java", "slug": "java"},
        {"name": "React", "slug": "react"},
        {"name": "机器学习", "slug": "machine-learning"},
        {"name": "深度学习", "slug": "deep-learning"},
        {"name": "前端开发", "slug": "frontend"},
        {"name": "后端开发", "slug": "backend"},
        {"name": "入门", "slug": "beginner"},
        {"name": "进阶", "slug": "advanced"},
        {"name": "智能网联", "slug": "intelligent-connected"},
    ]

    tags: list[Tag] = []
    created_count = 0
    for item in seeds:
        tag = await _get_tag_by_slug(session, item["slug"])
        if tag is None:
            tag = Tag(name=item["name"], slug=item["slug"], use_count=0)
            session.add(tag)
            await session.flush()
            created_count += 1
        tags.append(tag)

    print(f"    新增 {created_count} 个标签")
    return tags


async def seed_base_data(session: AsyncSession) -> None:
    """初始化系统基础数据。"""
    await seed_categories(session)
    await seed_tags(session)


async def _ensure_course_tags(
    session: AsyncSession,
    course: Course,
    tags: list[Tag],
    slugs: tuple[str, ...],
) -> None:
    tag_map = {tag.slug: tag for tag in tags}
    result = await session.execute(select(CourseTag.tag_id).where(CourseTag.course_id == course.id))
    existing_tag_ids = set(result.scalars().all())

    for slug in slugs:
        tag = tag_map[slug]
        if tag.id in existing_tag_ids:
            continue
        session.add(CourseTag(course_id=course.id, tag_id=tag.id))


async def seed_courses(
    session: AsyncSession,
    users: list[User],
    categories: list[Category],
    tags: list[Tag],
) -> list[Course]:
    """创建演示课程。"""
    print("  创建演示课程...")

    teacher = next(user for user in users if user.username == "teacher1")
    category_map = {category.slug: category for category in categories}

    seeds = [
        {
            "title": "Python入门",
            "subtitle": "零基础学Python",
            "summary": "从环境到基础语法",
            "description": "适合初学者的 Python 课程",
            "teacher_id": teacher.id,
            "category_id": category_map["programming"].id,
            "status": "published",
            "price": 99.0,
            "level": "beginner",
            "is_free": False,
            "published_at": datetime.now(timezone.utc),
            "tag_slugs": ("python", "beginner"),
        },
        {
            "title": "FastAPI实战",
            "subtitle": "现代Python Web开发",
            "summary": "接口设计到项目实战",
            "description": "FastAPI 框架完整教程",
            "teacher_id": teacher.id,
            "category_id": category_map["programming"].id,
            "status": "published",
            "price": 199.0,
            "level": "intermediate",
            "is_free": False,
            "published_at": datetime.now(timezone.utc) - timedelta(days=2),
            "tag_slugs": ("python", "advanced"),
        },
    ]

    courses: list[Course] = []
    created_count = 0
    for item in seeds:
        course = await _get_course_by_title(session, item["title"])
        if course is None:
            course = Course(
                title=item["title"],
                subtitle=item["subtitle"],
                summary=item["summary"],
                description=item["description"],
                teacher_id=item["teacher_id"],
                category_id=item["category_id"],
                status=item["status"],
                price=item["price"],
                level=item["level"],
                is_free=item["is_free"],
                published_at=item["published_at"],
            )
            session.add(course)
            await session.flush()
            created_count += 1
        await _ensure_course_tags(session, course, tags, item["tag_slugs"])
        courses.append(course)

    print(f"    新增 {created_count} 门课程")
    return courses


async def _seed_course_sections(
    session: AsyncSession,
    course: Course,
    chapter: Chapter,
    section_specs: list[dict[str, object]],
) -> None:
    for section_spec in section_specs:
        result = await session.execute(
            select(Section).where(
                Section.course_id == course.id,
                Section.chapter_id == chapter.id,
                Section.title == section_spec["title"],
            )
        )
        section = result.scalar_one_or_none()
        if section is None:
            section = Section(
                course_id=course.id,
                chapter_id=chapter.id,
                title=str(section_spec["title"]),
                description=str(section_spec["description"]),
                sort_order=int(section_spec["sort_order"]),
                duration=int(section_spec["duration"]),
                resource_count=1,
            )
            session.add(section)
            await session.flush()
        else:
            section.duration = int(section_spec["duration"])
            section.resource_count = 1

        result = await session.execute(
            select(Resource.id).where(Resource.section_id == section.id)
        )
        if result.scalar_one_or_none() is not None:
            continue

        session.add(
            Resource(
                course_id=course.id,
                chapter_id=chapter.id,
                section_id=section.id,
                title=str(section_spec["resource_title"]),
                type="document",
                file_url=get_demo_document_runtime_url(str(section_spec["document_file_name"])),
                duration=0,
                sort_order=1,
                is_required=True,
            )
        )


async def seed_course_content(session: AsyncSession, courses: list[Course]) -> None:
    """创建课程内容（章节、小节、资源）。"""
    print("  创建课程内容...")
    copied_paths = ensure_demo_document_assets()
    print(f"    已同步 {len(copied_paths)} 份演示文档")

    for course in courses:
        chapter_specs = DEMO_COURSE_CONTENT_SPECS.get(course.title)
        if chapter_specs is None:
            raise RuntimeError(f"缺少课程 {course.title} 的演示内容定义")

        for chapter_spec in chapter_specs:
            result = await session.execute(
                select(Chapter).where(
                    Chapter.course_id == course.id,
                    Chapter.title == chapter_spec["title"],
                )
            )
            chapter = result.scalar_one_or_none()
            if chapter is None:
                chapter = Chapter(
                    course_id=course.id,
                    title=str(chapter_spec["title"]),
                    description=str(chapter_spec["description"]),
                    sort_order=int(chapter_spec["sort_order"]),
                    section_count=len(chapter_spec["sections"]),
                    total_duration=0,
                )
                session.add(chapter)
                await session.flush()
            else:
                chapter.section_count = len(chapter_spec["sections"])
                chapter.total_duration = 0

            await _seed_course_sections(
                session,
                course,
                chapter,
                list(chapter_spec["sections"]),
            )

        course.total_sections = sum(len(chapter_spec["sections"]) for chapter_spec in chapter_specs)
        course.total_duration = 0

    await session.flush()
    print("    课程内容准备完成")


async def seed_announcements(session: AsyncSession) -> None:
    """创建演示公告。"""
    print("  创建演示公告...")

    seeds = [
        {
            "title": "欢迎使用在线学习平台",
            "content": "这是一个全新的在线学习平台，提供丰富的课程资源。",
            "type": "notice",
            "is_top": True,
            "is_published": True,
            "publish_at": datetime.now(timezone.utc),
        },
        {
            "title": "平台功能升级通知",
            "content": "我们新增了学习进度跟踪功能，帮助您更好地管理学习。",
            "type": "update",
            "is_top": False,
            "is_published": True,
            "publish_at": datetime.now(timezone.utc) - timedelta(days=7),
        },
    ]

    created_count = 0
    for item in seeds:
        announcement = await _get_announcement_by_title(session, item["title"])
        if announcement is not None:
            continue
        session.add(Announcement(**item))
        created_count += 1

    await session.flush()
    print(f"    新增 {created_count} 条公告")


async def seed_demo_data(session: AsyncSession) -> None:
    """初始化本地演示数据。"""
    users = await seed_users(session)
    categories = await seed_categories(session)
    tags = await seed_tags(session)
    courses = await seed_courses(session, users, categories, tags)
    await seed_course_content(session, courses)
    await seed_announcements(session)


async def seed_database(include_demo: bool = True) -> None:
    """兼容脚本入口：导入基础数据与演示数据。"""
    print("=" * 50)
    print("SQLite 种子数据脚本")
    print("=" * 50)
    print()

    try:
        async with AsyncSessionLocal() as session:
            print("开始导入基础数据...")
            await seed_base_data(session)

            if include_demo:
                print("开始导入演示数据...")
                await seed_demo_data(session)

            await session.commit()

        print()
        print("=" * 50)
        print("种子数据导入完成")
        if include_demo:
            print("测试账号:")
            print("  管理员: admin1 / Admin123456")
            print("  教师:   teacher1 / Test123456")
            print("  学生:   student1 / Test123456")
        print("=" * 50)
    except Exception as e:
        print(f"导入失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_database())
