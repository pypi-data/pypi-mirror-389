#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   listen_mounter.py
@Time    :   2025-09-27 17:01:23
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   监听装饰器
"""


from typing import Callable, List


class ListenMounter:
    @classmethod
    def mount_Listener(cls, function: Callable):
        setattr(cls, function.__name__, function)

    @staticmethod
    def listener():
        """带参数的装饰器"""

        def decorator(function: Callable):
            # 使用自定义名称或函数原名
            setattr(ListenMounter, function.__name__, function)
            return function

        return decorator

    @classmethod
    def get_Listener_function(cls, name: str):
        return getattr(cls, name, None)

    @classmethod
    def get_Listener_list(cls) -> List[str]:
        """获取所有挂载的监听函数名称列表"""
        listener_list = []

        # 遍历类属性字典
        for attr_name, attr_value in vars(cls).items():
            # 过滤条件：
            # 1. 必须是可调用对象（函数）
            # 2. 不是类自带的特殊方法（非双下划线开头）
            # 3. 不是类方法本身（如 mount_Listener, listener 等）
            if (
                callable(attr_value)
                and not attr_name.startswith("__")
                and attr_name
                not in [
                    "mount_Listener",
                    "listener",
                    "get_Listener_function",
                    "get_Listener_list",
                ]
            ):
                listener_list.append(attr_name)

        return listener_list


def listener():
    return ListenMounter.listener()
