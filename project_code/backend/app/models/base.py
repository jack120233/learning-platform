"""数据库基础模型模块

定义所有数据库模型的公共基类和混入类。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """声明式基类

    所有数据库模型应继承此类。
    """

    # 通用类型注解映射
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }

    def to_dict(self) -> dict[str, Any]:
        """将模型实例转换为字典

        Returns:
            包含所有属性的字典
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """从字典更新模型属性

        Args:
            data: 包含属性值的字典
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class TimestampMixin:
    """时间戳混入类

    为模型添加创建时间和更新时间字段。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class SoftDeleteMixin:
    """软删除混入类

    为模型添加软删除支持。
    """

    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否删除",
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间",
    )

    def soft_delete(self) -> None:
        """执行软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """恢复软删除"""
        self.is_deleted = False
        self.deleted_at = None


class IDMixin:
    """ID 混入类

    为模型添加自增主键。
    """

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
    )


class BaseModel(Base, IDMixin, TimestampMixin):
    """完整基础模型

    包含 ID、创建时间和更新时间。
    大多数模型可以继承此类。
    """

    __abstract__ = True
    # 在 flush 阶段主动取回 server_default/onupdate 生成的值，
    # 避免异步 ORM 对 created_at 等字段进行后续懒加载。
    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
