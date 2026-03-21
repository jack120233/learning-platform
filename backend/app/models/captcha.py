"""验证码数据模型

定义图形验证码相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CaptchaRecord(BaseModel):
    """图形验证码记录模型

    存储图形验证码的生成记录，用于验证。

    Attributes:
        captcha_key: 验证码唯一标识
        captcha_text: 验证码文本内容
        image_base64: Base64 编码的图片数据
        expires_at: 过期时间
    """

    __tablename__ = "captcha_records"

    captcha_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="验证码唯一标识",
    )
    captcha_text: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="验证码文本内容",
    )
    image_base64: Mapped[str] = mapped_column(
        String(50000),
        nullable=False,
        comment="Base64 编码的图片数据",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="过期时间",
    )

    def __repr__(self) -> str:
        return f"<CaptchaRecord(id={self.id}, key={self.captcha_key})>"

    @property
    def is_expired(self) -> bool:
        """检查验证码是否过期"""
        return datetime.utcnow() > self.expires_at