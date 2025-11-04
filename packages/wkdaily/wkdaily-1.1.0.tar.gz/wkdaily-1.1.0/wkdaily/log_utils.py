import abc
import logging
import sys
from typing import Protocol, TextIO, override


class LoggerProtocol(Protocol):
    def error(self, *args) -> None: ...
    def info(self, *args) -> None: ...
    def debug(self, *args) -> None: ...


class BaseLoggerFactory(abc.ABC):
    @abc.abstractmethod
    def get_logger(self, name: str) -> LoggerProtocol:
        raise NotImplementedError


logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def console_handler() -> logging.StreamHandler[TextIO]:
    handler = logging.StreamHandler()
    # 输出到控制台
    _ = handler.setStream(sys.stdout)
    # 设置格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


class LoggingFactory(BaseLoggerFactory):
    def __init__(self):
        pass

    @override
    def get_logger(self, name: str) -> LoggerProtocol:
        return self._init_logger(name)

    def _init_logger(self, name: str):
        logger: logging.Logger = logging.getLogger(name)
        logger.removeHandler(logging.getLogger().handlers[0])
        logger.addHandler(console_handler())
        return logger


logger_factory = LoggingFactory()


def get_logger(name: str) -> LoggerProtocol:
    return logger_factory.get_logger(name)
