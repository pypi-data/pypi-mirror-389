#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   async_receive_scheduler.py
@Time    :   2025-09-27 17:05:08
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   异步接收调度器
"""


from queue_sqlite_core import ShardedQueueOperation
from ...model import MessageItem
from typing import Callable
import asyncio
import threading
import concurrent.futures
import logging


class AsyncReceiveScheduler:
    def __init__(
        self, queue_operation: ShardedQueueOperation, receive_thread_num: int = 1
    ):
        self.callbacks = dict()
        self.receive_thread_num = receive_thread_num
        self.is_running = False
        self.lock = threading.Lock()
        self.queue_operation = queue_operation
        self.receive_thread = None  # 单一轮询线程

    def send_message(self, message: MessageItem, callback: Callable = None):  # type: ignore
        if callback is None:
            callback = lambda message: logging.info(message)
        # self.queue_operation.enqueue(message.to_dict())
        self.queue_operation.enqueue(message.to_dict_by_core())
        with self.lock:
            self.callbacks[message.id] = callback

    async def receive_message(self):
        """单一轮询线程，并行执行回调"""

        def callback_default(message):
            return message

        async with asyncio.Semaphore(self.receive_thread_num):
            while self.is_running:
                message_list = self.queue_operation.get_completed_messages()
                tasks = []
                if message_list:
                    for message in message_list:
                        message = MessageItem.from_dict(message)
                        with self.lock:
                            callback = self.callbacks.pop(message.id, None)
                            if callback is None:
                                callback = callback_default

                        tasks.append(
                            asyncio.create_task(self._safe_callback(callback, message))
                        )
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    await asyncio.sleep(0.05)

    async def _safe_callback(self, callback, message):
        """安全执行回调函数"""
        try:
            # 检查回调函数是否是异步函数
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                # 如果是同步函数，则在执行器中运行以避免阻塞事件循环
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.receive_thread_num
                ) as executor:
                    await loop.run_in_executor(executor, callback, message)
        except Exception as e:
            logging.error(f"回调执行错误: {str(e)}")
        finally:
            self.queue_operation.delete_message(message.id)

    def _run_receive_loop(self):
        """在新事件循环中运行接收消息循环"""
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 运行异步接收函数直到停止
            loop.run_until_complete(self.receive_message())
        except Exception as e:
            logging.error(f"任务调度出错: {str(e)}")
        finally:
            loop.close()

    def start_receive_thread(self):
        if self.is_running:
            return

        self.is_running = True
        # 创建单一轮询线程
        self.receive_thread = threading.Thread(
            target=self._run_receive_loop, daemon=True
        )
        self.receive_thread.start()

    def stop_receive_thread(self):
        if not self.is_running:
            return

        self.is_running = False
        # 等待轮询线程结束
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=5.0)
