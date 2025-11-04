# -*- coding: utf-8 -*-
"""
文件名: redis_queue.py
作者: li2810081
日期: 2025-11-03
描述: 简易的redis消息通知队列,持久化数据,支持多生产者多消费者,简易的kafka实现
"""

import sys
import os
import redis
import json
import time
import threading
from typing import Any, Dict, Optional, Callable, List


class RedisQueueConfig:
    """
    Redis队列配置类
    """
    
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 6379, 
                 db: int = 0,
                 password: Optional[str] = None,
                 max_connections: int = 10,
                 socket_timeout: int = 5,
                 retry_attempts: int = 3,
                 retry_delay: float = 1.0):
        """
        初始化Redis队列配置
        
        Args:
            host: Redis服务器地址
            port: Redis服务器端口
            db: Redis数据库编号
            password: Redis密码
            max_connections: 最大连接数
            socket_timeout: 套接字超时时间(秒)
            retry_attempts: 重试次数
            retry_delay: 重试延迟时间(秒)
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay


class RedisQueueManager:
    """
    Redis队列管理器
    """
    
    def __init__(self, config: RedisQueueConfig):
        """
        初始化Redis队列管理器
        
        Args:
            config: Redis队列配置
        """
        self.config = config
        self._redis_client = None
        self._lock = threading.Lock()
    
    def get_redis_client(self) -> redis.Redis:
        """
        获取Redis客户端连接
        
        Returns:
            redis.Redis: Redis客户端实例
            
        Raises:
            redis.ConnectionError: 连接Redis失败
        """
        if self._redis_client is None:
            with self._lock:
                if self._redis_client is None:
                    connection_pool = redis.ConnectionPool(
                        host=self.config.host,
                        port=self.config.port,
                        db=self.config.db,
                        password=self.config.password,
                        max_connections=self.config.max_connections,
                        socket_timeout=self.config.socket_timeout,
                        decode_responses=True
                    )
                    self._redis_client = redis.Redis(connection_pool=connection_pool)
        
        # 测试连接
        try:
            self._redis_client.ping()
        except redis.ConnectionError:
            self._redis_client = None
            raise redis.ConnectionError("无法连接到Redis服务器")
        
        return self._redis_client
    
    def close(self):
        """
        关闭Redis连接
        """
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None


class RedisQueueProducer:
    """
    Redis队列生产者
    """
    
    def __init__(self, queue_manager: RedisQueueManager, topic: str):
        """
        初始化Redis队列生产者
        
        Args:
            queue_manager: Redis队列管理器
            topic: 消息主题
        """
        self.queue_manager = queue_manager
        self.topic = topic
    
    def send_message(self, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        发送消息到队列
        
        Args:
            message: 消息内容
            key: 消息键，用于分区（可选）
            
        Returns:
            bool: 发送是否成功
            
        Raises:
            redis.RedisError: Redis操作失败
        """
        redis_client = self.queue_manager.get_redis_client()
        
        # 构建消息体
        message_data = {
            'id': str(int(time.time() * 1000)),  # 时间戳作为消息ID
            'timestamp': time.time(),
            'topic': self.topic,
            'key': key,
            'data': message
        }
        
        # 序列化消息
        message_json = json.dumps(message_data, ensure_ascii=False)
        
        # 重试机制
        for attempt in range(self.queue_manager.config.retry_attempts):
            try:
                # 使用列表作为队列，支持多消费者
                result = redis_client.lpush(f"queue:{self.topic}", message_json)
                
                # 同时保存到持久化存储
                if key:
                    redis_client.hset(f"messages:{self.topic}", key, message_json)
                
                return True
                
            except redis.RedisError as e:
                if attempt < self.queue_manager.config.retry_attempts - 1:
                    time.sleep(self.queue_manager.config.retry_delay)
                    continue
                else:
                    raise redis.RedisError(f"发送消息失败: {str(e)}")
        
        return False
    
    def send_batch_messages(self, messages: list, keys: Optional[list] = None) -> bool:
        """
        批量发送消息
        
        Args:
            messages: 消息列表
            keys: 消息键列表（可选）
            
        Returns:
            bool: 批量发送是否成功
        """
        redis_client = self.queue_manager.get_redis_client()
        
        pipeline = redis_client.pipeline()
        
        for i, message in enumerate(messages):
            key = keys[i] if keys and i < len(keys) else None
            
            message_data = {
                'id': str(int(time.time() * 1000) + i),  # 确保ID唯一
                'timestamp': time.time(),
                'topic': self.topic,
                'key': key,
                'data': message
            }
            
            message_json = json.dumps(message_data, ensure_ascii=False)
            
            pipeline.lpush(f"queue:{self.topic}", message_json)
            
            if key:
                pipeline.hset(f"messages:{self.topic}", key, message_json)
        
        try:
            pipeline.execute()
            return True
        except redis.RedisError:
            return False


class RedisStreamsConsumer:
    """
    Redis Streams消息队列消费者类
    支持消费者组、消息确认和负载均衡
    """
    
    def __init__(self, queue_manager: RedisQueueManager, topic: str, consumer_group: str = "default", consumer_id: str = None):
        """
        初始化消费者
        
        Args:
            queue_manager: Redis队列管理器
            topic: 消息主题
            consumer_group: 消费者组名称
            consumer_id: 消费者ID，如果为None则自动生成
        """
        self.queue_manager = queue_manager
        self.topic = topic
        self.consumer_group = consumer_group
        self.consumer_id = consumer_id or f"consumer-{int(time.time() * 1000)}"
        self._running = False
        self._consumer_thread = None
        
        # 初始化消费者组
        self._init_consumer_group()
    
    def _init_consumer_group(self):
        """
        初始化消费者组
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            # 创建消费者组，如果不存在则创建
            redis_client.xgroup_create(
                name=self.topic,
                groupname=self.consumer_group,
                id="0",
                mkstream=True
            )
        except redis.ResponseError as e:
            # 消费者组已存在，忽略错误
            if "BUSYGROUP" not in str(e):
                raise
    
    def consume_message(self, timeout: int = 1000) -> Optional[Dict[str, Any]]:
        """
        消费单条消息
        
        Args:
            timeout: 阻塞超时时间（毫秒）
            
        Returns:
            Optional[Dict[str, Any]]: 消息内容，如果超时返回None
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            # 使用消费者组读取消息
            messages = redis_client.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_id,
                streams={self.topic: ">"},
                count=1,
                block=timeout
            )
            
            if messages:
                stream_name, message_list = messages[0]
                if message_list:
                    message_id, message_data = message_list[0]
                    return {
                        "id": message_id,
                        "data": message_data,
                        "topic": self.topic,
                        "consumer_group": self.consumer_group
                    }
        except redis.RedisError as e:
            print(f"消费消息时发生错误: {e}")
        
        return None
    
    def ack_message(self, message_id: str) -> bool:
        """
        确认消息已处理
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 确认是否成功
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            redis_client.xack(self.topic, self.consumer_group, message_id)
            return True
        except redis.RedisError:
            return False
    
    def start_consuming(self, message_handler: Callable[[Dict[str, Any]], None], batch_size: int = 1):
        """
        开始持续消费消息
        
        Args:
            message_handler: 消息处理回调函数
            batch_size: 批量处理大小
        """
        self._running = True
        
        def consume_loop():
            while self._running:
                try:
                    messages = self.consume_batch_messages(batch_size, timeout=1000)
                    if messages:
                        for message in messages:
                            try:
                                message_handler(message)
                                # 确认消息已处理
                                self.ack_message(message["id"])
                            except Exception as e:
                                print(f"处理消息时发生错误: {e}")
                                # 处理失败的消息不会确认，稍后会重新投递
                except Exception as e:
                    print(f"消费循环发生错误: {e}")
                    time.sleep(1)
        
        self._consumer_thread = threading.Thread(target=consume_loop)
        self._consumer_thread.daemon = True
        self._consumer_thread.start()
    
    def consume_batch_messages(self, count: int = 10, timeout: int = 1000) -> List[Dict[str, Any]]:
        """
        批量消费消息
        
        Args:
            count: 消息数量
            timeout: 阻塞超时时间（毫秒）
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            messages = redis_client.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_id,
                streams={self.topic: ">"},
                count=count,
                block=timeout
            )
            
            result = []
            if messages:
                stream_name, message_list = messages[0]
                for message_id, message_data in message_list:
                    result.append({
                        "id": message_id,
                        "data": message_data,
                        "topic": self.topic,
                        "consumer_group": self.consumer_group
                    })
            return result
        except redis.RedisError as e:
            print(f"批量消费消息时发生错误: {e}")
            return []
    
    def stop_consuming(self):
        """
        停止消费消息
        """
        self._running = False
        if hasattr(self, '_consumer_thread'):
            self._consumer_thread.join(timeout=5)
    
    def get_pending_messages(self) -> List[Dict[str, Any]]:
        """
        获取待处理消息列表
        
        Returns:
            List[Dict[str, Any]]: 待处理消息列表
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            pending_messages = redis_client.xpending_range(
                name=self.topic,
                groupname=self.consumer_group,
                min="-",
                max="+",
                count=100
            )
            
            result = []
            for pending in pending_messages:
                result.append({
                    "message_id": pending["message_id"],
                    "consumer": pending["consumer"],
                    "delivered_ms": pending["delivered"],
                    "delivery_count": pending["delivery_count"]
                })
            return result
        except redis.RedisError as e:
            print(f"获取待处理消息时发生错误: {e}")
            return []
    
    def claim_pending_messages(self, min_idle_time: int = 60000) -> List[Dict[str, Any]]:
        """
        认领其他消费者超时的待处理消息
        
        Args:
            min_idle_time: 最小空闲时间（毫秒）
            
        Returns:
            List[Dict[str, Any]]: 认领的消息列表
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            # 获取所有待处理消息
            pending_messages = self.get_pending_messages()
            if not pending_messages:
                return []
            
            # 筛选需要认领的消息
            messages_to_claim = []
            for pending in pending_messages:
                if pending["delivered_ms"] >= min_idle_time:
                    messages_to_claim.append(pending["message_id"])
            
            if not messages_to_claim:
                return []
            
            # 认领消息
            claimed_messages = redis_client.xclaim(
                name=self.topic,
                groupname=self.consumer_group,
                consumername=self.consumer_id,
                min_idle_time=min_idle_time,
                message_ids=messages_to_claim
            )
            
            result = []
            for message_id, message_data in claimed_messages:
                result.append({
                    "id": message_id,
                    "data": message_data,
                    "topic": self.topic,
                    "consumer_group": self.consumer_group,
                    "claimed": True
                })
            return result
        except redis.RedisError as e:
            print(f"认领待处理消息时发生错误: {e}")
            return []


class RedisQueue:
    """
    简易Redis消息队列主类
    """
    
    def __init__(self, config: RedisQueueConfig):
        """
        初始化Redis消息队列
        
        Args:
            config: Redis队列配置
        """
        self.config = config
        self.queue_manager = RedisQueueManager(config)
    
    def create_producer(self, topic: str) -> RedisQueueProducer:
        """
        创建生产者
        
        Args:
            topic: 消息主题
            
        Returns:
            RedisQueueProducer: 生产者实例
        """
        return RedisQueueProducer(self.queue_manager, topic)
    
    def create_consumer(self, topic: str, consumer_group: str = "default", consumer_id: str = None) -> RedisStreamsConsumer:
        """
        创建消费者
        
        Args:
            topic: 消息主题
            consumer_group: 消费者组名称
            consumer_id: 消费者ID
            
        Returns:
            RedisStreamsConsumer: 消费者实例
        """
        return RedisStreamsConsumer(self.queue_manager, topic, consumer_group, consumer_id)
    
    def close(self):
        """
        关闭队列连接
        """
        self.queue_manager.close()


# 使用示例
if __name__ == "__main__":
    # 创建配置
    config = RedisQueueConfig(
        host="127.0.0.1",
        port=6379,
        db=0,
        password="redis_hwcj2e",
        retry_attempts=3,
        retry_delay=1
    )
    
    # 创建队列实例
    queue = RedisQueue(config)
    
    try:
        # 创建生产者
        producer = queue.create_producer("test_topic")
        
        # 发送单条消息
        message = {"type": "test", "content": "Hello Redis Queue"}
        success = producer.send_message(message, key="test_key_1")
        print(f"发送消息: {success}")
        
        # 批量发送消息
        messages = [
            {"type": "batch", "content": "Message 1"},
            {"type": "batch", "content": "Message 2"},
            {"type": "batch", "content": "Message 3"}
        ]
        keys = ["batch_key_1", "batch_key_2", "batch_key_3"]
        success = producer.send_batch_messages(messages, keys)
        print(f"批量发送消息: {success}")
        
        # 创建消费者
        consumer = queue.create_consumer("test_topic", "test_group")
        
        # 定义消息处理回调
        def message_handler(message):
            print(f"收到消息: {message}")
        
        # 开始消费消息
        print("开始消费消息...")
        consumer.start_consuming(message_handler)
        
        # 等待一段时间让消费者处理消息
        time.sleep(5)
        
        # 停止消费
        consumer.stop_consuming()
        print("停止消费消息")
        
        # 查询持久化消息
        all_messages = consumer.get_all_messages()
        print(f"持久化消息数量: {len(all_messages)}")
        
        # 根据键获取特定消息
        specific_message = consumer.get_message_by_key("test_key_1")
        print(f"特定消息: {specific_message}")
        
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭队列连接
        queue.close()


# 文档说明
"""
Redis消息队列使用说明

1. 基本概念
   - 生产者(Producer): 负责发送消息到队列
   - 消费者(Consumer): 负责从队列消费消息
   - 主题(Topic): 消息的分类标识
   - 键(Key): 消息的唯一标识，用于持久化存储

2. 主要功能
   - 支持多生产者多消费者
   - 消息持久化存储
   - 批量消息发送
   - 消息重试机制
   - 异步消息消费

3. 使用步骤
   a. 创建配置对象
   b. 创建队列实例
   c. 创建生产者和消费者
   d. 发送和消费消息
   e. 关闭连接

4. 注意事项
   - 确保Redis服务正常运行
   - 合理设置重试次数和延迟时间
   - 及时关闭连接释放资源
   - 消费者使用回调函数处理消息

5. 数据结构
   - 队列: list结构，使用lpush/rpop操作
   - 持久化: hash结构，存储键值对消息
"""

