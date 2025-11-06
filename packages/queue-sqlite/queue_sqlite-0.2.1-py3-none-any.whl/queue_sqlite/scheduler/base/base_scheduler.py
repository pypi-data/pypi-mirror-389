from abc import ABC, abstractmethod
from typing import Callable
from ...model import MessageItem, SchedulerConfig


class BaseScheduler(ABC):
    """调度器抽象类"""

    def __init__(self, config: SchedulerConfig = SchedulerConfig()):
        pass

    @abstractmethod
    def send_message(self, message: MessageItem, callback: Callable):
        """发送消息到队列

        Args:
            message (MessageItem): 消息对象
            callback (Callable): 发送完成后的回调函数
        """
        pass

    @abstractmethod
    def start(self):
        """启动调度器"""
        pass

    @abstractmethod
    def stop(self):
        """停止调度器"""
        pass

    @abstractmethod
    def update_listen_data(self, key, value):
        """更新监听数据"""
        pass

    @abstractmethod
    def get_listen_datas(self) -> list:
        """获取监听数据"""
        pass

    @abstractmethod
    def get_listen_data(self, key):
        """获取单个监听数据"""
        pass
