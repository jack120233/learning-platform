"""应用配置管理模块

使用 pydantic-settings 管理环境变量配置，支持 .env 文件加载。
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置类

    所有配置项通过环境变量或 .env 文件加载。
    环境变量名称不区分大小写。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础配置
    app_name: str = "在线学习平台"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "testing", "production"] = "development"

    # API 配置
    api_v1_prefix: str = "/api/v1"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 数据库配置
    database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:",
        description="异步数据库连接字符串",
    )
    database_echo: bool = False
    database_log_parameters: bool = False

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None

    # JWT 配置
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="JWT 签名密钥，生产环境必须修改",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 小时
    refresh_token_expire_days: int = 7  # 7 天
    remember_me_expire_days: int = 30  # 记住我 30 天

    # 密码加密配置
    bcrypt_rounds: int = 12

    # 验证码配置
    captcha_expire_minutes: int = 5  # 图形验证码 5 分钟
    email_code_expire_minutes: int = 10  # 邮箱验证码 10 分钟

    # 登录安全配置
    login_max_attempts: int = 5  # 最大尝试次数
    login_lockout_minutes: int = 30  # 锁定时长

    # CORS 配置
    cors_origins: str | list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: str | list[str] = ["*"]
    cors_allow_headers: str | list[str] = ["*"]

    # 日志配置
    log_level: str = "DEBUG"
    log_dir: str = "logs"
    log_to_console: bool = True
    log_to_file: bool = True
    log_file_prefix: str = "app"
    log_backup_count: int = 30

    # 文件上传配置
    upload_dir: str = str(BASE_DIR / "uploads")
    upload_url_prefix: str = "/uploads"
    course_cover_subdir: str = "course-covers"
    general_upload_subdir: str = "files"
    chunk_upload_tmp_subdir: str = ".chunk-sessions"
    course_cover_max_size: int = 10 * 1024 * 1024
    general_file_max_size: int = 100 * 1024 * 1024
    chunk_file_max_size: int = 500 * 1024 * 1024

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, v: bool | str) -> bool:
        """兼容常见的环境标记写法。"""
        if isinstance(v, bool):
            return v

        if isinstance(v, str):
            normalized = v.strip().lower()
            truthy = {"1", "true", "yes", "on", "debug", "development", "dev"}
            falsy = {"0", "false", "no", "off", "release", "production", "prod"}

            if normalized in truthy:
                return True
            if normalized in falsy:
                return False

        return bool(v)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """验证数据库连接字符串格式"""
        if not v:
            raise ValueError("数据库连接字符串不能为空")
        return v

    @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers")
    @classmethod
    def parse_list_from_string(cls, v: str | list[str]) -> list[str]:
        """将逗号分隔的字符串转换为列表"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def parsed_cors_origins(self) -> list[str]:
        """获取解析后的 CORS origins 列表"""
        if isinstance(self.cors_origins, str):
            return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        return self.cors_origins

    @property
    def async_database_url(self) -> str:
        """获取异步数据库连接字符串"""
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """获取配置单例

    使用 lru_cache 缓存配置实例，避免重复加载。
    """
    return Settings()


# 全局配置实例
settings = get_settings()
