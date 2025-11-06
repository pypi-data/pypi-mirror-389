#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   receive_scheduler.py
@Time    :   2025-09-27 17:03:55
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   接收调度器
"""


from queue_sqlite_core import ShardedQueueOperation
from ...model import MessageItem
from typing import Callable
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import logging


class ReceiveScheduler:
    def __init__(
        self, queue_operation: ShardedQueueOperation, receive_thread_num: int = 1
    ):
        self.callbacks = dict()
        self.receive_thread_num = receive_thread_num
        self.is_running = False
        self.executor = ThreadPoolExecutor(
            max_workers=receive_thread_num
        )  # 并行执行回调
        self.lock = threading.Lock()
        self.queue_operation = queue_operation
        self.receive_thread = None  # 单一轮询线程

    def send_message(self, message: MessageItem, callback: Callable = None):  # type: ignore
        if callback is None:
            callback = lambda message: logging.info(f"receive message: {message.id}")
        # self.queue_operation.enqueue(message.to_dict())
        self.queue_operation.enqueue(message.to_dict_by_core())
        with self.lock:
            self.callbacks[message.id] = callback

    def receive_message(self):
        """单一轮询线程，并行执行回调"""

        while self.is_running:
            message_list = self.queue_operation.get_completed_messages()
            if message_list:
                for message in message_list:
                    message = MessageItem.from_dict(message)
                    callback_default = lambda message: message
                    with self.lock:
                        callback = self.callbacks.pop(message.id, None)
                        if callback is None:
                            callback = callback_default

                    # 使用线程池并行执行回调
                    self.executor.submit(self._safe_callback, callback, message)
            else:
                time.sleep(0.1)  # 适当休眠避免CPU空转

    def _safe_callback(self, callback, message):
        """安全执行回调函数"""
        try:
            callback(message)
        except Exception as e:
            logging.error(f"回调执行错误: {str(e)}")
        finally:
            self.queue_operation.delete_message(message.id)

    def start_receive_thread(self):
        if self.is_running:
            return

        self.is_running = True
        # 创建单一轮询线程
        self.receive_thread = threading.Thread(target=self.receive_message, daemon=True)
        self.receive_thread.start()

    def stop_receive_thread(self):
        if not self.is_running:
            return

        self.is_running = False
        # 等待轮询线程结束
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)

        # 关闭线程池
        self.executor.shutdown(wait=True)
