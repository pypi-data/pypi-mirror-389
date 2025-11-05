# -*- coding: utf-8 -*-
"""
文件名: commons.py
作者: li2810081
创建日期: 2025-11-03
版本号: v1.0.1
文件描述: Redis 消息通知队列，支持持久化数据、多生产者多消费者，提供基于  Redis Streams 的 (kafka) 实现。
"""

import sys
import os
import redis
import logging
import json
import time
import threading

from typing import Any, Dict, Optional, Callable, List

logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class Message:
    # {
    #         'id': str(int(time.time() * 1000)),  # 时间戳作为消息ID
    #         'timestamp': time.time(),
    #         'topic': self.topic,
    #         'key': key,
    #         'data': message
    #     }
    id: str
    timestamp: float
    topic: str
    key: str
    data: Dict[str, Any]
    

    

def parse_block_to_ms(raw_value: Any, default: int = 0) -> int:
    """
    功能说明：
        将原始的阻塞时间配置值解析为毫秒单位的非负整数，用于 Redis XREADGROUP 的 block 参数。
        支持 None、整数、浮点数、以及字符串（如 "5000"、"5s"、"1.5"、"200ms"）。

    参数描述：
        raw_value：原始输入值，可能来自方法参数或配置文件。
        default：当 raw_value 无法解析时使用的默认毫秒值（非负整数）。

    返回值说明：
        返回转换后的非负整数毫秒值（int）。

    可能抛出的异常：
        ValueError：当 raw_value 或 default 为负数，或能解析但为负时抛出。
    """
    # 中文日志：开始解析 BLOCK 参数
    logger.debug("解析阻塞时间 BLOCK 参数：开始")

    if default is None:
        default = 0
    if not isinstance(default, int) or default < 0:
        raise ValueError("默认 BLOCK 毫秒值必须为非负整数")

    if raw_value is None:
        logger.debug(f"解析阻塞时间：raw_value 为 None，使用默认值 {default} 毫秒")
        return default

    # 避免布尔被当作整数
    if isinstance(raw_value, bool):
        logger.debug("解析阻塞时间：检测到布尔值，建议使用明确的毫秒整数；已使用默认值")
        return default

    # 整数
    if isinstance(raw_value, int):
        if raw_value < 0:
            raise ValueError("BLOCK 毫秒值不能为负数")
        logger.debug(f"解析阻塞时间：检测到整数 {raw_value} 毫秒")
        return raw_value

    # 浮点数
    if isinstance(raw_value, float):
        if raw_value < 0:
            raise ValueError("BLOCK 毫秒值不能为负数")
        ms = int(raw_value)
        logger.debug(f"解析阻塞时间：检测到浮点数 {raw_value}，转换为 {ms} 毫秒")
        return ms

    # 字符串
    if isinstance(raw_value, str):
        value = raw_value.strip().lower()
        # 结尾为 ms
        if value.endswith("ms"):
            value_num = value[:-2].strip()
            ms = int(float(value_num))
            if ms < 0:
                raise ValueError("BLOCK 毫秒值不能为负数")
            logger.debug(f"解析阻塞时间：字符串毫秒格式 {raw_value} -> {ms} 毫秒")
            return ms
        # 结尾为 s（秒）
        if value.endswith("s"):
            value_num = value[:-1].strip()
            seconds = float(value_num)
            if seconds < 0:
                raise ValueError("BLOCK 秒值不能为负数")
            ms = int(seconds * 1000)
            logger.debug(f"解析阻塞时间：字符串秒格式 {raw_value} -> {ms} 毫秒")
            return ms
        # 纯数字或可解析数字的字符串
        try:
            num = float(value)
            if num < 0:
                raise ValueError("BLOCK 数值不能为负数")
            ms = int(num)
            logger.debug(f"解析阻塞时间：字符串数值 {raw_value} -> {ms} 毫秒")
            return ms
        except Exception:
            logger.debug(f"解析阻塞时间：无法解析字符串 '{raw_value}'，使用默认值 {default} 毫秒")
            return default

    # 其他类型
    logger.debug(f"解析阻塞时间：不支持类型 {type(raw_value)}，使用默认值 {default} 毫秒")
    return default


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
                 retry_delay: float = 1.0,
                 stream_maxlen: Optional[int] = None):
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
            stream_maxlen: Streams 模式下的近似最大长度（条数），用于 XADD 裁剪，None 表示不裁剪。
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.stream_maxlen = stream_maxlen


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
    Redis队列生产者（基于 Redis Streams 的分布式生产）
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
        发送消息到 Redis Streams（分布式生产）
        
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
        
        # 重试机制（XADD 写入 Streams）
        for attempt in range(self.queue_manager.config.retry_attempts):
            try:
                # 使用 XADD 写入流，支持分布式生产与消费者组消费
                entry_id = redis_client.xadd(
                    name=self.topic,
                    fields={
                        'payload': message_json,
                        'key': key or ''
                    },
                    id='*',
                    maxlen=self.queue_manager.config.stream_maxlen,
                    approximate=True
                )
                
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
        批量发送消息到 Redis Streams
        
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
            
            pipeline.xadd(
                name=self.topic,
                fields={
                    'payload': message_json,
                    'key': key or ''
                },
                id='*',
                maxlen=self.queue_manager.config.stream_maxlen,
                approximate=True
            )
            
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
    
    def consume_message(self, timeout: Any = 1000) -> Optional[Dict[str, Any]]:
        """
        消费单条消息
        
        Args:
            timeout: 阻塞超时时间（毫秒），支持 int/float/str/None（如 "5s"、"200ms"、1000）。
            
        Returns:
            Optional[Dict[str, Any]]: 消息内容，如果超时返回None
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            block_ms = parse_block_to_ms(timeout, default=1000)
            logger.debug(f"开始读取 Redis Streams（单条）：BLOCK={block_ms} 毫秒，topic={self.topic}，group={self.consumer_group}，consumer={self.consumer_id}")
            # 使用消费者组读取消息
            messages = redis_client.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_id,
                streams={self.topic: ">"},
                count=1,
                block=block_ms
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
            logger.debug(f"消费消息时发生错误: {e}")
        
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
                                logger.debug(f"处理消息时发生错误: {e}")
                                # 处理失败的消息不会确认，稍后会重新投递
                except Exception as e:
                    logger.debug(f"消费循环发生错误: {e}")
                    time.sleep(1)
        
        self._consumer_thread = threading.Thread(target=consume_loop)
        self._consumer_thread.daemon = True
        self._consumer_thread.start()
    
    def consume_batch_messages(self, count: int = 10, timeout: Any = 1000) -> List[Dict[str, Any]]:
        """
        批量消费消息
        
        Args:
            count: 消息数量
            timeout: 阻塞超时时间（毫秒），支持 int/float/str/None（如 "5s"、"200ms"、1000）。
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        redis_client = self.queue_manager.get_redis_client()
        
        try:
            block_ms = parse_block_to_ms(timeout, default=1000)
            logger.debug(f"开始读取 Redis Streams（批量）：BLOCK={block_ms} 毫秒，count={count}，topic={self.topic}，group={self.consumer_group}，consumer={self.consumer_id}")
            messages = redis_client.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_id,
                streams={self.topic: ">"},
                count=count,
                block=block_ms
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
            logger.debug(f"批量消费消息时发生错误: {e}")
            return []
    
    def stop_consuming(self):
        """
        停止消费消息
        """
        self._running = False
        if hasattr(self, '_consumer_thread'):
            self._consumer_thread.join(timeout=5)

    def get_all_messages(self) -> List[Dict[str, Any]]:
        """
        获取持久化消息列表（从 Hash：messages:{topic} 读取）

        Returns:
            List[Dict[str, Any]]: 消息字典列表（解析自 JSON），若不存在或解析失败则返回空列表。

        可能抛出的异常：
            redis.RedisError：Redis 访问异常（内部捕获并转为空列表）。
        """
        redis_client = self.queue_manager.get_redis_client()
        try:
            raw = redis_client.hgetall(f"messages:{self.topic}")
            result: List[Dict[str, Any]] = []
            for k, v in raw.items():
                try:
                    data = json.loads(v)
                    result.append(data)
                except Exception as e:
                    logger.debug(f"解析持久化消息失败（key={k}）：{e}")
            logger.debug(f"读取持久化消息完成：共 {len(result)} 条（topic={self.topic}）")
            return result
        except redis.RedisError as e:
            logger.debug(f"读取持久化消息时发生错误: {e}")
            return []

    def get_message_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        根据键读取持久化消息（Hash：messages:{topic} 中的指定 key）

        Args:
            key: 消息唯一键。

        Returns:
            Optional[Dict[str, Any]]: 解析后的消息字典；不存在或解析失败返回 None。

        可能抛出的异常：
            redis.RedisError：Redis 访问异常（内部捕获并返回 None）。
        """
        redis_client = self.queue_manager.get_redis_client()
        try:
            val = redis_client.hget(f"messages:{self.topic}", key)
            if val is None:
                logger.debug(f"未找到持久化消息（key={key}, topic={self.topic}）")
                return None
            try:
                data = json.loads(val)
                logger.debug(f"读取持久化消息成功（key={key}, topic={self.topic}）")
                return data
            except Exception as e:
                logger.debug(f"解析持久化消息失败（key={key}）：{e}")
                return None
        except redis.RedisError as e:
            logger.debug(f"根据键读取持久化消息时发生错误: {e}")
            return None
    
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
            logger.debug(f"获取待处理消息时发生错误: {e}")
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
            logger.debug(f"认领待处理消息时发生错误: {e}")
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
        host="",
        port=6379,
        db=0,
        password="",
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
        logger.debug(f"发送消息: {success}")
        
        
        # 创建消费者
        consumer = queue.create_consumer("test_topic")
        
        # 定义消息处理回调
        def message_handler(message):
            print(f"收到消息: {message}")
        
        # 开始消费消息
        logger.debug("开始消费消息...")
        consumer.start_consuming(message_handler)
        
        # 等待一段时间让消费者处理消息
        time.sleep(5)
        
        # 停止消费
        consumer.stop_consuming()
        logger.debug("停止消费消息")
        
        # 查询持久化消息
        all_messages = consumer.get_all_messages()
        logger.debug(f"持久化消息数量: {len(all_messages)}")
        
        # 根据键获取特定消息
        specific_message = consumer.get_message_by_key("test_key_1")
        logger.debug(f"特定消息: {specific_message}")
        
    except Exception as e:
        logger.debug(f"发生错误: {e}")
    finally:
        # 关闭队列连接
        queue.close()

