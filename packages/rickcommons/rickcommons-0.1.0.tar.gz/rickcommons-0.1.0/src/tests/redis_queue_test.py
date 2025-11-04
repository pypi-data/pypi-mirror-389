# -*- coding: utf-8 -*-
"""
文件名: redis_queue_test.py
作者: li2810081
日期: 2025-11-03
描述: Redis队列模块的单元测试和集成测试
"""

import pytest
import time
import json
import redis
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from rickcommons.redis_queue import (
    RedisQueueConfig,
    RedisQueueManager,
    RedisQueueProducer,
    RedisStreamsConsumer,
    RedisQueue
)


class TestRedisQueueConfig:
    """Redis队列配置类测试"""
    
    def test_config_default_values(self):
        """测试配置类的默认值"""
        config = RedisQueueConfig()
        
        assert config.host == 'localhost'
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.max_connections == 10
        assert config.socket_timeout == 5
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
    
    def test_config_custom_values(self):
        """测试配置类的自定义值"""
        config = RedisQueueConfig(
            host='127.0.0.1',
            port=6380,
            db=1,
            password='redis',
            max_connections=20,
            socket_timeout=10,
            retry_attempts=5,
            retry_delay=2.0
        )
        
        assert config.host == '127.0.0.1'
        assert config.port == 6380
        assert config.db == 1
        assert config.password == 'redis'
        assert config.max_connections == 20
        assert config.socket_timeout == 10
        assert config.retry_attempts == 5
        assert config.retry_delay == 2.0


class TestRedisQueueManager:
    """Redis队列管理器测试"""
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        assert manager.config == config
        assert manager._redis_client is None
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_get_redis_client_success(self, mock_redis):
        """测试成功获取Redis客户端"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        # 模拟Redis客户端
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        client = manager.get_redis_client()
        
        assert client == mock_client
        mock_redis.assert_called_once()
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_get_redis_client_connection_error(self, mock_redis):
        """测试Redis连接失败"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        # 模拟连接失败
        mock_client = Mock()
        mock_client.ping.side_effect = redis.ConnectionError("Connection failed")
        mock_redis.return_value = mock_client
        
        with pytest.raises(redis.ConnectionError, match="无法连接到Redis服务器"):
            manager.get_redis_client()
    
    def test_close_method(self):
        """测试关闭连接方法"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        # 模拟有连接的场景
        mock_client = Mock()
        manager._redis_client = mock_client
        
        manager.close()
        
        mock_client.close.assert_called_once()
        assert manager._redis_client is None


class TestRedisQueueProducer:
    """Redis队列生产者测试"""
    
    def test_producer_initialization(self):
        """测试生产者初始化"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        producer = RedisQueueProducer(manager, "test_topic")
        
        assert producer.queue_manager == manager
        assert producer.topic == "test_topic"
    
    @patch('qyscripts.redis_queue.time.time')
    @patch('qyscripts.redis_queue.json.dumps')
    def test_send_message_success(self, mock_json_dumps, mock_time):
        """测试成功发送消息"""
        # 模拟时间戳
        mock_time.return_value = 1609459200.0
        
        # 模拟JSON序列化
        mock_json_dumps.return_value = '{"test": "data"}'
        
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        # 模拟Redis客户端
        mock_client = Mock()
        mock_client.lpush.return_value = 1
        mock_client.hset.return_value = 1
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            producer = RedisQueueProducer(manager, "test_topic")
            message = {"type": "test", "content": "Hello"}
            
            result = producer.send_message(message, key="test_key")
            
            assert result is True
            mock_client.lpush.assert_called_once_with("queue:test_topic", '{"test": "data"}')
            mock_client.hset.assert_called_once_with("messages:test_topic", "test_key", '{"test": "data"}')
    
    @patch('qyscripts.redis_queue.time.time')
    @patch('qyscripts.redis_queue.json.dumps')
    def test_send_message_without_key(self, mock_json_dumps, mock_time):
        """测试发送消息（无键）"""
        mock_time.return_value = 1609459200.0
        mock_json_dumps.return_value = '{"test": "data"}'
        
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_client.lpush.return_value = 1
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            producer = RedisQueueProducer(manager, "test_topic")
            message = {"type": "test", "content": "Hello"}
            
            result = producer.send_message(message)
            
            assert result is True
            mock_client.lpush.assert_called_once()
            mock_client.hset.assert_not_called()
    
    @patch('qyscripts.redis_queue.time.time')
    @patch('qyscripts.redis_queue.json.dumps')
    def test_send_message_retry_success(self, mock_json_dumps, mock_time):
        """测试发送消息重试成功"""
        mock_time.return_value = 1609459200.0
        mock_json_dumps.return_value = '{"test": "data"}'
        
        config = RedisQueueConfig(retry_attempts=3, retry_delay=0.1)
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        # 前两次失败，第三次成功
        mock_client.lpush.side_effect = [redis.RedisError("Error 1"), redis.RedisError("Error 2"), 1]
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            producer = RedisQueueProducer(manager, "test_topic")
            message = {"type": "test", "content": "Hello"}
            
            result = producer.send_message(message)
            
            assert result is True
            assert mock_client.lpush.call_count == 3
    
    @patch('qyscripts.redis_queue.time.time')
    @patch('qyscripts.redis_queue.json.dumps')
    def test_send_message_all_retries_failed(self, mock_json_dumps, mock_time):
        """测试发送消息所有重试都失败"""
        mock_time.return_value = 1609459200.0
        mock_json_dumps.return_value = '{"test": "data"}'
        
        config = RedisQueueConfig(retry_attempts=2, retry_delay=0.1)
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_client.lpush.side_effect = redis.RedisError("Persistent error")
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            producer = RedisQueueProducer(manager, "test_topic")
            message = {"type": "test", "content": "Hello"}
            
            with pytest.raises(redis.RedisError, match="发送消息失败"):
                producer.send_message(message)
    
    @patch('qyscripts.redis_queue.time.time')
    @patch('qyscripts.redis_queue.json.dumps')
    def test_send_batch_messages_success(self, mock_json_dumps, mock_time):
        """测试批量发送消息成功"""
        mock_time.return_value = 1609459200.0
        mock_json_dumps.return_value = '{"test": "data"}'
        
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_pipeline = Mock()
        mock_client.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [1, 1, 1]
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            producer = RedisQueueProducer(manager, "test_topic")
            messages = [
                {"type": "batch", "content": "Message 1"},
                {"type": "batch", "content": "Message 2"},
                {"type": "batch", "content": "Message 3"}
            ]
            keys = ["key1", "key2", "key3"]
            
            result = producer.send_batch_messages(messages, keys)
            
            assert result is True
            mock_pipeline.execute.assert_called_once()
    
    @patch('qyscripts.redis_queue.time.time')
    @patch('qyscripts.redis_queue.json.dumps')
    def test_send_batch_messages_failure(self, mock_json_dumps, mock_time):
        """测试批量发送消息失败"""
        mock_time.return_value = 1609459200.0
        mock_json_dumps.return_value = '{"test": "data"}'
        
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_pipeline = Mock()
        mock_client.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.side_effect = redis.RedisError("Pipeline error")
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            producer = RedisQueueProducer(manager, "test_topic")
            messages = [
                {"type": "batch", "content": "Message 1"},
                {"type": "batch", "content": "Message 2"}
            ]
            
            result = producer.send_batch_messages(messages)
            
            assert result is False


