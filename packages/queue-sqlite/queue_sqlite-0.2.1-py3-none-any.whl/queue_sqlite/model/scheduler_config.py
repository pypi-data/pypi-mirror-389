#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   scheduler_config.py
@Time    :   2025-10-28 10:21:21
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   队列调度器配置
"""

from dataclasses import dataclass, field
from typing import Dict, Any
import logging


@dataclass
class SchedulerConfig:
    receive_thread_num: int = field(
        default=1,
        metadata={"help": "接收消息的线程数"},
    )
    task_thread_num: int = field(
        default=4,
        metadata={"help": "任务执行线程数"},
    )
    shard_num: int = field(
        default=4,
        metadata={"help": "分片数"},
    )
    queue_name: str = field(
        default="default",
        metadata={"help": "队列名称"},
    )
    meta: Dict[str, Any] = field(
        default_factory=dict,
        metadata={"help": "队列元数据"},
    )

    @classmethod
    def get_field_descriptions(cls) -> Dict[str, str]:
        """获取所有字段的描述信息

        Returns:
            Dict[str, str]: 字段名到描述信息的映射
        """
        from dataclasses import fields

        descriptions = {}
        for field_info in fields(cls):
            if "help" in field_info.metadata:
                descriptions[field_info.name] = field_info.metadata["help"]
            else:
                descriptions[field_info.name] = "无描述信息"

        return descriptions

    @classmethod
    def print_field_info(cls):
        """打印所有字段的信息，包括类型、默认值和描述"""
        from dataclasses import fields

        logging.info(f"=== {cls.__name__} 字段信息 ===")
        for field_info in fields(cls):
            logging.info(
                f"{field_info.name}: {field_info.type} (默认值: {field_info.default})"
            )
            logging.info(f"    描述: {field_info.metadata.get('help', '无描述信息')}")
            logging.info("-" * 50)
