"""健康检查模块测试

测试服务的健康状态检查接口。
"""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_success_response


class TestHealthCheck:
    """健康检查测试类"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """测试健康检查接口

        验证：
        - 返回状态码 200
        - 业务码为 200
        - 返回正确的消息
        """
        response = await client.get("/api/v1/health")
        data = assert_success_response(response, "服务运行正常")
        assert data["data"] is None

    @pytest.mark.asyncio
    async def test_ping(self, client: AsyncClient):
        """测试 Ping 接口

        验证：
        - 返回状态码 200
        - 业务码为 200
        - 返回 pong 消息
        """
        response = await client.get("/api/v1/ping")
        data = assert_success_response(response, "pong")
        assert data["data"] is None

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """测试根路径接口

        验证：
        - 返回状态码 200
        - 包含应用名称和版本信息
        """
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "name" in data["data"]
        assert "version" in data["data"]
        assert "environment" in data["data"]