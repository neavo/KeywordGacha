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
        level = "DEBUG",
        format = "[{time:YYYY-MM-DD HH:mm:ss}] [{level}] {message}",
        enqueue = True,
        encoding = "utf-8",
        rotation = "2 MB",
        retention = 3
    )

    # 全局控制台实例
    console_highlight = Console(highlight = True, tab_size = 4)
    console_no_highlight = Console(highlight = False, tab_size = 4)

    @staticmethod
    def rule(*args, **kwargs):
        LogHelper.console_no_highlight.rule(*args, **kwargs)
        
    @staticmethod
    def json(json, *args, **kwargs):
        LogHelper.console_no_highlight.print_json(str(json), *args, **kwargs)

    @staticmethod
    def print(*args, **kwargs):
        if "highlight" in kwargs and kwargs["highlight"] == True:
            LogHelper.console_highlight.print(*args, **kwargs)
        else:
            LogHelper.console_no_highlight.print(*args, **kwargs)

    @staticmethod
    def status(status, *args, **kwargs):
        return LogHelper.console_no_highlight.status(status, *args, **kwargs)

    @staticmethod
    def is_debug():
        return os.path.exists("debug.txt")

    @staticmethod
    def get_trackback(e):
        return f"{e}\n{("".join(traceback.format_exception(None, e, e.__traceback__))).strip()}"

    @staticmethod
    def debug(message, *args, **kwargs):
        LoguruLogger.debug(str(message), *args, **kwargs)
        LogHelper.logger.debug(str(message), *args, **kwargs)

    @staticmethod
    def info(message, *args, **kwargs):
        LoguruLogger.info(str(message), *args, **kwargs)
        LogHelper.logger.info(str(message), *args, **kwargs)

    @staticmethod
    def warning(message, *args, **kwargs):
        LoguruLogger.warning(str(message), *args, **kwargs)
        LogHelper.logger.warning(str(message), *args, **kwargs)

    @staticmethod
    def error(message, *args, **kwargs):
        LoguruLogger.error(str(message), *args, **kwargs)
        LogHelper.logger.error(str(message), *args, **kwargs)

    @staticmethod
    def critical(message, *args, **kwargs):
        LoguruLogger.critical(str(message), *args, **kwargs)
        LogHelper.logger.critical(str(message), *args, **kwargs)