#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   task_scheduler.py
@Time    :   2025-09-27 17:04:09
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   任务调度器
"""


import logging
from queue_sqlite_core import ShardedQueueOperation
from ...model import MessageItem
from ...constant import MessageStatus
from ...cycle.task_cycle import TaskCycle
from ...mounter.task_mounter import TaskMounter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import time
import threading
import multiprocessing
import json


class TaskScheduler:
    def __init__(
        self,
        queue_operation: ShardedQueueOperation,
        task_thread_num: int = multiprocessing.cpu_count() * 2,
    ):
        self.task_thread_num = task_thread_num
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=task_thread_num)  # 并行执行任务
        self.queue_operation = queue_operation
        self.task_thread = None  # 单一轮询线程

    def _process_message(self, message: MessageItem):
        """处理单个消息"""
        try:
            if message.destination == "client":
                message.status = MessageStatus.COMPLETED
                message.result = {"result": "success"}
                message.updatetime = datetime.now()
                return message

            task_function = TaskMounter.get_task_function(message.destination)
            task_cycle = TaskCycle(message, task_function)
            task_cycle.run()

            message.status = task_cycle.get_task_status()  # type: ignore
            if message.status == MessageStatus.FAILED:
                message.result = {"error": task_cycle.get_task_error()}
            else:
                message.result = task_cycle.get_task_result()  # type: ignore
            message.updatetime = datetime.now()
        except Exception as e:
            message.status = MessageStatus.FAILED
            message.result = {"error": str(e)}
            message.updatetime = datetime.now()

        return message

    def _update_result(self, message):
        """更新任务结果到数据库"""
        try:
            self.queue_operation.update_result(message.id, json.dumps(message.result))
            self.queue_operation.update_status(message.id, message.status)
        except Exception as e:
            logging.error(f"任务结果更新失败: {str(e)}")

    def task_callback(self):
        """单一轮询线程，并行执行任务"""
        while self.is_running:
            try:
                message_list = self.queue_operation.dequeue(
                    size=self.task_thread_num * 2
                )
                if message_list:
                    # 并行处理所有获取到的消息
                    for message in message_list:
                        self.executor.submit(
                            lambda m: self._update_result(self._process_message(m)),
                            MessageItem.from_dict(message),
                        )
                else:
                    time.sleep(0.1)  # 适当休眠
            except Exception as e:
                logging.error(f"任务调度错误: {str(e)}")
                time.sleep(1)

    def start_task_thread(self):
        if self.is_running:
            return

        self.is_running = True
        # 创建单一轮询线程
        self.task_thread = threading.Thread(target=self.task_callback, daemon=True)
        self.task_thread.start()

    def stop_task_thread(self):
        if not self.is_running:
            return

        self.is_running = False
        # 等待轮询线程结束
        if self.task_thread and self.task_thread.is_alive():
            self.task_thread.join(timeout=2.0)

        # 关闭线程池
        self.executor.shutdown(wait=True)
