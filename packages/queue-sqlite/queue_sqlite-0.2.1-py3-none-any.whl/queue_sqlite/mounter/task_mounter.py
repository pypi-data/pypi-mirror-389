#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   task_mounter.py
@Time    :   2025-09-27 17:01:38
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   任务挂载器
"""


from typing import Callable, List
from dataclasses import dataclass, field


@dataclass
class TaskMeta:
    name: str = field(default="", metadata={"help": "任务名称"})
    description: str = field(default="", metadata={"help": "任务描述"})
    max_retries: int = field(default=3, metadata={"help": "任务最大重试次数"})
    delay: float = field(default=1, metadata={"help": "任务延迟执行时间"})


class TaskMounter:
    @classmethod
    def mount_task(cls, function: Callable):
        setattr(cls, function.__name__, function)

    @staticmethod
    def task(meta: dict = {}):
        """带参数的装饰器"""

        def decorator(function: Callable):
            # 使用自定义名称或函数原名
            name = meta.get("name", function.__name__)
            description = meta.get("description", "")
            max_retries = meta.get("max_retries", 3)
            delay = meta.get("delay", 1)
            task_meta = TaskMeta(
                name=name, description=description, max_retries=max_retries, delay=delay
            )
            function.meta = task_meta  # type: ignore
            setattr(TaskMounter, function.__name__, function)
            return function

        return decorator

    @classmethod
    def get_task_function(cls, name: str):
        return getattr(cls, name, None)

    @classmethod
    def get_task_meta(cls, task_name: str):
        task_function = cls.get_task_function(task_name)
        if task_function:
            return getattr(task_function, "meta", {})

    @classmethod
    def get_task_list(cls) -> List[str]:
        """获取所有挂载的任务函数名称列表"""
        task_list = []

        # 遍历类属性字典
        for attr_name, attr_value in vars(cls).items():
            # 过滤条件：
            # 1. 必须是可调用对象（函数）
            # 2. 不是类自带的特殊方法（非双下划线开头）
            # 3. 不是类方法本身（如 mount_task, get_task_list 等）
            if (
                callable(attr_value)
                and not attr_name.startswith("__")
                and attr_name
                not in ["mount_task", "task", "get_task_function", "get_task_list"]
            ):
                task_list.append(attr_name)

        return task_list


# task 装饰器
def task(meta: dict = {}):
    return TaskMounter.task(meta)
