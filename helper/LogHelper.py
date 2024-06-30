import logging

class LogHelper:
    # 创建一个logger
    logger = logging.getLogger("KeywordGacha")
    logger.setLevel(logging.DEBUG)

    # 创建一个handler
    file_handler = TimedRotatingFileHandler(
                        filename = "KeywordGacha.log",
                        encoding = "utf-8",
                        when = "H", # 每小时轮转
                        interval = 1, # 轮转周期为1
                        backupCount = 24 # 保留24个备份
                    )
    console_handler = logging.StreamHandler()

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