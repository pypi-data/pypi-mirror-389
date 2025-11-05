# easylog_default.py
import os
import sys
import logging
from colorama import init, Fore
from logging.handlers import RotatingFileHandler

# 初始化 colorama
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, "")
        reset = Fore.RESET
        return f"{color}{log_message}{reset}"


class EasyLogManager:
    """
    日志管理器，支持：
    - 默认 Logger
    - 多 logger
    - 彩色控制台和文件日志
    - RotatingFileHandler
    - 启动时清空日志文件
    """

    _loggers = {}

    # 默认参数
    DEFAULT_LOG_FOLDER = "/tmp/mepybase/logs"
    DEFAULT_LOG_FILE = "log.log"
    DEFAULT_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 80 * 1024 * 1024
    DEFAULT_BACKUP_COUNT = 2

    @classmethod
    def get_logger(
        cls,
        name: str = "default",
        log_file: str = None,
        log_folder: str = None,
        level: int = None,
        max_bytes: int = None,
        backup_count: int = None,
    ) -> logging.Logger:
        """
        获取 logger 实例，如果已存在则返回现有 logger。
        支持覆盖默认路径、文件、等级等参数。
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level or cls.DEFAULT_LEVEL)
        logger.propagate = False  # 避免重复打印到 root logger

        # ✅ 清理已有 handler 避免重复打印
        if logger.hasHandlers():
            logger.handlers.clear()

        # 路径与文件名
        folder = log_folder or cls.DEFAULT_LOG_FOLDER
        file_name = log_file or cls.DEFAULT_LOG_FILE
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_path = os.path.join(folder, file_name)

        # ✅ 启动时清空日志文件
        if os.path.exists(file_path):
            open(file_path, "w").close()

        # 文件 Handler（带颜色）
        fh = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes or cls.DEFAULT_MAX_BYTES,
            backupCount=backup_count or cls.DEFAULT_BACKUP_COUNT,
            encoding="utf-8",
        )
        fh.setFormatter(
            ColoredFormatter(
                "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(fh)

        # 控制台 Handler（彩色）
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(
            ColoredFormatter(
                "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(ch)

        # 异常捕获
        def log_exception(exc_type, exc_value, exc_traceback):
            logger.error(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback),
            )

        sys.excepthook = log_exception

        cls._loggers[name] = logger
        return logger


# ===============================
# 测试示例
# ===============================
if __name__ == "__main__":
    # 默认 logger
    default_logger = EasyLogManager.get_logger()
    default_logger.info("This is default log message")

    # 自定义 perf logger
    perf_logger = EasyLogManager.get_logger(
        name="perf",
        log_file="perf.log",
        log_folder="./logs",
        level=logging.DEBUG,
    )
    perf_logger.info("This is perf log message")

    # 测试各种级别
    default_logger.debug("Debug message (should not appear by default)")
    default_logger.warning("Warning message")
    default_logger.error("Error message")
    perf_logger.debug("Debug message in perf logger")
    perf_logger.error("Error message in perf logger")

    # 模拟异常
    try:
        1 / 0
    except Exception:
        default_logger.error("Exception in default logger", exc_info=True)
        perf_logger.error("Exception in perf logger", exc_info=True)
