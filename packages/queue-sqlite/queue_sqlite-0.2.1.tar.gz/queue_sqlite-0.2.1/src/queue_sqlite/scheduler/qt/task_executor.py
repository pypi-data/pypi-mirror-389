#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   task_executor.py
@Time    :   2025-10-28 14:31:25
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   任务执行器
"""


import asyncio
import logging
from typing import Any, Callable, Dict
from datetime import datetime
from ...constant import MessageStatus
from ...mounter.task_mounter import TaskMounter
from queue_sqlite_core import ShardedQueueOperation
from ...model.message_item import MessageItem
from qtpy.QtCore import QRunnable


class QtTaskExecutor(QRunnable):
    """Qt 任务执行器 - 修复版"""

    def __init__(
        self, message_data: Dict[str, Any], queue_operation: ShardedQueueOperation
    ):
        super().__init__()
        self.message_data = message_data
        self.queue_operation = queue_operation
        self.setAutoDelete(True)

    def run(self):
        """执行任务"""
        try:
            message = MessageItem.from_dict(self.message_data)

            if message.destination == "client":
                self._process_client_message(message)
                return

            task_function = TaskMounter.get_task_function(message.destination)
            if task_function is None:
                raise ValueError(f"任务函数未找到: {message.destination}")

            # 执行任务
            if asyncio.iscoroutinefunction(task_function):
                # 异步任务 - 在当前线程运行事件循环
                asyncio.run(self._execute_async_task(message, task_function))
            else:
                # 同步任务
                self._execute_sync_task(message, task_function)

        except Exception as e:
            logging.error(f"任务执行错误: {str(e)}")
            # 更新任务状态为失败
            try:
                self.queue_operation.update_status(
                    self.message_data["id"], MessageStatus.FAILED.value
                )
                self.queue_operation.update_result(
                    self.message_data["id"], f'{{"error": "{str(e)}"}}'
                )
            except Exception as update_error:
                logging.error(f"更新任务状态失败: {str(update_error)}")

    def _process_client_message(self, message: MessageItem):
        """处理客户端消息"""
        message.status = MessageStatus.COMPLETED
        message.result = {"result": "success"}
        message.updatetime = datetime.now()
        self._update_task_result(message)

    def _execute_sync_task(self, message: MessageItem, task_function: Callable):
        """执行同步任务"""
        from ...cycle.task_cycle import TaskCycle

        try:
            task_cycle = TaskCycle(message, task_function)
            task_cycle.run()

            status = task_cycle.get_task_status()
            if not status:
                raise ValueError("任务未完成")
            message.status = status
            if message.status == MessageStatus.FAILED:
                message.result = {"error": task_cycle.get_task_error()}
            else:
                # 获取序列化后的结果
                result_str = task_cycle.get_task_result()
                try:
                    import json

                    message.result = json.loads(result_str)
                except:
                    message.result = {"result": result_str}

            self._update_task_result(message)

        except Exception as e:
            logging.error(f"同步任务执行失败 {message.id}: {str(e)}")
            message.status = MessageStatus.FAILED
            message.result = {"error": str(e)}
            self._update_task_result(message)

    async def _execute_async_task(self, message: MessageItem, task_function: Callable):
        """执行异步任务"""
        from ...cycle.async_task_cycle import AsyncTaskCycle

        try:
            task_cycle = AsyncTaskCycle(message, task_function)
            await task_cycle.run()
            status = task_cycle.get_task_status()
            if not status:
                raise ValueError("任务未完成")
            message.status = status
            if message.status == MessageStatus.FAILED:
                message.result = {"error": task_cycle.get_task_error()}
            else:
                # 获取序列化后的结果
                result_str = task_cycle.get_task_result()
                try:
                    import json

                    message.result = json.loads(result_str)
                except:
                    message.result = {"result": result_str}

            self._update_task_result(message)

        except Exception as e:
            logging.error(f"异步任务执行失败 {message.id}: {str(e)}")
            message.status = MessageStatus.FAILED
            message.result = {"error": str(e)}
            self._update_task_result(message)

    def _update_task_result(self, message: MessageItem):
        """更新任务结果到数据库"""
        import json

        try:
            # 序列化结果
            result_str = json.dumps(message.result) if message.result else "{}"
            self.queue_operation.update_result(message.id, result_str)
            self.queue_operation.update_status(message.id, message.status.value)
        except Exception as e:
            logging.error(f"更新任务结果失败 {message.id}: {str(e)}")
