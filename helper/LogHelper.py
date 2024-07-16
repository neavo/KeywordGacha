import os
import logging
import traceback

from loguru import logger as LoguruLogger
from rich.console import Console
from rich.logging import RichHandler

class LogHelper:
    # 控制台日志实例
    logger = logging.getLogger("KeywordGacha")
    logger.setLevel(logging.DEBUG if os.path.exists("debug.txt") else logging.INFO)
    logger.addHandler(RichHandler(
        markup = True,
        show_path = False,
        rich_tracebacks = True,
        log_time_format = "[%X]",
        omit_repeated_times = False
    ))

    # 全局文件日志实例
    LoguruLogger.remove(0)
    LoguruLogger.add(
        "KeywordGacha.log",
        delay = True,
        level = "DEBUG" if os.path.exists("debug.txt") else "INFO",
        format = "[{time:YYYY-MM-DD HH:mm:ss}] [{level}] {message}",
        enqueue = True,
        encoding = "utf-8",
        rotation = "1 MB",
        retention = 3
    )

    # 全局控制台实例
    console = Console(highlight = False)

    @staticmethod
    def print(*args):
        LogHelper.console.print(*args)

    @staticmethod
    def is_debug():
        return os.path.exists("debug.txt")

    @staticmethod
    def get_trackback(e):
        f"\n{("".join(traceback.format_exception(None, e, e.__traceback__))).strip()}"

    @staticmethod
    def debug(message):
        LoguruLogger.debug(message)
        LogHelper.logger.debug(message)

    @staticmethod
    def info(message):
        LoguruLogger.info(message)
        LogHelper.logger.info(message)

    @staticmethod
    def warning(message):
        LoguruLogger.warning(message)
        LogHelper.logger.warning(message)

    @staticmethod
    def error(message):
        LoguruLogger.error(message)
        LogHelper.logger.error(message)

    @staticmethod
    def critical(message):
        LoguruLogger.critical(message)
        LogHelper.logger.critical(message)