class TestRedisStreamsConsumer:
    """Redis Streams消费者测试"""
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_consumer_initialization(self, mock_redis):
        """测试消费者初始化"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            consumer = RedisStreamsConsumer(manager, "test_topic", "test_group", "test_consumer")
            
            assert consumer.queue_manager == manager
            assert consumer.topic == "test_topic"
            assert consumer.consumer_group == "test_group"
            assert consumer.consumer_id == "test_consumer"
            assert consumer._running is False
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_init_consumer_group_success(self, mock_redis):
        """测试初始化消费者组成功"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            consumer = RedisStreamsConsumer(manager, "test_topic", "test_group")
            
            mock_client.xgroup_create.assert_called_once_with(
                name="test_topic",
                groupname="test_group",
                id="0",
                mkstream=True
            )
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_init_consumer_group_already_exists(self, mock_redis):
        """测试消费者组已存在的情况"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        # 模拟消费者组已存在的错误
        from redis import ResponseError
        mock_client.xgroup_create.side_effect = ResponseError("BUSYGROUP Consumer Group name already exists")
        
        # 不应该抛出异常
        try:
            consumer = RedisStreamsConsumer(manager, "test_topic", "test_group")
            assert consumer is not None
        except ResponseError:
            pytest.fail("消费者组已存在时不应该抛出异常")
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_consume_message_success(self, mock_redis):
        """测试成功消费消息"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        # 模拟有消息的情况
        mock_message_data = {"field1": "value1", "field2": "value2"}
        mock_client.xreadgroup.return_value = [
            ("test_topic", [("12345-0", mock_message_data)])
        ]
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            consumer = RedisStreamsConsumer(manager, "test_topic", "test_group")
            
            message = consumer.consume_message(timeout=1000)
            
            assert message is not None
            assert message["id"] == "12345-0"
            assert message["data"] == mock_message_data
            assert message["topic"] == "test_topic"
            assert message["consumer_group"] == "test_group"
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_consume_message_timeout(self, mock_redis):
        """测试消费消息超时"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        # 模拟没有消息的情况
        mock_client.xreadgroup.return_value = []
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            consumer = RedisStreamsConsumer(manager, "test_topic", "test_group")
            
            message = consumer.consume_message(timeout=1000)
            
            assert message is None
    
    @patch('qyscripts.redis_queue.redis.Redis')
    def test_ack_message_success(self, mock_redis):
        """测试成功确认消息"""
        config = RedisQueueConfig()
        manager = RedisQueueManager(config)
        
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        with patch.object(manager, 'get_redis_client', return_value=mock_client):
            consumer = RedisStreamsConsumer(manager, "test_topic", "test_group")
            
            result = consumer.ack_message("test_message_id")