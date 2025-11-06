#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   async_task_scheduler.py
@Time    :   2025-09-27 17:05:22
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   异步任务调度器
"""


from queue_sqlite_core import ShardedQueueOperation
from ...model import MessageItem
from ...constant import MessageStatus
from ...cycle.async_task_cycle import AsyncTaskCycle
from ...mounter.task_mounter import TaskMounter
import asyncio
from datetime import datetime
import threading
import multiprocessing
import logging
import json


class AsyncTaskScheduler:

    def __init__(
        self,
        queue_operation: ShardedQueueOperation,
        task_thread_num: int = multiprocessing.cpu_count() * 2,
    ):
        self.task_thread_num = task_thread_num
        self.is_running = False
        self.queue_operation = queue_operation
        self.task_thread = None  # 单一轮询线程

    async def _process_message(self, message: MessageItem):
        """处理单个消息"""
        try:
            if message.destination == "client":
                message.status = MessageStatus.COMPLETED
                message.result = {"result": "success"}
                message.updatetime = datetime.now()
                return message

            task_function = TaskMounter.get_task_function(message.destination)
            if task_function is None:
                raise ValueError(
                    f"Task function not found for destination: {message.destination}"
                )

            task_cycle = AsyncTaskCycle(message, task_function)
            await task_cycle.run()

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

    def _process_messages(self, message):
        """更新任务结果到数据库"""
        try:
            self.queue_operation.update_result(message.id, json.dumps(message.result))
            self.queue_operation.update_status(message.id, message.status)
        except Exception as e:
            logging.error(f"任务结果更新失败: {str(e)}")

    async def task_callback(self):
        """单一轮询线程，并行执行任务"""
        # 使用信号量控制并发任务数
        semaphore = asyncio.Semaphore(self.task_thread_num)

        async def limited_process_message(message):
            async with semaphore:
                return await self._process_message(MessageItem.from_dict(message))

        while self.is_running:
            try:
                message_list = self.queue_operation.dequeue(
                    size=self.task_thread_num * 2
                )
                if not message_list:
                    # 使用指数退避策略减少轮询开销
                    await asyncio.sleep(0.05)  # 增加延迟减少CPU使用
                    continue

                # 并发处理消息
                tasks = [
                    asyncio.create_task(limited_process_message(message))
                    for message in message_list
                ]

                # 等待所有任务完成
                completed, _ = await asyncio.wait(
                    tasks,
                    return_when=asyncio.ALL_COMPLETED,
                    timeout=30.0,  # 添加超时防止无限等待
                )

                # 批量处理结果
                for task in completed:
                    try:
                        message = task.result()
                        self._process_messages(message)
                    except Exception as e:
                        logging.error(f"处理任务结果时出错: {str(e)}")

            except Exception as e:
                logging.error(f"任务调度出错: {str(e)}")
                await asyncio.sleep(0.1)  # 出错时短暂延迟

    def _run_task_loop(self):
        """在新事件循环中运行任务处理循环"""
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 运行异步任务处理函数直到停止
            loop.run_until_complete(self.task_callback())
        except Exception as e:
            logging.error(f"任务调度出错: {str(e)}")
        finally:
            loop.close()

    def start_task_thread(self):
        if self.is_running:
            return

        self.is_running = True
        self.task_thread = threading.Thread(target=self._run_task_loop)
        self.task_thread.daemon = True
        self.task_thread.start()

    def stop_task_thread(self):
        if not self.is_running:
            return

        self.is_running = False
        if self.task_thread:
            self.task_thread.join(timeout=5.0)
            self.task_thread = None
