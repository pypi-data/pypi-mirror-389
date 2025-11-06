#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   listen_scheduler.py
@Time    :   2025-10-28 14:22:38
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   监听调度器 - 改进版，解决数据库锁定问题
"""
import logging
import time
import sqlite3
from .listen_task import QtListenTask
from ...queue_operation.listen_operation import ListenOperation
from qtpy.QtCore import QThreadPool, QMutex, QMutexLocker
import threading


class QtListenScheduler:
    """Qt 监听调度器 - 改进版，解决数据库锁定问题"""

    def __init__(self, listen_operation: ListenOperation):
        self.listen_operation = listen_operation
        self.is_running = False
        self.listen_thread = None
        self.thread_pool = QThreadPool.globalInstance()
        self.db_mutex = QMutex()  # 数据库操作互斥锁

        # 监听配置
        self.poll_interval = 0.1  # 轮询间隔（秒）
        self.max_retries = 5  # 最大重试次数
        self.retry_delay = 0.2  # 重试延迟（秒）

        # 确保监听表存在
        self._ensure_listen_tables()

    def _ensure_listen_tables(self):
        """确保监听相关的表存在"""
        try:
            # 使用互斥锁保护数据库操作
            with QMutexLocker(self.db_mutex):
                # 检查表是否存在，如果不存在则创建
                conn = self.listen_operation._get_connection()

                # 检查 change_log 表是否存在
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='change_log'"
                )
                if cursor.fetchone() is None:
                    logging.info("创建缺失的 change_log 表")
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

    def _safe_listen_data(self):
        """安全地获取监听数据，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                # 使用互斥锁保护数据库操作
                with QMutexLocker(self.db_mutex):
                    status, change_data_items = self.listen_operation.listen_data()
                return status, change_data_items
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self.max_retries - 1:
                    logging.warning(
                        f"数据库锁定，第 {attempt + 1} 次重试获取监听数据..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f"获取监听数据失败: {str(e)}")
                    return False, []
            except Exception as e:
                logging.error(f"获取监听数据时发生未知错误: {str(e)}")
                return False, []

        return False, []

    def _process_listen_data(self, change_data_items):
        """处理监听数据"""
        processed_count = 0
        for data in change_data_items:
            try:
                # 修正字段索引
                if len(data) >= 8:
                    delete_id = data[0]  # id
                    table_name = data[1]  # table_name
                    row_id = data[2]  # row_id
                    column_name = data[3]  # column_name
                    old_value = data[4]  # old_value
                    new_value = data[5]  # new_value

                    # 使用线程池执行监听任务
                    task = QtListenTask(
                        column_name,
                        new_value,
                        int(delete_id),
                        self.listen_operation,
                        self.db_mutex,
                        self.max_retries,
                        self.retry_delay,
                    )
                    self.thread_pool.start(task)  # type: ignore
                    processed_count += 1

            except Exception as e:
                logging.error(f"处理监听数据失败: {str(e)}")

        return processed_count

    def _listen_loop(self):
        """监听数据变化循环 - 改进版"""
        consecutive_errors = 0
        max_consecutive_errors = 10

        while self.is_running:
            try:
                status, change_data_items = self._safe_listen_data()

                if status and change_data_items:
                    processed_count = self._process_listen_data(change_data_items)
                    consecutive_errors = 0  # 重置连续错误计数

                    if processed_count > 0:
                        logging.debug(f"成功处理 {processed_count} 个监听数据项")

                elif not status:
                    # 没有数据或获取失败，短暂休眠
                    time.sleep(self.poll_interval)
                    consecutive_errors += 1

                    # 如果连续错误太多，延长休眠时间
                    if consecutive_errors >= max_consecutive_errors:
                        # logging.warning("连续多次获取监听数据失败，延长休眠时间")
                        time.sleep(self.poll_interval * 5)
                        consecutive_errors = 0  # 重置计数
                else:
                    # 有状态但没有数据，正常休眠
                    time.sleep(self.poll_interval)
                    consecutive_errors = 0

            except Exception as e:
                logging.error(f"监听循环错误: {str(e)}")
                consecutive_errors += 1
                time.sleep(self.poll_interval * 2)  # 出错时延长休眠

    def start(self):
        """启动监听调度器"""
        if self.is_running:
            return

        self.is_running = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        logging.info("Qt 监听调度器已启动")

    def stop(self):
        """停止监听调度器"""
        if not self.is_running:
            return

        self.is_running = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=3.0)
        logging.info("Qt 监听调度器已停止")
