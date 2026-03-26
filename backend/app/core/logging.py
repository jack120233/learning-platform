"""日志配置模块

提供统一的日志配置和管理功能。
"""

import logging
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import TextIO


# 日志颜色（仅用于控制台）
class LogColor:
    """日志颜色常量"""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器

    为不同级别的日志添加颜色，便于在控制台区分。
    """

    LEVEL_COLORS = {
        logging.DEBUG: LogColor.CYAN,
        logging.INFO: LogColor.GREEN,
        logging.WARNING: LogColor.YELLOW,
        logging.ERROR: LogColor.RED,
        logging.CRITICAL: LogColor.MAGENTA,
    }

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        # 保存原始级别名
        original_levelname = record.levelname

        # 添加颜色
        color = self.LEVEL_COLORS.get(record.levelno, LogColor.WHITE)
        record.levelname = f"{color}{record.levelname}{LogColor.RESET}"

        # 格式化
        result = super().format(record)

        # 恢复原始级别名
        record.levelname = original_levelname

        return result


class RequestFormatter(logging.Formatter):
    """请求日志格式化器

    为请求日志添加额外的上下文信息。
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化请求日志

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        # 添加时间戳
        if not hasattr(record, "timestamp"):
            record.timestamp = datetime.now().isoformat()

        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_file_prefix: str = "app",
    backup_count: int = 30,
    console_stream: TextIO | None = None,
) -> logging.Logger:
    """配置应用日志

    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_dir: 日志文件目录
        log_to_console: 是否输出到控制台
        log_to_file: 是否输出到文件
        log_file_prefix: 日志文件前缀
        backup_count: 保留日志文件数量（天数）
        console_stream: 控制台输出流（用于测试）

    Returns:
        配置好的根日志器
    """
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 日志格式
    console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"

    # 控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(console_stream or sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredFormatter(console_format, datefmt="%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(console_handler)

    # 文件处理器
    if log_to_file:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 主日志文件（按天轮转）
        log_file = log_path / f"{log_file_prefix}.log"
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(file_handler)

        # 错误日志单独文件
        error_log_file = log_path / f"{log_file_prefix}_error.log"
        error_handler = TimedRotatingFileHandler(
            filename=str(error_log_file),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(error_handler)

    # 配置第三方库日志级别（降低噪音）
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器

    Args:
        name: 日志器名称（通常使用 __name__）

    Returns:
        日志器实例
    """
    return logging.getLogger(name)


# 请求日志器
request_logger = logging.getLogger("request")