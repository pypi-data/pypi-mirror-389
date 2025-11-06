#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   message_priority.py
@Time    :   2025-09-27 16:56:58
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   消息优先级枚举类
"""


from enum import IntEnum


class MessagePriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3
