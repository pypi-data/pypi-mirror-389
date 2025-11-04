"""
消息通知信号模块
提供自定义消息通知机制，允许其他APP订阅和处理消息
"""

from django.dispatch import Signal
from django.dispatch import receiver
from django.db.models.signals import post_save
import logging

logger = logging.getLogger(__name__)

# 定义自定义信号
# data_fetched: 数据获取完成信号
# message_received: 消息接收信号
data_fetched = Signal()
message_received = Signal()


class NotificationManager:
    """
    消息通知管理器
    负责管理消息通知的发送和接收
    """

    @staticmethod
    def send_data_fetched_notification(sender, data_type, data, **kwargs):
        """
        发送数据获取完成通知
        
        参数:
            sender: 发送者
            data_type: 数据类型
            data: 获取的数据
            **kwargs: 其他参数
        """
        try:
            logger.info(f"发送数据获取完成通知: 类型={data_type}, 数据量={len(data) if hasattr(data, '__len__') else 'N/A'}")
            data_fetched.send(
                sender=sender,
                data_type=data_type,
                data=data,
                **kwargs
            )
            logger.info("数据获取完成通知发送成功")
        except Exception as e:
            logger.error(f"发送数据获取完成通知失败: {e}")

    @staticmethod
    def send_message_received_notification(sender, message_type, message, **kwargs):
        """
        发送消息接收通知
        
        参数:
            sender: 发送者
            message_type: 消息类型
            message: 消息内容
            **kwargs: 其他参数
        """
        try:
            logger.info(f"发送消息接收通知: 类型={message_type}, 消息={message}")
            message_received.send(
                sender=sender,
                message_type=message_type,
                message=message,
                **kwargs
            )
            logger.info("消息接收通知发送成功")
        except Exception as e:
            logger.error(f"发送消息接收通知失败: {e}")


# 示例接收器 - 其他APP可以注册自己的接收器
@receiver(data_fetched)
def handle_data_fetched(sender, **kwargs):
    """
    处理数据获取完成信号
    其他APP可以注册自己的处理函数
    
    参数:
        sender: 发送者
        **kwargs: 信号参数
    """
    data_type = kwargs.get('data_type')
    data = kwargs.get('data')
    logger.info(f"接收到数据获取信号: 类型={data_type}")
    # 这里可以添加自定义处理逻辑


@receiver(message_received)
def handle_message_received(sender, **kwargs):
    """
    处理消息接收信号
    其他APP可以注册自己的处理函数
    
    参数:
        sender: 发送者
        **kwargs: 信号参数
    """
    message_type = kwargs.get('message_type')
    message = kwargs.get('message')
    logger.info(f"接收到消息信号: 类型={message_type}, 消息={message}")
    # 这里可以添加自定义处理逻辑