"""管理员申请数据模型

定义管理员申请相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AdminApplication(BaseModel):
    """管理员申请记录模型

    存储用户申请成为管理员的审核记录。

    Attributes:
        user_id: 申请人ID
        reason: 申请理由
        department: 所属部门
        status: 审核状态（pending/approved/rejected）
        reviewer_id: 审核人ID
        review_comment: 审核意见
        reviewed_at: 审核时间
    """

    __tablename__ = "admin_applications"

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="申请人ID",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="申请理由",
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="所属部门",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="审核状态",
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="审核人ID",
    )
    review_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="审核意见",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )

    def __repr__(self) -> str:
        return f"<AdminApplication(id={self.id}, user_id={self.user_id}, status={self.status})>"