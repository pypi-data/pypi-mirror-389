from queue_sqlite.model import MessageItem
from queue_sqlite.scheduler import QueueScheduler
import time
from async_taks import *
import threading
import psutil


class TestAsyncScheduler:

    callback_counter = 0
    lock = threading.Lock()
    is_monitoring = False

    @classmethod
    def monitor_resources(cls):
        """监控资源使用情况"""
        while cls.is_monitoring:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            print(f"CPU使用率: {cpu}%, 内存使用率: {memory}%")
            time.sleep(0.5)

    @classmethod
    async def _callback(cls, message_item: MessageItem):
        with cls.lock:
            cls.callback_counter += 1
        # if cls.callback_counter % 100 == 0:  # 每100个任务打印一次
        #     print(f"callback: {cls.callback_counter}")
        # print(f"callback: {message_item}")
        # print(f"callback: {message_item.id}")
        # print(f"callback: {message_item.expire_time}")
        # print(f"callback: {message_item.tags}")

    @classmethod
    def test_async_scheduler(cls):
        """测试异步调度器"""
        TASK_NUM = 10000
        messages = []
        for i in range(TASK_NUM):
            message_item = MessageItem(content={"num": i}, destination="async_example")
            messages.append(message_item)

        cls.is_monitoring = True
        monitor_thread = threading.Thread(target=cls.monitor_resources, daemon=True)
        monitor_thread.start()
        queue_scheduler = QueueScheduler(
            scheduler_type="async",
        )

        start_time = time.perf_counter()
        queue_scheduler.start()

        for message_item in messages:
            message_item: MessageItem
            queue_scheduler.send_message(message_item, cls._callback)

        while (
            queue_scheduler.queue_operation.get_queue_length() > 0
            or cls.callback_counter < TASK_NUM
        ):  # 30秒超时
            time.sleep(0.5)
            print(f"当前队列长度：{queue_scheduler.queue_operation.get_queue_length()}")
            print(f"当前回调数量：{cls.callback_counter}")

        queue_scheduler.stop()

        print(f"当前队列长度：{queue_scheduler.queue_operation.get_queue_length()}")
        print(f"测试函数：斐波那契数列")
        print(f"次数：{TASK_NUM}")
        print(f"总耗时: {time.perf_counter() - start_time:.2f}秒")

        cls.is_monitoring = False
        monitor_thread.join(timeout=1)
