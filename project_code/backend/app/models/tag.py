"""标签数据模型

定义标签相关的数据库模型。
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Tag(BaseModel):
    """标签模型

    用于课程标签管理。

    Attributes:
        name: 标签名称
        slug: URL友好标识
        color: 标签颜色
        use_count: 使用次数
    """

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
        comment="标签名称",
    )
    slug: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
        comment="URL友好标识",
    )
    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="标签颜色",
    )
    use_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="使用次数",
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"