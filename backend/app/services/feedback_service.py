"""反馈消息服务模块。

提供反馈、消息管理的业务逻辑。
"""

import json
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.course import Course
from app.models.feedback import Feedback
from app.models.message import Message
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackProcess
from app.schemas.message import MessageSend


class FeedbackService:
    """反馈服务类"""

    @staticmethod
    def normalize_feedback_type(raw_type: str | None, course_id: int | None = None) -> str:
        """统一反馈类型到前端使用的 system/course。"""
        if course_id is not None or raw_type == "course":
            return "course"
        return "system"

    @staticmethod
    def normalize_feedback_status(raw_status: str | None) -> str:
        """统一反馈状态到前端使用的 pending/processed。"""
        if raw_status in {"processed", "resolved", "closed"}:
            return "processed"
        return "pending"

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        data: FeedbackCreate,
    ) -> Feedback:
        """提交反馈

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 反馈数据

        Returns:
            创建的反馈
        """
        feedback = Feedback(
            user_id=user_id,
            type=data.feedback_type,
            course_id=data.course_id,
            title=data.title,
            content=data.content,
            contact=data.contact,
            images=json.dumps(data.images) if data.images else None,
        )
        db.add(feedback)
        await db.flush()
        return feedback

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int | None = None,
        feedback_type: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        """获取反馈列表

        Args:
            db: 数据库会话
            user_id: 用户ID（用户查看自己的反馈）
            feedback_type: 反馈类型筛选
            status: 状态筛选（管理员查看）
            keyword: 关键字搜索（管理员查看）
            page: 页码
            page_size: 每页数量

        Returns:
            反馈列表和总数
        """
        base_query = (
            select(
                Feedback,
                User.username.label("username"),
                User.email.label("user_email"),
                User.phone.label("user_phone"),
                Course.title.label("course_title"),
            )
            .join(User, User.id == Feedback.user_id)
            .outerjoin(Course, Course.id == Feedback.course_id)
        )

        conditions = []

        if user_id:
            conditions.append(Feedback.user_id == user_id)

        if feedback_type == "course":
            conditions.append(or_(Feedback.course_id.is_not(None), Feedback.type == "course"))
        elif feedback_type == "system":
            conditions.append(and_(Feedback.course_id.is_(None), Feedback.type != "course"))

        if status == "processed":
            conditions.append(Feedback.status.in_(["processed", "resolved", "closed"]))
        elif status == "pending":
            conditions.append(Feedback.status.in_(["pending", "processing"]))
        elif status:
            conditions.append(Feedback.status == status)

        if keyword:
            pattern = f"%{keyword.strip()}%"
            conditions.append(
                or_(
                    Feedback.content.ilike(pattern),
                    Feedback.title.ilike(pattern),
                    User.username.ilike(pattern),
                    Course.title.ilike(pattern),
                )
            )

        if conditions:
            base_query = base_query.where(*conditions)

        # 获取总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = (
            base_query
            .order_by(Feedback.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        feedbacks = [
            self.serialize_feedback_row(feedback, username, user_email, user_phone, course_title)
            for feedback, username, user_email, user_phone, course_title in result.all()
        ]

        return feedbacks, total

    async def get_by_id(
        self,
        db: AsyncSession,
        feedback_id: int,
    ) -> dict | None:
        """通过ID获取反馈详情。"""
        query = (
            select(
                Feedback,
                User.username.label("username"),
                User.email.label("user_email"),
                User.phone.label("user_phone"),
                Course.title.label("course_title"),
            )
            .join(User, User.id == Feedback.user_id)
            .outerjoin(Course, Course.id == Feedback.course_id)
            .where(Feedback.id == feedback_id)
        )
        result = await db.execute(query)
        row = result.first()
        if row is None:
            return None

        feedback, username, user_email, user_phone, course_title = row
        return self.serialize_feedback_row(
            feedback,
            username,
            user_email,
            user_phone,
            course_title,
        )

    async def process(
        self,
        db: AsyncSession,
        feedback_id: int,
        data: FeedbackProcess | None,
        reviewer_id: int,
    ) -> Feedback:
        """处理反馈

        Args:
            db: 数据库会话
            feedback_id: 反馈ID
            data: 处理数据
            reviewer_id: 处理人ID

        Returns:
            更新后的反馈

        Raises:
            NotFoundException: 反馈不存在
        """
        feedback = await db.get(Feedback, feedback_id)
        if not feedback:
            raise NotFoundException("反馈不存在")

        feedback.status = "processed"
        if data is not None:
            feedback.reply = data.reply
        feedback.replied_at = datetime.now(timezone.utc)
        feedback.replied_by = reviewer_id

        await db.flush()
        return feedback

    def serialize_feedback_row(
        self,
        feedback: Feedback,
        username: str | None = None,
        user_email: str | None = None,
        user_phone: str | None = None,
        course_title: str | None = None,
    ) -> dict:
        """将反馈模型与关联信息序列化为前端需要的结构。"""
        feedback_type = self.normalize_feedback_type(feedback.type, feedback.course_id)
        normalized_status = self.normalize_feedback_status(feedback.status)
        images = json.loads(feedback.images) if feedback.images else []

        return {
            "feedback_id": feedback.id,
            "id": feedback.id,
            "user_id": feedback.user_id,
            "username": username,
            "user_email": user_email,
            "user_phone": user_phone,
            "feedback_type": feedback_type,
            "type": feedback_type,
            "course_id": feedback.course_id,
            "course_title": course_title,
            "title": feedback.title,
            "content": feedback.content,
            "contact": feedback.contact,
            "images": images,
            "status": normalized_status,
            "reply": feedback.reply,
            "replied_at": feedback.replied_at,
            "processed_at": feedback.replied_at,
            "created_at": feedback.created_at,
        }


class MessageService:
    """消息服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int,
        type: str | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Message], int]:
        """获取消息列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            type: 类型筛选
            is_read: 已读状态筛选
            page: 页码
            page_size: 每页数量

        Returns:
            消息列表和总数
        """
        query = select(Message).where(Message.user_id == user_id)

        if type:
            query = query.where(Message.type == type)
        if is_read is not None:
            query = query.where(Message.is_read == is_read)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(Message.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        messages = list(result.scalars().all())

        return messages, total

    async def get_by_id(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
    ) -> Message | None:
        """通过ID获取消息"""
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.id == message_id,
                    Message.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def mark_read(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
    ) -> Message:
        """标记消息已读

        Args:
            db: 数据库会话
            message_id: 消息ID
            user_id: 用户ID

        Returns:
            更新后的消息

        Raises:
            NotFoundException: 消息不存在
        """
        message = await self.get_by_id(db, message_id, user_id)
        if not message:
            raise NotFoundException("消息不存在")

        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.now(timezone.utc)

        await db.flush()
        return message

    async def mark_all_read(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> int:
        """标记所有消息已读

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            更新的消息数量
        """
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.user_id == user_id,
                    Message.is_read == False,
                )
            )
        )
        messages = result.scalars().all()

        now = datetime.now(timezone.utc)
        for message in messages:
            message.is_read = True
            message.read_at = now

        return len(messages)

    async def delete(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
    ) -> None:
        """删除消息

        Args:
            db: 数据库会话
            message_id: 消息ID
            user_id: 用户ID

        Raises:
            NotFoundException: 消息不存在
        """
        message = await self.get_by_id(db, message_id, user_id)
        if not message:
            raise NotFoundException("消息不存在")

        await db.delete(message)

    async def get_unread_count(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        """获取未读消息数量

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            各类型未读数量
        """
        # 总未读数
        result = await db.execute(
            select(func.count()).where(
                and_(
                    Message.user_id == user_id,
                    Message.is_read == False,
                )
            )
        )
        total = result.scalar() or 0

        # 各类型未读数
        type_counts = {}
        for msg_type in ["system", "course", "interaction"]:
            result = await db.execute(
                select(func.count()).where(
                    and_(
                        Message.user_id == user_id,
                        Message.type == msg_type,
                        Message.is_read == False,
                    )
                )
            )
            type_counts[msg_type] = result.scalar() or 0

        return {
            "total": total,
            "system": type_counts.get("system", 0),
            "course": type_counts.get("course", 0),
            "interaction": type_counts.get("interaction", 0),
        }

    async def send(
        self,
        db: AsyncSession,
        data: MessageSend,
        sender_id: int | None = None,
    ) -> Message:
        """发送消息

        Args:
            db: 数据库会话
            data: 消息数据
            sender_id: 发送者ID

        Returns:
            创建的消息
        """
        message = Message(
            user_id=data.user_id,
            type=data.type,
            title=data.title,
            content=data.content,
            link=data.link,
            sender_id=sender_id,
        )
        db.add(message)
        await db.flush()
        return message


# 创建全局服务实例
feedback_service = FeedbackService()
message_service = MessageService()
