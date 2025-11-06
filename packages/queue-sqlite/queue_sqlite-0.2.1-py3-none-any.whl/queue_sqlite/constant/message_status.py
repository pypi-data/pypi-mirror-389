#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   message_status.py
@Time    :   2025-09-27 16:57:25
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   消息状态枚举类
"""


from enum import IntEnum


class MessageStatus(IntEnum):
    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3
    RETRYING = 4
