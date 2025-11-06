#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   __init__.py
@Time    :   2025-09-27 17:03:16
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   标准调度器
"""


from .receive_scheduler import ReceiveScheduler
from .task_scheduler import TaskScheduler
from .listen_data_scheduler import ListenDataScheduler
from ...model import MessageItem
from typing import Callable
from queue_sqlite_core import ShardedQueueOperation
from ...queue_operation.listen_operation import ListenOperation
from ..cleanup_scheduler import CleanupScheduler
import os
from ..base import BaseScheduler
from ...model import SchedulerConfig


class StandardQueueScheduler(BaseScheduler):
    def __init__(
        self,
        config: SchedulerConfig = SchedulerConfig(),
    ):
        self.queue_operation = ShardedQueueOperation(
            config.shard_num, config.queue_name
        )
        self.listen_operation = ListenOperation(
            os.path.join(self.queue_operation.db_dir, "listen.db")
        )
        self.listen_operation.create_table()

        self.listen_scheduler = ListenDataScheduler(self.listen_operation)
        self.receive_scheduler = ReceiveScheduler(
            self.queue_operation, config.receive_thread_num
        )
        self.task_scheduler = TaskScheduler(
            self.queue_operation, config.task_thread_num
        )
        self.cleanup_scheduler = CleanupScheduler(self.queue_operation)

    def send_message(self, message: MessageItem, callback: Callable):
        self.receive_scheduler.send_message(message, callback)

    def update_listen_data(self, key, value):
        self.listen_operation.update_listen_data(key, value)

    def get_listen_datas(self):
        return self.listen_operation.get_values()

    def get_listen_data(self, key):
        return self.listen_operation.get_value(key)

    def start(self):
        self.receive_scheduler.start_receive_thread()
        self.task_scheduler.start_task_thread()
        self.cleanup_scheduler.start_cleanup()
        self.listen_scheduler.start_listen_data()

    def stop(self):
        self.receive_scheduler.stop_receive_thread()
        self.listen_scheduler.stop_listen_data()
        self.task_scheduler.stop_task_thread()
        self.cleanup_scheduler.stop_cleanup()
        # self.queue_operation.close_all_connections()


__all__ = ["StandardQueueScheduler"]
