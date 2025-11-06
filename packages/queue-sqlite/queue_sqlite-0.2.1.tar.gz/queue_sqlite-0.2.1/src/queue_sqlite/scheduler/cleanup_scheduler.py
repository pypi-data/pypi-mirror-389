#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   cleanup_scheduler.py
@Time    :   2025-09-27 17:02:55
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   清理调度器
"""


# 新建清理调度器
import threading
import time
from queue_sqlite_core import ShardedQueueOperation
import logging


class CleanupScheduler:
    def __init__(
        self,
        queue_operation: ShardedQueueOperation,
        interval_minutes=60,
        remove_days=30,
    ):
        self.queue_operation = queue_operation
        self.interval = interval_minutes * 60  # 转换为秒
        self.is_running = False
        self.cleanup_thread = None
        self.remove_days = remove_days

        # for i in range(self.queue_operation.shard_num):
        # 清理过期但未处理的消息
        self.queue_operation.clean_expired_messages()
        # 彻底删除30天前的消息
        self.queue_operation.remove_expired_messages(self.remove_days)

    def cleanup_expired_messages(self):
        """清理过期消息"""
        while self.is_running:
            try:
                self.queue_operation.clean_expired_messages()

            except Exception as e:
                logging.error(f"清理消息错误: {str(e)}")

            # 休眠等待下次清理
            for _ in range(self.interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def start_cleanup(self):
        if self.is_running:
            return

        self.is_running = True
        self.cleanup_thread = threading.Thread(
            target=self.cleanup_expired_messages, daemon=True
        )
        self.cleanup_thread.start()

    def stop_cleanup(self):
        if not self.is_running:
            return

        self.is_running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2.0)
