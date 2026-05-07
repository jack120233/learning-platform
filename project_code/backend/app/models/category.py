"""分类数据模型

定义分类相关的数据库模型。
"""

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Category(BaseModel):
    """分类模型

    用于课程分类管理。

    Attributes:
        name: 分类名称
        slug: URL友好标识
        description: 分类描述
        icon: 分类图标
        sort_order: 排序序号
        parent_id: 父分类ID（用于多级分类）
        is_active: 是否启用
    """

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="分类名称",
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="URL友好标识",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="分类描述",
    )
    icon: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="分类图标URL",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序序号",
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="父分类ID",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="是否启用",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"