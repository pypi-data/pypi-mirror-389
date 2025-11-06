#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   __init__.py
@Time    :   2025-09-27 17:02:39
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   队列调度器
"""

from .standard import StandardQueueScheduler
from ._async import AsyncQueueScheduler
from .base import BaseScheduler
from ..model import MessageItem, SchedulerConfig
from typing import Callable, Literal
import logging


SCHEDULER_TYPES = {"standard": StandardQueueScheduler, "async": AsyncQueueScheduler}

try:
    from .qt import QtQueueScheduler

    print(SCHEDULER_TYPES)
    if QtQueueScheduler.is_available():
        SCHEDULER_TYPES["qt"] = QtQueueScheduler
except ImportError:
    logging.warning(
        "Qt is not available, if you want to use it, please install PyQt5/PyQt6/PySide6"
    )

SchedulerType = Literal["standard", "async", "qt"]


class QueueScheduler(BaseScheduler):
    def __init__(
        self,
        scheduler_type: SchedulerType = "standard",
        config: SchedulerConfig = SchedulerConfig(),
    ):
        scheduler_class = SCHEDULER_TYPES.get(scheduler_type, None)
        if not scheduler_class:
            raise ValueError(f"Invalid scheduler type: {scheduler_type}")
        self.scheduler = scheduler_class(config)

        if self.scheduler:
            self.queue_operation = self.scheduler.queue_operation

    def send_message(self, message: MessageItem, callback: Callable):
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        self.scheduler.send_message(message, callback)

    def start(self):
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        self.scheduler.start()

    def stop(self):
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        self.scheduler.stop()

    def update_listen_data(self, key, value):
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        self.scheduler.update_listen_data(key, value)

    def get_listen_datas(self):
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        return self.scheduler.get_listen_datas()

    def get_listen_data(self, key):
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        return self.scheduler.get_listen_data(key)


__all__ = ["QueueScheduler"]
