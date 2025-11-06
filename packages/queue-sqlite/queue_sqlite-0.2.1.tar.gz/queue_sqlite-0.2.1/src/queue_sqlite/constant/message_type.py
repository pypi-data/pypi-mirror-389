#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   message_type.py
@Time    :   2025-09-27 16:57:58
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   消息类型枚举类
"""

from enum import Enum


class MessageType(Enum):
    TASK = "task"  # 任务
    LISTEN = "listen"  # 监听
