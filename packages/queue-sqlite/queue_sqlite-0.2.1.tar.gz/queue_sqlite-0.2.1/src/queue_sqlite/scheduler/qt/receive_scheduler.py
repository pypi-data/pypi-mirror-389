#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   receive_scheduler.py
@Time    :   2025-10-28 14:31:06
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   接收调度器
"""


from typing import Callable, Optional
from queue_sqlite_core import ShardedQueueOperation
from qtpy.QtCore import QThreadPool
import threading
from ...model import MessageItem
import time
import logging
from .callback_task import QtCallbackTask


class QtReceiveScheduler:
    """Qt 接收调度器 - 独立实现"""

    def __init__(
        self, queue_operation: ShardedQueueOperation, receive_thread_num: int = 1
    ):
        self.callbacks = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.queue_operation = queue_operation
        self.receive_thread = None
        self.thread_pool = QThreadPool.globalInstance()

    def send_message(self, message: MessageItem, callback: Optional[Callable] = None):
        """发送消息到队列"""
        if callback is None:
            callback = lambda message: logging.info(f"收到消息: {message.id}")

        # 入队消息
        self.queue_operation.enqueue(message.to_dict_by_core())
        with self.lock:
            self.callbacks[message.id] = callback

    def _receive_loop(self):
        """接收消息循环"""
        while self.is_running:
            try:
                # 获取已完成的消息
                message_list = self.queue_operation.get_completed_messages()
                if message_list:
                    for message_data in message_list:
                        try:
                            message = MessageItem.from_dict(message_data)

                            with self.lock:
                                callback = self.callbacks.pop(message.id, None)
                                if callback is None:
                                    callback = lambda msg: None

                            # 使用线程池执行回调
                            task = QtCallbackTask(
                                callback, message, self.queue_operation
                            )
                            self.thread_pool.start(task)  # type: ignore

                        except Exception as e:
                            logging.error(f"处理完成消息失败: {str(e)}")
                            # 即使处理失败也尝试删除消息
                            try:
                                self.queue_operation.delete_message(message_data["id"])
                            except:
                                pass
                else:
                    time.sleep(0.05)  # 短暂休眠避免CPU空转

            except Exception as e:
                logging.error(f"接收消息循环错误: {str(e)}")
                time.sleep(0.1)  # 出错时稍长休眠

    def start(self):
        """启动接收调度器"""
        if self.is_running:
            return

        self.is_running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        logging.info("Qt 接收调度器已启动")

    def stop(self):
        """停止接收调度器"""
        if not self.is_running:
            return

        self.is_running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=3.0)
        logging.info("Qt 接收调度器已停止")
