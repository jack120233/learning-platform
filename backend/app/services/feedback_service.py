"""反馈消息服务模块

提供反馈、消息管理的业务逻辑。
"""

import json
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.feedback import Feedback
from app.models.message import Message
from app.schemas.feedback import FeedbackCreate, FeedbackProcess
from app.schemas.message import MessageSend


class FeedbackService:
    """反馈服务类"""

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
            type=data.type,
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
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Feedback], int]:
        """获取反馈列表

        Args:
            db: 数据库会话
            user_id: 用户ID（用户查看自己的反馈）
            status: 状态筛选（管理员查看）
            page: 页码
            page_size: 每页数量

        Returns:
            反馈列表和总数
        """
        query = select(Feedback)

        if user_id:
            query = query.where(Feedback.user_id == user_id)
        if status:
            query = query.where(Feedback.status == status)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(Feedback.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        feedbacks = list(result.scalars().all())

        return feedbacks, total

    async def get_by_id(
        self,
        db: AsyncSession,
        feedback_id: int,
    ) -> Feedback | None:
        """通过ID获取反馈"""
        return await db.get(Feedback, feedback_id)

    async def process(
        self,
        db: AsyncSession,
        feedback_id: int,
        data: FeedbackProcess,
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
        feedback = await self.get_by_id(db, feedback_id)
        if not feedback:
            raise NotFoundException("反馈不存在")

        feedback.status = "resolved"
        feedback.reply = data.reply
        feedback.replied_at = datetime.now(timezone.utc)
        feedback.replied_by = reviewer_id

        await db.flush()
        return feedback


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