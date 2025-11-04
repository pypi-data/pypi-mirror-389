"""
Qyscripts - 自用的一些工具函数

包含Redis消息队列、Django注解等实用工具
"""

from .redis_queue import RedisQueue, RedisQueueConfig, RedisQueueProducer, RedisStreamsConsumer

__version__ = "0.1.0"
__all__ = [
    "RedisQueue", 
    "RedisQueueConfig", 
    "RedisQueueProducer", 
    "RedisStreamsConsumer"
]

def main() -> None:
    """命令行入口点"""
    print("Qyscripts - 自用工具函数集合")
    print(f"版本: {__version__}")
    print("可用模块:")
    print("- redis_queue: Redis消息队列实现")
    print("- django-ann: Django注解工具")
