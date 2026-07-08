"""应用配置管理模块

使用 pydantic-settings 管理环境变量配置，支持 .env 文件加载。
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
REPOSITORY_ROOT = PROJECT_ROOT.parent
FRONTEND_ROOT = REPOSITORY_ROOT / "UI"
FRONTEND_DIST_DIR = FRONTEND_ROOT / "dist"
FRONTEND_INDEX_PATH = FRONTEND_DIST_DIR / "index.html"
WINDOWS_EDITIONS = {"windows_local", "windows_classroom"}
DEFAULT_DEVELOPMENT_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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
    app_edition: Literal["development", "windows_local", "windows_classroom", "server"] = "development"

    # API 配置
    api_v1_prefix: str = "/api/v1"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 本地运行数据目录配置（Windows 单机/机房版默认使用）
    local_data_dir: str = str(BASE_DIR / "data")
    local_database_path: str | None = None
    local_cache_dir: str | None = None

    # 启动器与前端产物配置
    frontend_dist_dir: str = str(FRONTEND_DIST_DIR)
    frontend_index_path: str = str(FRONTEND_INDEX_PATH)
    startup_log_dir: str = str(BASE_DIR / "logs")

    # Windows local 默认把单机数据放在 backend/data 下
    windows_local_data_dir: str = str(BASE_DIR / "data")
    windows_local_log_dir: str = str(BASE_DIR / "logs")
    windows_local_upload_dir: str = str(BASE_DIR / "uploads")
    windows_local_cache_dir: str = str(BASE_DIR / "data" / "cache")
    windows_local_database_filename: str = "windows-local.db"

    # 数据库配置
    database_url: str | None = Field(
        default=None,
        description="异步数据库连接字符串；Windows 版本未显式配置时自动回落到本地 SQLite 文件",
    )
    database_echo: bool = False
    database_log_parameters: bool = False
    sqlite_timeout_seconds: float = 30.0
    sqlite_busy_timeout_ms: int = 30_000

    # 缓存配置
    cache_backend: Literal["auto", "memory", "diskcache"] = "auto"
    cache_default_ttl_seconds: int | None = 300
    cache_size_limit_bytes: int = 256 * 1024 * 1024
    cache_max_item_size_bytes: int = 1024 * 1024
    cache_key_prefix: str = "learning-platform"

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
    avatar_subdir: str = "avatars"
    feedback_image_subdir: str = "feedback-images"
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

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str | None) -> str | None:
        """兼容未配置或空字符串数据库连接。"""
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers")
    @classmethod
    def parse_list_from_string(cls, v: str | list[str]) -> list[str]:
        """将逗号分隔的字符串转换为列表"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def is_windows_edition(self) -> bool:
        """是否为 Windows 单机/机房运行版本。"""
        return self.app_edition in WINDOWS_EDITIONS

    @property
    def resolved_local_database_path(self) -> Path:
        """Windows 版本默认 SQLite 文件路径。"""
        if self.local_database_path:
            return Path(self.local_database_path)
        if self.app_edition == "windows_local":
            return Path(self.windows_local_data_dir) / self.windows_local_database_filename
        return Path(self.local_data_dir) / "learning_platform.db"

    @property
    def resolved_cache_dir(self) -> Path:
        """本地磁盘缓存目录。"""
        if self.local_cache_dir:
            return Path(self.local_cache_dir)
        if self.app_edition == "windows_local":
            return Path(self.windows_local_cache_dir)
        return Path(self.local_data_dir) / "cache"

    @property
    def windows_sqlite_database_url(self) -> str:
        """Windows 版本本地 SQLite 数据库连接字符串。"""
        database_path = self.resolved_local_database_path
        return f"sqlite+aiosqlite:///{database_path.as_posix()}"

    @property
    def resolved_upload_dir(self) -> Path:
        """解析后的上传目录。"""
        if self.app_edition == "windows_local" and self.upload_dir == str(BASE_DIR / "uploads"):
            return Path(self.windows_local_upload_dir)
        return Path(self.upload_dir)

    @property
    def resolved_log_dir(self) -> Path:
        """解析后的日志目录。"""
        if self.app_edition == "windows_local" and self.log_dir == "logs":
            return Path(self.windows_local_log_dir)
        return Path(self.log_dir)

    @property
    def parsed_frontend_dist_dir(self) -> Path:
        """解析后的前端生产包目录。"""
        return Path(self.frontend_dist_dir)

    @property
    def parsed_frontend_index_path(self) -> Path:
        """解析后的前端首页文件。"""
        return Path(self.frontend_index_path)

    @property
    def parsed_cors_origins(self) -> list[str]:
        """获取解析后的 CORS origins 列表"""
        if isinstance(self.cors_origins, str):
            return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        return self.cors_origins

    @property
    def async_database_url(self) -> str:
        """获取异步数据库连接字符串。"""
        if self.database_url:
            return self.database_url
        if self.is_windows_edition:
            return self.windows_sqlite_database_url
        return DEFAULT_DEVELOPMENT_DATABASE_URL

    @property
    def effective_cache_backend(self) -> Literal["memory", "diskcache"]:
        """获取按运行版本解析后的缓存后端。"""
        if self.cache_backend != "auto":
            return self.cache_backend
        if self.is_windows_edition:
            return "diskcache"
        return "memory"

    @property
    def is_sqlite_database(self) -> bool:
        """当前数据库是否为 SQLite。"""
        try:
            return make_url(self.async_database_url).drivername.startswith("sqlite")
        except Exception:
            return False

    @property
    def is_sqlite_memory_database(self) -> bool:
        """当前数据库是否为内存 SQLite。"""
        if not self.is_sqlite_database:
            return False
        url = make_url(self.async_database_url)
        database = url.database or ""
        return database in {"", ":memory:"} or url.query.get("mode") == "memory"

    @property
    def is_sqlite_file_database(self) -> bool:
        """当前数据库是否为 SQLite 文件数据库。"""
        return self.is_sqlite_database and not self.is_sqlite_memory_database

    @property
    def sqlalchemy_connect_args(self) -> dict[str, float]:
        """SQLAlchemy 连接参数。"""
        if not self.is_sqlite_file_database:
            return {}
        return {"timeout": self.sqlite_timeout_seconds}

    @property
    def runtime_directories(self) -> list[Path]:
        """需要在本地运行时确保存在的目录。"""
        directories = [self.resolved_upload_dir, self.resolved_log_dir]
        if self.app_edition == "windows_local":
            directories.extend(
                [
                    Path(self.windows_local_data_dir),
                    self.resolved_local_database_path.parent,
                    self.resolved_cache_dir,
                ]
            )
        return list(dict.fromkeys(directories))

    @property
    def windows_local_frontend_ready(self) -> bool:
        """Windows 单机版是否已包含可直接承载的前端生产包。"""
        return self.parsed_frontend_index_path.is_file()


@lru_cache
def get_settings() -> Settings:
    """获取配置单例

    使用 lru_cache 缓存配置实例，避免重复加载。
    """
    return Settings()


# 全局配置实例
settings = get_settings()
