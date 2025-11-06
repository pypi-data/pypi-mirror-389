#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   task_scheduler.py
@Time    :   2025-10-28 14:19:39
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   Qt 任务调度器
"""
import logging
from qtpy.QtCore import QThreadPool
from .task_executor import QtTaskExecutor
from queue_sqlite_core import ShardedQueueOperation
import time
import threading


class QtTaskScheduler:
    """Qt 任务调度器 - 独立实现"""

    def __init__(
        self, queue_operation: ShardedQueueOperation, task_thread_num: int = 4
    ):
        self.is_running = False
        self.queue_operation = queue_operation
        self.task_thread = None
        self.thread_pool = QThreadPool.globalInstance()
        # 设置最大线程数
        self.thread_pool.setMaxThreadCount(max(1, task_thread_num))  # type: ignore

    def _task_loop(self):
        """任务处理循环"""
        while self.is_running:
            try:
                # 出队消息进行处理
                message_list = self.queue_operation.dequeue(
                    size=self.thread_pool.maxThreadCount() * 2  # type: ignore
                )
                if message_list:
                    for message_data in message_list:
                        # 使用线程池执行任务
                        task = QtTaskExecutor(message_data, self.queue_operation)
                        self.thread_pool.start(task)  # type: ignore
                else:
                    time.sleep(0.05)  # 短暂休眠

            except Exception as e:
                logging.error(f"任务调度循环错误: {str(e)}")
                time.sleep(0.1)

    def start(self):
        """启动任务调度器"""
        if self.is_running:
            return

        self.is_running = True
        self.task_thread = threading.Thread(target=self._task_loop, daemon=True)
        self.task_thread.start()
        logging.info("Qt 任务调度器已启动")

    def stop(self):
        """停止任务调度器"""
        if not self.is_running:
            return

        self.is_running = False
        if self.task_thread and self.task_thread.is_alive():
            self.task_thread.join(timeout=3.0)
        logging.info("Qt 任务调度器已停止")
