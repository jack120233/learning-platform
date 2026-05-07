"""消息服务模块

提供消息管理的业务逻辑。
"""

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.message import Message
from app.schemas.message import MessageSend


class MessageService:
    """消息服务类"""

    NOTIFICATION_TYPES = ("notification", "system", "course", "interaction")

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int,
        type: str | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Message], int]:
        """获取消息列表"""
        query = select(Message).where(Message.user_id == user_id)

        if type and type != "all":
            query = query.where(self._build_type_filter(type))
        if is_read is not None:
            query = query.where(Message.is_read == is_read)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

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
        """标记消息已读"""
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
        """标记所有消息已读"""
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
        """删除消息"""
        message = await self.get_by_id(db, message_id, user_id)
        if not message:
            raise NotFoundException("消息不存在")

        await db.delete(message)

    async def get_unread_count(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        """获取未读消息数量"""
        total = await self._count_unread(db, user_id)
        announcement = await self._count_unread(db, user_id, ["announcement"])
        notification = await self._count_unread(db, user_id, self.NOTIFICATION_TYPES)
        system = await self._count_unread(db, user_id, ["system"])
        course = await self._count_unread(db, user_id, ["course"])
        interaction = await self._count_unread(db, user_id, ["interaction"])

        return {
            "total": total,
            "announcement": announcement,
            "notification": notification,
            "system": system,
            "course": course,
            "interaction": interaction,
        }

    async def send(
        self,
        db: AsyncSession,
        data: MessageSend,
        sender_id: int | None = None,
    ) -> Message:
        """发送消息"""
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

    def _build_type_filter(self, message_type: str):
        """构造消息类型筛选条件。"""
        if message_type == "announcement":
            return Message.type == "announcement"
        if message_type == "notification":
            return or_(*(Message.type == item for item in self.NOTIFICATION_TYPES))
        return Message.type == message_type

    async def _count_unread(
        self,
        db: AsyncSession,
        user_id: int,
        message_types: Iterable[str] | None = None,
    ) -> int:
        """统计未读消息数量。"""
        query = select(func.count()).where(
            and_(
                Message.user_id == user_id,
                Message.is_read == False,
            )
        )
        if message_types:
            query = query.where(or_(*(Message.type == item for item in message_types)))
        result = await db.execute(query)
        return result.scalar() or 0


# 创建全局服务实例
message_service = MessageService()
