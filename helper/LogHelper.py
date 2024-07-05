import re
import logging
from logging.handlers import RotatingFileHandler

class ColorStreamHandler(logging.StreamHandler):

    LEVEL_NAME = [
        " [DEBUG] ",
        " [INFO] ",
        " [WARNING] ",
        " [ERROR] ",
        " [CRITICAL] ",      
    ]

    COLOR_LEVEL_NAME = [
        " [\033[94mDEBUG\033[0m] ",         # 蓝色
        " [\033[92mINFO\033[0m] ",          # 绿色
        " [\033[93mWARNING\033[0m] ",       # 黄色
        " [\033[91mERROR\033[0m] ",         # 红色
        " [\033[1;95mCRITICAL\033[0m] ",    # 亮品红色     
    ]

    def emit(self, record):
        message = self.format(record)

        for k, v in enumerate(self.LEVEL_NAME):
            if v in message:
                # message = message.replace(v, self.COLOR_LEVEL_NAME[k])
                message = re.sub(re.escape(v), self.COLOR_LEVEL_NAME[k], message, count = 1)
                break

        print(message)

class LogHelper:
    # 创建一个logger
    logger = logging.getLogger("KeywordGacha")
    logger.setLevel(logging.DEBUG)

    # 创建一个handler
    file_handler = RotatingFileHandler(
                        filename = "KeywordGacha.log",
                        encoding = "utf-8",
                        maxBytes = 1 * 1024 * 1024, 
                        backupCount = 1
                    )
    console_handler = ColorStreamHandler()

    # 定义输出格式
    file_handler_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 设置输出格式
    file_handler.setFormatter(file_handler_formatter)
    console_handler.setFormatter(console_handler_formatter)

    # 给logger添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 静态方法定义
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