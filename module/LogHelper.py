import os
import logging
import traceback

from rich.status import Status
from rich.console import Console
from rich.logging import RichHandler
from loguru import logger as LoguruLogger

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
        rotation = "4 MB",
        retention = 3
    )

    # 全局控制台实例
    console_highlight = Console(highlight = True, tab_size = 4)
    console_no_highlight = Console(highlight = False, tab_size = 4)

    @staticmethod
    def rule(*args, **kwargs) -> None:
        LogHelper.console_no_highlight.rule(*args, **kwargs)

    @staticmethod
    def input(*args, **kwargs) -> str:
        return LogHelper.console_no_highlight.input(*args, **kwargs)

    @staticmethod
    def print(*args, **kwargs) -> None:
        if kwargs.get("highlight", True) == True:
            LogHelper.console_highlight.print(*args, **kwargs)
        else:
            LogHelper.console_no_highlight.print(*args, **kwargs)

    @staticmethod
    def status(*args, **kwargs) -> Status:
        return LogHelper.console_no_highlight.status(*args, **kwargs)

    @staticmethod
    def is_debug() -> bool:
        return os.path.exists("debug.txt")

    @staticmethod
    def get_trackback(e: Exception) -> str:
        return f"{e}\n{("".join(traceback.format_exception(None, e, e.__traceback__))).strip()}"

    @staticmethod
    def debug(*args, **kwargs) -> None:
        LoguruLogger.debug(*args, **kwargs)
        LogHelper.logger.debug(*args, **kwargs)

    @staticmethod
    def info(*args, **kwargs) -> None:
        LoguruLogger.info(*args, **kwargs)
        LogHelper.logger.info(*args, **kwargs)

    @staticmethod
    def warning(*args, **kwargs) -> None:
        LoguruLogger.warning(*args, **kwargs)
        LogHelper.logger.warning(*args, **kwargs)

    @staticmethod
    def error(*args, **kwargs) -> None:
        LoguruLogger.error(*args, **kwargs)
        LogHelper.logger.error(*args, **kwargs)

    @staticmethod
    def critical(*args, **kwargs) -> None:
        LoguruLogger.critical(*args, **kwargs)
        LogHelper.logger.critical(*args, **kwargs)