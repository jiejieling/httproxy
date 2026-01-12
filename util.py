import logging
import logging.handlers
import asyncio


def setup_logging(filename, log_size, verbose):
    """
    设置日志记录，包括异步任务ID过滤器。
    :param filename: 日志文件名，'-'表示标准输出
    :param log_size: 日志文件最大大小（MB）
    :param verbose: 是否启用详细日志记录
    :return: 配置好的logger对象
    """
    class LoggingAsyncTaskIdFilter(logging.Filter):
        def filter(self, record):
            try:
                record.async_task_id = asyncio.current_task().get_name()
            except RuntimeError:  # 当不在协程中时
                record.async_task_id = 'Main'
            return True

    logger = logging.getLogger("zzapp")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # 添加task_id过滤器
    logger.addFilter(LoggingAsyncTaskIdFilter())

    if not filename or filename in ('-', 'STDOUT'):
        handler = logging.StreamHandler()
    else:
        handler = logging.handlers.RotatingFileHandler(
            filename, maxBytes=(log_size * (1 << 20)), backupCount=5)

    formatter = logging.Formatter(
        "%(asctime)s %(name)s[%(process)d][%(thread)d][%(async_task_id)s] [%(levelname)s] [%(filename)s:%(lineno)d]%(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
