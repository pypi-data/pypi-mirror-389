#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   __init__.py
@Time    :   2025-09-27 17:05:40
@Author  :   chakcy
@Email   :   947105045@qq.com
@License :   (C)Copyright 2020-2025, chakcy
@package :   queue_sqlite
@description   :   A high-performance, SQLite-based distributed task queue system with Rust-backed core operations. Supports task mounting, message listening, priority handling, retry mechanisms, and automatic cleanup of expired messages. Ideal for building reliable, scalable background task processing systems.
"""

from . import constant
from . import cycle
from . import model
from . import mounter
from . import queue_operation
from . import scheduler
import logging
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# 设置 error 级别日志写入 error.log 文件
if not os.path.exists("log"):
    os.mkdir("log")
error_log_handler = logging.FileHandler("log/error.log", encoding="utf-8")
error_log_handler.setLevel(logging.ERROR)
error_log_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logging.getLogger().addHandler(error_log_handler)

__title__ = "queue_sqlite"
__version__ = "0.2.1"
__author__ = "chakcy"
__email__ = "947105045@qq.com"
__license__ = "MIT"
__copyright__ = "Copyright 2020-2025, chakcy"
__all__ = ["constant", "cycle", "model", "mounter", "queue_operation", "scheduler"]
__version_info__ = tuple(int(i) for i in __version__.split("."))
__description__ = "A high-performance, SQLite-based distributed task queue system with Rust-backed core operations. Supports task mounting, message listening, priority handling, retry mechanisms, and automatic cleanup of expired messages. Ideal for building reliable, scalable background task processing systems."


def get_info():
    return {
        "name": __title__,
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "copyright": __copyright__,
        "description": __description__,
    }
