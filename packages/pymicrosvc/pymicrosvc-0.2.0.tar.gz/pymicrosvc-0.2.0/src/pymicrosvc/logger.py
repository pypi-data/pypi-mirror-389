# -*- coding: utf-8 -*-
import logging
import os
from logging.handlers import RotatingFileHandler


class PyMicroSvcLogger:
    logger: logging.Logger | None = None

    @classmethod
    def setup_logger(cls):
        PyMicroSvcLogger.logger = logging.getLogger("py-micro-svc")
        PyMicroSvcLogger.logger.setLevel(logging.INFO)

        # 防止重复添加处理器
        if PyMicroSvcLogger.logger.handlers:
            return

        log_file = os.path.expanduser("~") + "/logs/py-micro-svc/py-micro-svc.log"
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 只添加文件处理器
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # 保留5个备份文件
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        PyMicroSvcLogger.logger.addHandler(file_handler)

        # 关键修复：防止日志向父logger传播
        PyMicroSvcLogger.logger.propagate = False

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if PyMicroSvcLogger.logger is None:
            PyMicroSvcLogger.setup_logger()
        if PyMicroSvcLogger.logger is None:
            return logging.getLogger("py-micro-svc")
        else:
            return PyMicroSvcLogger.logger
