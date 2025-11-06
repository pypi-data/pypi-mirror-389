#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   listen_task.py
@Time    :   2025-10-28 14:30:41
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   监听任务 - 改进版，解决数据库锁定问题
"""

from queue_sqlite.queue_operation.listen_operation import ListenOperation
from ...mounter.listen_mounter import ListenMounter
import logging
from qtpy.QtCore import QRunnable, QMutexLocker
import asyncio
from typing import Callable
import time
import sqlite3


class QtListenTask(QRunnable):
    """Qt 监听任务 - 改进版，解决数据库锁定问题"""

    def __init__(
        self,
        key: str,
        value: str,
        delete_id: int,
        listen_operation: ListenOperation,
        db_mutex,
        max_retries=5,
        retry_delay=0.2,
    ):
        super().__init__()
        self.key = key
        self.value = value
        self.delete_id = delete_id
        self.listen_operation = listen_operation
        self.db_mutex = db_mutex
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.setAutoDelete(True)

    def run(self):
        """执行监听回调"""
        try:
            listen_function = ListenMounter.get_Listener_function(self.key)
            if listen_function:
                if asyncio.iscoroutinefunction(listen_function):
                    # 异步监听函数
                    asyncio.run(self._run_async_listener(listen_function))
                else:
                    # 同步监听函数
                    listen_function(self.value)
        except Exception as e:
            logging.error(f"监听函数执行错误 {self.key}: {str(e)}")
        finally:
            # 安全删除变更日志
            self._safe_delete_change_log()

    def _safe_delete_change_log(self):
        """安全删除变更日志，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                # 使用互斥锁保护数据库操作
                with QMutexLocker(self.db_mutex):
                    self.listen_operation.delete_change_log(self.delete_id)
                break  # 成功则退出循环
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self.max_retries - 1:
                    logging.debug(
                        f"删除变更日志时数据库锁定，第 {attempt + 1} 次重试..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f"删除变更日志失败 {self.delete_id}: {str(e)}")
                    break
            except Exception as e:
                logging.error(f"删除变更日志失败 {self.delete_id}: {str(e)}")
                break

    async def _run_async_listener(self, listen_function: Callable):
        """执行异步监听函数"""
        try:
            await listen_function(self.value)
        except Exception as e:
            logging.error(f"异步监听函数执行错误 {self.key}: {str(e)}")
