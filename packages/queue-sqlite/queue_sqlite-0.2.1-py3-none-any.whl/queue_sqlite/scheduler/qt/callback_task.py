#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   callback_task.py
@Time    :   2025-10-28 11:40:02
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   回调任务
"""
import asyncio
import logging
from queue_sqlite_core import ShardedQueueOperation
from ...model import MessageItem
from typing import Callable
from qtpy.QtCore import QRunnable


class QtCallbackTask(QRunnable):
    """Qt 回调任务"""

    def __init__(
        self,
        callback: Callable,
        message: MessageItem,
        queue_operation: ShardedQueueOperation,
    ):
        super().__init__()
        self.callback = callback
        self.message = message
        self.queue_operation = queue_operation
        self.setAutoDelete(True)

    def run(self):
        """执行回调函数"""
        try:
            # 检查是否是协程函数
            if asyncio.iscoroutinefunction(self.callback):
                # 对于异步回调，在当前线程中运行事件循环
                asyncio.run(self._run_async_callback())
            else:
                self.callback(self.message)
        except Exception as e:
            logging.error(f"回调执行错误: {str(e)}")
        finally:
            # 删除消息
            try:
                self.queue_operation.delete_message(self.message.id)
            except Exception as e:
                logging.error(f"删除消息失败 {self.message.id}: {str(e)}")

    async def _run_async_callback(self):
        """运行异步回调"""
        try:
            await self.callback(self.message)
        except Exception as e:
            logging.error(f"异步回调执行错误: {str(e)}")
