#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   __init__.py
@Time    :   2025-10-26 10:26:16
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   Qt调度器 - 独立实现
"""

import logging
import os
from ..base import BaseScheduler
from ...model import MessageItem, SchedulerConfig
from queue_sqlite_core import ShardedQueueOperation
from ...queue_operation.listen_operation import ListenOperation
from .receive_scheduler import QtReceiveScheduler
from .listen_scheduler import QtListenScheduler
from .task_scheduler import QtTaskScheduler
from ..cleanup_scheduler import CleanupScheduler as QtCleanupScheduler
from qtpy.QtCore import QThreadPool
from qtpy.QtWidgets import QApplication
from typing import Callable, Dict, Any, List


class QtQueueScheduler(BaseScheduler):
    """完全独立的 Qt 队列调度器 - 修复版"""

    qt_type = None

    def __init__(
        self,
        config: SchedulerConfig = SchedulerConfig(),
    ):

        # 初始化队列操作
        self.queue_operation = ShardedQueueOperation(
            config.shard_num, config.queue_name
        )

        # 初始化监听操作
        db_dir = f"cache/{config.queue_name}"
        os.makedirs(db_dir, exist_ok=True)
        self.listen_operation = ListenOperation(f"{db_dir}/listen.db")

        # 确保监听表被创建
        self._ensure_listen_operation_tables()

        # 初始化各个独立的调度器组件
        self.receive_scheduler = QtReceiveScheduler(
            self.queue_operation, config.receive_thread_num
        )
        self.task_scheduler = QtTaskScheduler(
            self.queue_operation, config.task_thread_num
        )
        self.listen_scheduler = QtListenScheduler(self.listen_operation)
        self.cleanup_scheduler = QtCleanupScheduler(self.queue_operation)

    @classmethod
    def is_available(cls) -> bool:
        # 检查  PySide6/PyQt6/PyQt5/PySide2 模块中的一个
        import importlib

        qt_modules = ["PySide6", "PyQt6", "PyQt5", "PySide2"]
        for module in qt_modules:
            try:
                importlib.import_module(module)
                cls.qt_type = module
                logging.info(f"已找到 Qt 模块: {module}")
                print(f"已找到 Qt 模块: {module}")
                return True
            except ImportError:  # 模块未找到
                continue
        return False

    def _ensure_qapplication(self):
        """确保 QApplication 实例存在"""
        try:
            if not QApplication.instance():
                # 对于非GUI应用，创建无窗口的QApplication
                import sys

                self.app = QApplication(sys.argv if hasattr(sys, "argv") else [])
                logging.info("已创建 QApplication 实例")
        except Exception as e:
            logging.warning(f"创建 QApplication 失败: {str(e)}")

    def _ensure_listen_operation_tables(self):
        """确保监听操作的表被正确创建"""
        try:
            # 强制重新创建表
            self.listen_operation.create_table()

            # 额外检查 change_log 表
            conn = self.listen_operation._get_connection()
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='change_log'"
            )
            if cursor.fetchone() is None:
                logging.warning("change_log 表不存在，尝试手动创建")
                conn.execute(
                    """
                    CREATE TABLE change_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT,
                        row_id INTEGER,
                        column_name TEXT,
                        old_value TEXT,
                        new_value TEXT,
                        is_delete integer DEFAULT 0,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                conn.commit()

        except Exception as e:
            logging.error(f"确保监听表存在失败: {str(e)}")

    def send_message(self, message: MessageItem, callback: Callable):
        """发送消息到队列"""
        self.receive_scheduler.send_message(message, callback)

    def update_listen_data(self, key: str, value: str):
        """更新监听数据"""
        self.listen_operation.update_listen_data(key, value)

    def get_listen_datas(self) -> List:
        """获取所有监听数据"""
        return self.listen_operation.get_values()

    def get_listen_data(self, key: str):
        """获取单个监听数据"""
        return self.listen_operation.get_value(key)

    def start(self):
        """启动所有调度器组件"""
        # 确保有 QApplication 实例（对于 GUI 应用）
        self._ensure_qapplication()
        self.receive_scheduler.start()
        self.task_scheduler.start()
        self.cleanup_scheduler.start_cleanup()
        self.listen_scheduler.start()
        logging.info("Qt 队列调度器已完全启动")

    def stop(self):
        """停止所有调度器组件"""
        self.listen_scheduler.stop()
        self.cleanup_scheduler.stop_cleanup()
        self.task_scheduler.stop()
        self.receive_scheduler.stop()
        logging.info("Qt 队列调度器已完全停止")

    def get_queue_info(self) -> Dict[str, Any]:
        """获取队列信息"""
        try:
            return {
                "queue_length": self.queue_operation.get_queue_length(),
                "shard_num": self.queue_operation.shard_num,
                "db_dir": self.queue_operation.db_dir,
                "active_threads": QThreadPool.globalInstance().activeThreadCount(),  # type: ignore
                "max_threads": QThreadPool.globalInstance().maxThreadCount(),  # type: ignore
            }
        except Exception as e:
            logging.error(f"获取队列信息失败: {str(e)}")
            return {}
