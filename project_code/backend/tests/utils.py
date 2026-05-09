"""测试工具函数

提供测试中常用的辅助函数。
"""

import random
import string
from typing import Any


def random_string(length: int = 10) -> str:
    """生成随机字符串

    Args:
        length: 字符串长度

    Returns:
        随机字符串
    """
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_email() -> str:
    """生成随机邮箱

    Returns:
        随机邮箱地址
    """
    return f"{random_string(8)}@example.com"


def random_username() -> str:
    """生成随机用户名

    Returns:
        随机用户名
    """
    return f"user_{random_string(8)}"


def assert_response_code(response, expected_code: int = 200):
    """断言响应状态码

    Args:
        response: HTTP 响应
        expected_code: 预期状态码
    """
    assert response.status_code == expected_code, (
        f"预期状态码 {expected_code}，实际为 {response.status_code}，"
        f"响应内容: {response.text}"
    )


def assert_business_code(response, expected_code: int = 200):
    """断言业务状态码

    Args:
        response: HTTP 响应
        expected_code: 预期业务状态码
    """
    data = response.json()
    assert data["code"] == expected_code, (
        f"预期业务码 {expected_code}，实际为 {data['code']}，"
        f"消息: {data.get('message')}"
    )


def get_response_data(response) -> Any:
    """获取响应数据

    Args:
        response: HTTP 响应

    Returns:
        响应数据
    """
    return response.json().get("data")


class AsyncContextManagerMock:
    """异步上下文管理器 Mock

    用于 Mock 异步上下文管理器。
    """

    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass