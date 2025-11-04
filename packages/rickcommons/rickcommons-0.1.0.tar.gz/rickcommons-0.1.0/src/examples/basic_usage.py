#!/usr/bin/env python3
"""
Qyscripts 基本使用示例

这个示例展示了如何使用Qyscripts库进行Redis队列的基本操作，
包括发送消息和消费消息。
"""

import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rickcommons.redis_queue import (
    RedisQueueConfig, 
    RedisQueueManager, 
    RedisQueueProducer, 
    RedisStreamsConsumer
)


def basic_producer_consumer_example():
    """基本生产者和消费者示例"""
    print("=== 基本生产者和消费者示例 ===")
    
    # 配置Redis连接
    config = RedisQueueConfig(
        host='localhost',
        port=6379,
        password=None,
        db=0
    )
    
    # 创建管理器
    manager = RedisQueueManager(config)
    
    try:
        # 创建生产者
        producer = RedisQueueProducer(manager)
        
        # 创建消费者
        consumer = RedisStreamsConsumer(
            manager=manager,
            stream_name="example_stream",
            consumer_group="example_group",
            consumer_name="example_consumer"
        )
        
        # 发送测试消息
        print("发送测试消息...")
        messages = [
            "第一条测试消息",
            "第二条测试消息", 
            "第三条测试消息"
        ]
        
        for i, message in enumerate(messages, 1):
            success = producer.send_message("example_stream", message)
            print(f"消息 {i} 发送{'成功' if success else '失败'}: {message}")
        
        # 消费消息
        print("\n开始消费消息...")
        for i in range(3):
            message = consumer.consume_message(timeout=3000)  # 3秒超时
            if message:
                print(f"收到消息: {message['data']}")
                # 确认消息
                consumer.ack_message(message['id'])
            else:
                print("没有收到消息")
                
    finally:
        # 关闭连接
        manager.close()


def batch_operations_example():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")
    
    config = RedisQueueConfig(
        host='localhost',
        port=6379,
        password=None,
        db=0
    )
    
    manager = RedisQueueManager(config)
    
    try:
        producer = RedisQueueProducer(manager)
        consumer = RedisStreamsConsumer(
            manager=manager,
            stream_name="batch_stream",
            consumer_group="batch_group",
            consumer_name="batch_consumer"
        )
        
        # 批量发送消息
        print("批量发送消息...")
        batch_messages = [f"批量消息_{i}" for i in range(1, 6)]
        success = producer.send_batch_messages("batch_stream", batch_messages)
        print(f"批量发送{'成功' if success else '失败'}: {len(batch_messages)} 条消息")
        
        # 批量消费消息
        print("批量消费消息...")
        messages = consumer.consume_batch_messages(count=5, timeout=3000)
        print(f"收到 {len(messages)} 条消息:")
        for msg in messages:
            print(f"  - {msg['data']}")
            consumer.ack_message(msg['id'])
            
    finally:
        manager.close()


def continuous_consumer_example():
    """持续消费者示例"""
    print("\n=== 持续消费者示例 ===")
    
    config = RedisQueueConfig(
        host='localhost',
        port=6379,
        password=None,
        db=0
    )
    
    manager = RedisQueueManager(config)
    
    try:
        producer = RedisQueueProducer(manager)
        consumer = RedisStreamsConsumer(
            manager=manager,
            stream_name="continuous_stream",
            consumer_group="continuous_group",
            consumer_name="continuous_consumer"
        )
        
        # 发送一些初始消息
        print("发送初始消息...")
        for i in range(3):
            producer.send_message("continuous_stream", f"持续消息_{i+1}")
        
        # 定义消息处理函数
        def message_handler(message):
            print(f"处理消息: {message['data']}")
            # 确认消息
            consumer.ack_message(message['id'])
        
        # 启动持续消费
        print("启动持续消费 (运行5秒)...")
        consumer.start_consuming(
            message_handler=message_handler,
            batch_size=2,
            timeout=1000
        )
        
        # 在消费过程中发送更多消息
        time.sleep(2)
        print("发送额外消息...")
        producer.send_message("continuous_stream", "额外消息_1")
        producer.send_message("continuous_stream", "额外消息_2")
        
        # 等待一段时间
        time.sleep(3)
        
        # 停止消费
        consumer.stop_consuming()
        print("持续消费已停止")
        
    finally:
        manager.close()


if __name__ == "__main__":
    print("Qyscripts 使用示例")
    print("=" * 50)
    
    # 检查Redis是否可用
    try:
        config = RedisQueueConfig(host='localhost', port=6379)
        manager = RedisQueueManager(config)
        manager.close()
        print("✓ Redis连接正常")
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        print("请确保Redis服务器正在运行")
        sys.exit(1)
    
    # 运行示例
    basic_producer_consumer_example()
    batch_operations_example()
    continuous_consumer_example()
    
    print("\n所有示例执行完成!")