#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   async_task_cycle.py
@Time    :   2025-09-27 16:59:17
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   异步任务周期类
"""


from ..model import MessageItem
from ..constant import MessageStatus
from ..mounter.task_mounter import TaskMeta
import json
import asyncio
import functools


def retry_async(max_retries=3):
    """
    异步重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            # 使用message_item中的retry_count作为最大重试次数
            task_meta: TaskMeta = self.callback.meta
            retries = task_meta.max_retries
            # retries = getattr(self.message_item, "retry_count", max_retries)
            delay_time = task_meta.delay
            # 至少尝试一次（retries+1），最多尝试max_retries+1次
            actual_retries = min(retries, max_retries) if max_retries > 0 else retries

            for attempt in range(actual_retries + 1):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < actual_retries:
                        await asyncio.sleep(delay_time)
                    else:
                        break
            if last_exception:
                raise last_exception
            else:
                raise Exception("Unknown error occurred during async task execution")

        return wrapper

    return decorator


class AsyncTaskCycle:
    def __init__(self, message_item: MessageItem, callback):
        self.message_item = message_item
        self.callback = callback
        self.task_result = None
        self.task_status = None
        self.task_error = None

    @retry_async(max_retries=3)
    async def run(self):
        try:
            task_result = await self.callback(self.message_item)  # type: ignore
        except Exception as e:
            self.task_result = None
            self.task_status = MessageStatus.FAILED
            self.task_error = str(e)
        else:
            self.task_result = task_result
            self.task_status = MessageStatus.COMPLETED
            self.task_error = None

    def get_task_result(self):
        """获取任务结果 - 优化版本"""
        if self.task_result is None:
            return json.dumps({"result": None})

        # 如果已经是字符串，尝试解析
        if isinstance(self.task_result, str):
            try:
                # 如果是 JSON 字符串，直接返回
                json.loads(self.task_result)
                return self.task_result
            except:
                # 如果不是 JSON，包装成 JSON
                return json.dumps({"result": self.task_result})

        # 如果是 MessageItem 对象，提取其中的 result 字段
        if isinstance(self.task_result, MessageItem):
            result_data = self.task_result.result
            if isinstance(result_data, (dict, list)):
                return json.dumps(result_data)
            else:
                return json.dumps({"result": result_data})

        # 其他情况正常序列化
        try:
            return json.dumps(self.task_result)
        except:
            return json.dumps({"result": str(self.task_result)})

    def get_task_status(self):
        return self.task_status

    def get_task_error(self):
        return self.task_error

    def get_task_message_item(self):
        return self.message_item

    def get_task_callback(self):
        return self.callback
