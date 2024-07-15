import os
import re
import logging
import traceback

from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.logging import RichHandler

class LogHelper:
    # 创建一个logger
    logger = logging.getLogger("KeywordGacha")
    logger.setLevel(logging.DEBUG if os.path.exists("debug.txt") else logging.INFO)

    # 创建一个handler
    file_handler = RotatingFileHandler(
        filename = "KeywordGacha.log",
        encoding = "utf-8",
        maxBytes = 2 * 1024 * 1024, 
        backupCount = 1
    )

    # 定义输出格式
    file_handler_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )

    # 设置输出格式
    file_handler.setFormatter(file_handler_formatter)

    # 给logger添加handler
    logger.addHandler(file_handler)
    logger.addHandler(RichHandler(
        markup = True,
        show_path = False,
        rich_tracebacks = True,
        log_time_format = "[%X]",
        omit_repeated_times = False
    ))

    # 注册全局控制台实例
    console = Console(highlight = False)

    @staticmethod
    def print(*args):
        return LogHelper.console.print(*args)

    @staticmethod
    def is_debug():
        return os.path.exists("debug.txt")

    @staticmethod
    def get_trackback(e):
        return f"\n{("".join(traceback.format_exception(None, e, e.__traceback__))).strip()}"

    @staticmethod
    def debug(message):
        return LogHelper.logger.debug(message)

    @staticmethod
    def info(message):
        return LogHelper.logger.info(message)

    @staticmethod
    def warning(message):
        return LogHelper.logger.warning(message)

    @staticmethod
    def error(message):
        return LogHelper.logger.error(message)

    @staticmethod
    def critical(message):
        return LogHelper.logger.critical(message)