#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   test_pyside6_scheduler.py
@Time    :   2025-10-26 10:40:00
@Author  :   chakcy
@description   :   独立 PySide6 调度器测试
"""

import time
from queue_sqlite.scheduler import QueueScheduler
from queue_sqlite.model import MessageItem
from queue_sqlite.mounter import task


@task(meta={"task_name": "pyside6_example"})
def pyside6_example_task(message_item: MessageItem):
    """PySide6 调度器测试任务"""
    print(f"处理任务: {message_item.id}")
    # 模拟一些工作
    result = sum(i * i for i in range(1000))
    message_item.result = {
        "status": "completed",
        "result": result,
        "task_id": message_item.id,
    }
    return message_item


@task(meta={"task_name": "async_pyside6_task"})
async def async_pyside6_task(message_item: MessageItem):
    """异步任务测试"""
    import asyncio

    print(f"处理异步任务: {message_item.id}")
    await asyncio.sleep(0.1)  # 模拟异步操作
    message_item.result = {"status": "async_completed", "task_id": message_item.id}
    return message_item


def task_callback(message_item: MessageItem):
    """任务完成回调"""
    print(f"任务完成回调: {message_item.id}, 结果: {message_item.result}")


def test_pyside6_scheduler():
    """测试独立的 PySide6 调度器"""

    # 创建独立的 PySide6 调度器
    scheduler = QueueScheduler(
        scheduler_type="qt",  # 指定使用 PySide6 调度器
    )

    print("启动 qt 调度器...")
    scheduler.start()

    try:
        # 发送同步任务
        for i in range(5):
            message = MessageItem(
                content={"task_index": i, "type": "sync"},
                destination="pyside6_example_task",
            )
            scheduler.send_message(message, task_callback)
            print(f"发送同步消息: {message.id}")

        # 发送异步任务
        for i in range(5):
            message = MessageItem(
                content={"task_index": i, "type": "async"},
                destination="async_pyside6_task",
            )
            scheduler.send_message(message, task_callback)
            print(f"发送异步消息: {message.id}")

        # 等待任务处理
        print("等待任务处理...")
        for i in range(10):
            queue_info = scheduler.scheduler.get_queue_info()
            print(f"队列状态: {queue_info}")
            time.sleep(1)

            if queue_info.get("queue_length", 0) == 0:
                break

    finally:
        print("停止 PySide6 调度器...")
        scheduler.stop()
        print("测试完成")


if __name__ == "__main__":
    test_pyside6_scheduler()
