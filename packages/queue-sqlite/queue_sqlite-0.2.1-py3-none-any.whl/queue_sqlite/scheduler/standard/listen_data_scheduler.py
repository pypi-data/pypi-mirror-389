#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   listen_data_scheduler.py
@Time    :   2025-09-27 17:03:39
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   监听数据调度器
"""


from ...queue_operation.listen_operation import ListenOperation
from concurrent.futures import ThreadPoolExecutor
from ...mounter.listen_mounter import ListenMounter
import threading
import multiprocessing


class ListenDataScheduler:
    def __init__(self, listen_operation: ListenOperation):
        self.listen_operation = listen_operation
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
        self.listen_thread = None

    def _process_listen_data(self, key, value, delete_id):
        listen_function = ListenMounter.get_Listener_function(key)
        if listen_function:
            try:
                listen_function(value)
            except Exception as e:
                ValueError(f"Error in {key} listener function: {e}")
            finally:
                self.listen_operation.delete_change_log(delete_id=delete_id)

    def listen(self):
        while self.is_running:
            status, change_data_items = self.listen_operation.listen_data()
            if status:
                for data in change_data_items:
                    key = data[6]
                    new_value = data[7]
                    delete_id = data[0]
                    self.executor.submit(
                        self._process_listen_data, key, new_value, delete_id
                    )

    def start_listen_data(self):
        if self.is_running:
            return
        self.is_running = True
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def stop_listen_data(self):
        if not self.is_running:
            return
        self.is_running = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)

        self.executor.shutdown(wait=True)
