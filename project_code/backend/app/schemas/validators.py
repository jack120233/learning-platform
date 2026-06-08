"""共享的 Schema 校验工具。"""

import re
from typing import Annotated

from pydantic import AfterValidator

_MAX_EMAIL_LENGTH = 254
_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_email_address(value: str) -> str:
    """校验邮箱格式，避免依赖 pydantic 的可选 email-validator 包。"""

    normalized = value.strip()
    if not normalized:
        raise ValueError("请输入邮箱地址")

    if len(normalized) > _MAX_EMAIL_LENGTH or not _EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("邮箱格式不正确")

    return normalized


EmailAddress = Annotated[str, AfterValidator(validate_email_address)]
