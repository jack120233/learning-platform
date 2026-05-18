"""老师审核数据模型

定义老师审核相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TeacherAudit(BaseModel):
    """老师审核记录模型

    存储用户申请成为老师的审核记录。

    Attributes:
        user_id: 申请人ID
        real_name: 真实姓名
        id_card: 身份证号（脱敏存储）
        phone: 联系电话
        email: 联系邮箱
        organization: 所属机构
        title: 职称/头衔
        introduction: 个人简介
        certificate_urls: 证书/资质图片URLs（JSON数组）
        status: 审核状态（pending/approved/rejected）
        reviewer_id: 审核人ID
        review_comment: 审核意见
        reviewed_at: 审核时间
    """

    __tablename__ = "teacher_audits"

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="申请人ID",
    )
    real_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="真实姓名",
    )
    id_card: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="身份证号（加密存储）",
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="联系电话",
    )
    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="联系邮箱",
    )
    organization: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="所属机构",
    )
    title: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="职称/头衔",
    )
    introduction: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="个人简介",
    )
    certificate_urls: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="证书/资质图片URLs（JSON数组）",
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
        return f"<TeacherAudit(id={self.id}, user_id={self.user_id}, status={self.status})>"