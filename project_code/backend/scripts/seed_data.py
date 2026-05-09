"""数据库种子数据脚本

用于初始化测试数据。

用法:
    cd backend
    python scripts/seed_data.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.dependencies import AsyncSessionLocal
from app.core.security import hash_password
from app.models import (
    User,
    Category,
    Tag,
    Course,
    Chapter,
    Section,
    Resource,
    Announcement,
)


async def seed_users(session) -> list[User]:
    """创建测试用户（与 test-plan.md 一致）"""
    print("  创建测试用户...")

    users = [
        # 管理员
        User(
            username="admin1",
            email="admin1@example.com",
            password_hash=hash_password("Admin123456"),
            nickname="管理员",
            role="admin",
            status="active",
        ),
        # 教师
        User(
            username="teacher1",
            email="teacher1@example.com",
            password_hash=hash_password("Test123456"),
            nickname="张老师",
            role="teacher",
            status="active",
        ),
        User(
            username="teacher2",
            email="teacher2@example.com",
            password_hash=hash_password("Test123456"),
            nickname="李老师",
            role="teacher",
            status="active",
        ),
        User(
            username="teacher3",
            email="teacher3@example.com",
            password_hash=hash_password("Test123456"),
            nickname="王老师",
            role="teacher",
            status="active",
        ),
        User(
            username="teacher4",
            email="teacher4@example.com",
            password_hash=hash_password("Test123456"),
            nickname="赵老师",
            role="teacher",
            status="active",
        ),
        User(
            username="teacher5",
            email="teacher5@example.com",
            password_hash=hash_password("Test123456"),
            nickname="陈老师",
            role="teacher",
            status="active",
        ),
        User(
            username="teacher6",
            email="teacher6@example.com",
            password_hash=hash_password("Test123456"),
            nickname="刘老师",
            role="teacher",
            status="active",
        ),
        # 学生
        User(
            username="student1",
            email="student1@example.com",
            password_hash=hash_password("Test123456"),
            nickname="学生1",
            role="student",
            status="active",
        ),
        User(
            username="student2",
            email="student2@example.com",
            password_hash=hash_password("Test123456"),
            nickname="学生2",
            role="student",
            status="active",
        ),
    ]

    session.add_all(users)
    await session.flush()
    print(f"    ✅ 创建 {len(users)} 个用户")
    return users


async def seed_categories(session) -> list[Category]:
    """创建课程分类"""
    print("  创建课程分类...")

    categories = [
        Category(name="编程开发", slug="programming", description="软件开发相关课程", sort_order=1),
        Category(name="人工智能", slug="ai", description="AI和机器学习课程", sort_order=2),
        Category(name="数据分析", slug="data-analysis", description="数据分析和可视化课程", sort_order=3),
        Category(name="设计创意", slug="design", description="UI/UX设计课程", sort_order=4),
        Category(name="语言学习", slug="language", description="外语学习课程", sort_order=5),
    ]

    session.add_all(categories)
    await session.flush()
    print(f"    ✅ 创建 {len(categories)} 个分类")
    return categories


async def seed_tags(session) -> list[Tag]:
    """创建课程标签"""
    print("  创建课程标签...")

    tags = [
        Tag(name="Python", slug="python", use_count=0),
        Tag(name="JavaScript", slug="javascript", use_count=0),
        Tag(name="Java", slug="java", use_count=0),
        Tag(name="React", slug="react", use_count=0),
        Tag(name="机器学习", slug="machine-learning", use_count=0),
        Tag(name="深度学习", slug="deep-learning", use_count=0),
        Tag(name="前端开发", slug="frontend", use_count=0),
        Tag(name="后端开发", slug="backend", use_count=0),
        Tag(name="入门", slug="beginner", use_count=0),
        Tag(name="进阶", slug="advanced", use_count=0),
    ]

    session.add_all(tags)
    await session.flush()
    print(f"    ✅ 创建 {len(tags)} 个标签")
    return tags


async def seed_courses(session, users: list[User], categories: list[Category], tags: list[Tag]) -> list[Course]:
    """创建测试课程（与 test-plan.md 一致）"""
    print("  创建测试课程...")

    teacher = users[1]  # teacher1

    courses = [
        Course(
            title="Python入门",
            subtitle="零基础学Python",
            description="适合初学者的Python课程",
            teacher_id=teacher.id,
            category_id=categories[0].id,
            status="published",
            price=99.0,
            level="beginner",
            is_free=False,
        ),
        Course(
            title="FastAPI实战",
            subtitle="现代Python Web开发",
            description="FastAPI框架完整教程",
            teacher_id=teacher.id,
            category_id=categories[0].id,
            status="published",
            price=199.0,
            level="intermediate",
            is_free=False,
        ),
    ]

    session.add_all(courses)
    await session.flush()

    # 关联标签
    courses[0].tags = [tags[0], tags[8]]  # Python, 入门
    courses[1].tags = [tags[0], tags[9]]  # Python, 进阶

    print(f"    ✅ 创建 {len(courses)} 门课程")
    return courses


async def seed_course_content(session, courses: list[Course]) -> None:
    """创建课程内容（章节、小节、资源）"""
    print("  创建课程内容...")

    for course in courses[:2]:  # 只为前两门课程创建内容
        # 创建章节
        chapters = [
            Chapter(
                course_id=course.id,
                title=f"第一章：{course.title}基础",
                description="基础概念和环境搭建",
                sort_order=1,
            ),
            Chapter(
                course_id=course.id,
                title="第二章：核心知识",
                description="核心概念和基本操作",
                sort_order=2,
            ),
        ]

        session.add_all(chapters)
        await session.flush()

        # 为每章创建小节
        for chapter in chapters:
            sections = [
                Section(
                    course_id=course.id,
                    chapter_id=chapter.id,
                    title=f"第{chapter.sort_order}节：理论讲解",
                    description="理论知识讲解",
                    sort_order=1,
                ),
                Section(
                    course_id=course.id,
                    chapter_id=chapter.id,
                    title=f"第{chapter.sort_order}节：实践练习",
                    description="动手实践",
                    sort_order=2,
                ),
            ]

            session.add_all(sections)
            await session.flush()

            # 为每个小节创建资源
            for section in sections:
                resources = [
                    Resource(
                        course_id=course.id,
                        chapter_id=chapter.id,
                        section_id=section.id,
                        title=f"视频教程",
                        type="video",
                        file_url="https://example.com/video.mp4",
                        duration=600,  # 10分钟
                        sort_order=1,
                    ),
                    Resource(
                        course_id=course.id,
                        chapter_id=chapter.id,
                        section_id=section.id,
                        title=f"学习资料",
                        type="document",
                        file_url="https://example.com/doc.pdf",
                        sort_order=2,
                    ),
                ]

                session.add_all(resources)

    await session.flush()
    print("    ✅ 创建课程内容完成")


async def seed_announcements(session) -> None:
    """创建系统公告"""
    print("  创建系统公告...")

    announcements = [
        Announcement(
            title="欢迎使用在线学习平台",
            content="这是一个全新的在线学习平台，提供丰富的课程资源。",
            type="notice",
            is_top=True,
            is_published=True,
            publish_at=datetime.now(timezone.utc),
        ),
        Announcement(
            title="平台功能升级通知",
            content="我们新增了学习进度跟踪功能，帮助您更好地管理学习。",
            type="update",
            is_top=False,
            is_published=True,
            publish_at=datetime.now(timezone.utc) - timedelta(days=7),
        ),
    ]

    session.add_all(announcements)
    await session.flush()
    print(f"    ✅ 创建 {len(announcements)} 条公告")


async def seed_database() -> None:
    """初始化测试数据"""
    print("=" * 50)
    print("数据库种子数据脚本")
    print("=" * 50)
    print()

    try:
        async with AsyncSessionLocal() as session:
            # 检查是否已有数据
            result = await session.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                print("⚠️  数据库已有数据，跳过种子数据导入")
                print("   如需重新导入，请先清空数据库表")
                return

            print("开始导入种子数据...")

            # 按依赖顺序创建数据
            users = await seed_users(session)
            categories = await seed_categories(session)
            tags = await seed_tags(session)
            courses = await seed_courses(session, users, categories, tags)
            await seed_course_content(session, courses)
            await seed_announcements(session)

            # 提交事务
            await session.commit()

        print()
        print("=" * 50)
        print("✅ 种子数据导入完成")
        print()
        print("测试账号（与 test-plan.md 一致）:")
        print("  管理员: admin1 / Admin123456")
        print("  教师:   teacher1 / Test123456")
        print("  学生:   student1 / Test123456")
        print("  学生:   student2 / Test123456")
        print("=" * 50)

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_database())