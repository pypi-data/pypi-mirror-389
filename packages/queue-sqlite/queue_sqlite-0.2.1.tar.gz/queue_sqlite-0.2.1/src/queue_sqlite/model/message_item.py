#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   message_item.py
@Time    :   2025-09-27 17:00:27
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   消息数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from ..constant import MessageStatus, MessagePriority, MessageType
import json
from enum import Enum
import uuid
import logging


@dataclass
class MessageItem:
    # 必需字段
    content: dict = field(  # type ignore
        metadata={"description": "消息内容，包含具体的任务数据或信息"}
    )

    # 可选字段
    status: MessageStatus = field(
        default=MessageStatus.PENDING,
        metadata={
            "description": "消息状态：PENDING(待处理)、PROCESSING(处理中)、COMPLETED(已完成)、FAILED(失败)"
        },
    )
    type: MessageType = field(
        default=MessageType.TASK,
        metadata={
            "description": "消息类型：TASK(任务)、NOTIFICATION(通知)、RESPONSE(响应)"
        },
    )
    createtime: datetime = field(
        default_factory=datetime.now,  # type: ignore
        metadata={"description": "消息创建时间"},
    )
    updatetime: datetime = field(
        default_factory=datetime.now,  # type: ignore
        metadata={"description": "消息最后更新时间"},
    )
    result: dict = field(
        default_factory=dict,
        metadata={"description": "消息处理结果，存储任务执行后的输出数据"},
    )
    id: str = field(
        default_factory=lambda: str(uuid.uuid4()),
        metadata={"description": "消息唯一标识符"},
    )
    priority: MessagePriority = field(
        default=MessagePriority.NORMAL,
        metadata={
            "description": "消息优先级：LOW(低)、NORMAL(普通)、HIGH(高)、URGENT(紧急)"
        },
    )
    source: str = field(
        default="client", metadata={"description": "消息来源，标识发送方"}
    )
    destination: str = field(
        default="client", metadata={"description": "消息目标，标识接收方(即task函数名)"}
    )
    retry_count: int = field(
        default=0, metadata={"description": "重试次数，记录消息处理失败后的重试次数"}
    )
    expire_time: Optional[datetime] = field(
        default=None, metadata={"description": "消息过期时间，超过此时间消息将不再处理"}
    )
    tags: Optional[str] = field(
        default=None, metadata={"description": "消息标签，用于分类和筛选"}
    )
    metadata: dict = field(
        default_factory=dict,
        metadata={"description": "额外元数据，存储自定义的扩展信息"},
    )

    @classmethod
    def from_dict(cls, data: dict) -> "MessageItem":
        """从字典创建消息对象"""
        # 处理日期时间字段
        datetime_fields = ["createtime", "updatetime", "expire_time"]
        for field in datetime_fields:
            if field in data:
                if data[field] == "null":
                    data[field] = None
                    continue
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
                elif isinstance(data[field], datetime):
                    continue
                elif data[field] is None:
                    data[field] = None
                else:
                    raise ValueError(
                        f"请使用 'str' 或 'datetime' 类型设置 {field} 字段"
                    )

        if "content" in data:
            if data["content"] == "null":
                data["content"] = {}
            elif isinstance(data["content"], str):
                data["content"] = json.loads(data["content"])

        if "metadata" in data:
            if data["metadata"] == "null":
                data["metadata"] = {}
            elif isinstance(data["metadata"], str):
                data["metadata"] = json.loads(data["metadata"])

        if "result" in data:
            if data["result"] == "null":
                data["result"] = {}
            elif isinstance(data["result"], str):
                data["result"] = json.loads(data["result"])

        if "tags" in data:
            if data["tags"] == "null":
                data["tags"] = None

        # 处理枚举字段
        if "type" in data:
            if isinstance(data["type"], str):
                # 根据字符串值查找对应的枚举成员
                for member in MessageType:
                    if member.value == data["type"]:
                        data["type"] = member
                        break
                else:
                    raise ValueError(f"Invalid message type: {data['type']}")
            elif isinstance(data["type"], MessageType):
                pass  # 已经是枚举类型
            else:
                raise ValueError(f"请使用 'str' 或 'MessageType' 类型设置 type 字段")

        if "status" in data:
            if isinstance(data["status"], str):
                # 尝试将字符串转换为整数，如果失败则使用字符串作为枚举名称
                try:
                    data["status"] = MessageStatus(
                        int(data["status"])
                    )  # 尝试作为枚举值
                except ValueError:
                    data["status"] = MessageStatus(data["status"])  # 使用枚举名称
            elif isinstance(data["status"], int):
                data["status"] = MessageStatus(data["status"])  # 使用枚举值
            elif isinstance(data["status"], MessageStatus):
                pass  # 已经是枚举类型
            else:
                raise ValueError(f"Invalid message status: {data['status']}")

        if "priority" in data:
            if isinstance(data["priority"], str):
                # 尝试将字符串转换为整数，如果失败则使用字符串作为枚举名称
                try:
                    data["priority"] = MessagePriority(
                        int(data["priority"])
                    )  # 尝试作为枚举值
                except ValueError:
                    # 如果转换失败，尝试通过枚举名称查找
                    for member in MessagePriority:
                        if member.name == data["priority"]:
                            data["priority"] = member
                            break
                    else:
                        raise ValueError(
                            f"Invalid message priority: {data['priority']}"
                        )
            elif isinstance(data["priority"], int):
                data["priority"] = MessagePriority(data["priority"])  # 使用枚举值
            elif isinstance(data["priority"], MessagePriority):
                pass  # 已经是枚举类型
            else:
                raise ValueError("请使用 'int' 或 'str' 类型设置 priority 字段")

        if "retry_count" in data:
            if isinstance(data["retry_count"], str):
                if data["retry_count"].isdigit():
                    data["retry_count"] = int(data["retry_count"])
                else:
                    raise ValueError("请使用 'int' 类型设置 retry_count 字段")
            elif isinstance(data["retry_count"], int):
                pass  # 已经是整数类型

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            Dict[str, Any]: 消息数据字典
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "content": self.content,
            "createtime": self.createtime.isoformat(),
            "updatetime": self.updatetime.isoformat(),
            "priority": self.priority.value,
            "source": self.source,
            "retry_count": self.retry_count,
            "expire_time": self.expire_time.isoformat() if self.expire_time else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "result": self.result,
            "destination": self.destination,
        }

    def to_dict_by_core(self) -> Dict[str, Any]:
        """转换为核心库需要的字典格式"""
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "content": json.dumps(self.content),
            "createtime": self.createtime.isoformat(),
            "updatetime": self.updatetime.isoformat(),
            "priority": self.priority.value,
            "source": self.source,
            "retry_count": self.retry_count,
            "expire_time": self.expire_time.isoformat() if self.expire_time else "null",
            "tags": self.tags if self.tags else "null",
            "metadata": json.dumps(self.metadata),
            "result": json.dumps(self.result),
            "destination": self.destination,
        }

    def to_json(self) -> str:
        """转换为json字符串"""
        # 将枚举类型转换为字符串
        data = self.to_dict()
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.timestamp()
        return json.dumps(data)

    def is_expired(self) -> bool:
        """检查消息是否过期

        Returns:
            bool: 是否过期
        """
        if self.expire_time is None:
            return False
        return datetime.now() > self.expire_time

    def can_retry(self) -> bool:
        """检查消息是否可以重试

        Returns:
            bool: 是否可以重试
        """
        return self.retry_count < 3

    @classmethod
    def get_field_descriptions(cls) -> Dict[str, str]:
        """获取所有字段的描述信息

        Returns:
            Dict[str, str]: 字段名到描述信息的映射
        """
        from dataclasses import fields

        descriptions = {}
        for field_info in fields(cls):
            if "description" in field_info.metadata:
                descriptions[field_info.name] = field_info.metadata["description"]
            else:
                descriptions[field_info.name] = "无描述信息"

        return descriptions

    @classmethod
    def print_field_info(cls):
        """打印所有字段的信息，包括类型、默认值和描述"""
        from dataclasses import fields

        logging.info(f"=== {cls.__name__} 字段信息 ===")
        for field_info in fields(cls):
            logging.info(f"字段名: {field_info.name}")
            logging.info(f"类型: {field_info.type}")
            logging.info(f"默认值: {field_info.default}")
            if field_info.default_factory is not None:
                logging.info(f"默认工厂: {field_info.default_factory}")
            if "description" in field_info.metadata:
                logging.info(f"描述: {field_info.metadata['description']}")
            logging.info("-" * 50)
