#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   async_listen_data_scheduler.py
@Time    :   2025-09-27 17:04:54
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   异步监听数据调度器
"""


from ...queue_operation.listen_operation import ListenOperation
import asyncio
from ...mounter.listen_mounter import ListenMounter
import threading
import multiprocessing
import concurrent.futures


class AsyncListenDataScheduler:
    def __init__(self, listen_operation: ListenOperation):
        self.listen_operation = listen_operation
        self.is_running = False
        self.thread_num = multiprocessing.cpu_count()
        self.listen_thread = None

    async def _process_listen_data(self, key, value, delete_id):
        listen_function = ListenMounter.get_Listener_function(key)
        if listen_function:
            if asyncio.iscoroutinefunction(listen_function):
                await listen_function(value)
            else:
                try:
                    loop = asyncio.get_event_loop()
                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=self.thread_num
                    ) as executor:
                        await loop.run_in_executor(executor, listen_function, value)
                    listen_function(value)
                except Exception as e:
                    ValueError(f"Error in {key} listener function: {e}")
                finally:
                    self.listen_operation.delete_change_log(delete_id=delete_id)

    async def listen(self):
        async with asyncio.Semaphore(self.thread_num):
            while self.is_running:
                status, change_data_items = self.listen_operation.listen_data()
                tasks = []
                if status:
                    for data in change_data_items:
                        key = data[6]
                        new_value = data[7]
                        delete_id = data[0]
                        tasks.append(
                            asyncio.create_task(
                                self._process_listen_data(key, new_value, delete_id)
                            )
                        )
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)

                else:
                    await asyncio.sleep(0.05)

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
