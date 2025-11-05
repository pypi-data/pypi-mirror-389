# -*- coding: utf-8 -*-
"""
文件名: test.py
作者: li2810081
创建日期: 2025-11-05
版本号: v1.0.0
文件描述: 基于 Redis Streams 的生产者/消费者测试脚本，演示批量消费与阻塞读取、跨消费者组广播及逐条确认。
"""

import sys
import os
import json
import time
import argparse
import logging
from typing import Any, Dict, Optional


# 日志配置（中文输出）
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 兼容 src 布局：将项目的 src 目录加入 sys.path，方便 "import rickcommons.server"
CURRENT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rickcommons.server import (
    RedisQueueConfig,
    RedisQueueManager,
    RedisQueueProducer,
    RedisStreamsConsumer,
    parse_block_to_ms,
)


def build_manager(host, port, db: int, password: Optional[str], stream_maxlen: Optional[int]) -> RedisQueueManager:
    """
    功能说明：
        构建并返回 RedisQueueManager 管理器实例，用于连接 Redis 并提供生产者/消费者所需的客户端。

    参数描述：
        host: Redis 地址。
        port: Redis 端口。
        db: Redis 数据库编号。
        password: Redis 密码，未设置时为 None。
        stream_maxlen: Streams 近似最大长度，用于 XADD 裁剪，None 表示不裁剪。

    返回值说明：
        RedisQueueManager: 已初始化的队列管理器。

    可能抛出的异常：
        redis.ConnectionError: 连接失败时可能抛出（内部在 get_redis_client() 时校验）。
    """
    config = RedisQueueConfig(
        host=host,
        port=port,
        db=db,
        password=password,
        stream_maxlen=stream_maxlen,
    )
    return RedisQueueManager(config=config)


def run_producer(topic: str, count: int, interval: float, key_prefix: Optional[str],
                 host: str, port: int, db: int, password: Optional[str], stream_maxlen: Optional[int]) -> None:
    """
    功能说明：
        以固定间隔向指定 topic 发送 count 条测试消息，演示 Redis Streams 的生产行为。

    参数描述：
        topic: 目标主题（Stream 名称）。
        count: 需要发送的消息条数。
        interval: 每条消息的发送间隔（秒）。
        key_prefix: 消息键前缀，用于持久化 Hash（messages:{topic}）。
        host/port/db/password/stream_maxlen: Redis 连接与 Streams 配置参数。

    返回值说明：
        None。函数完成后打印发送结果日志。

    可能抛出的异常：
        redis.RedisError: 发送过程中发生的 Redis 异常（内部带重试机制）。
    """
    manager = build_manager(host, port, db, password, stream_maxlen)
    producer = RedisQueueProducer(queue_manager=manager, topic=topic)
    logger.info(f"生产者启动：topic={topic}，准备发送 {count} 条消息，间隔 {interval}s")

    for i in range(1, count + 1):
        key = f"{key_prefix}{i}" if key_prefix else None
        payload: Dict[str, Any] = {
            "index": i,
            "message": f"这是第 {i} 条测试消息",
            "ts": time.time(),
        }
        ok = producer.send_message(payload, key=key)
        if ok:
            logger.info(f"发送成功：index={i}，key={key}")
        else:
            logger.error(f"发送失败：index={i}，key={key}")
        if i < count:
            time.sleep(interval)

    logger.info("生产者任务完成")


def _parse_stream_payload(raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    功能说明：
        解析消费者从 Redis Streams 读到的单条消息的 data 字段，将其中的 'payload'（JSON 字符串）转换为字典。

    参数描述：
        raw_data: 来自 XREADGROUP 的单条消息 data（如 {'payload': '...json...', 'key': 'k1'}）。

    返回值说明：
        dict 或 None：解析成功返回字典，失败返回 None。

    可能抛出的异常：
        无（内部捕获异常并返回 None）。
    """
    try:
        payload_str = raw_data.get("payload")
        if not payload_str:
            logger.warning("消息中不存在 payload 字段或为空")
            return None
        return json.loads(payload_str)
    except Exception as e:
        logger.error(f"解析 payload 失败：{e}")
        return None


def run_consumer(topic: str, group: str, consumer_id: Optional[str],
                 batch_size: int, timeout: Any,
                 host: str, port: int, db: int, password: Optional[str]) -> None:
    """
    功能说明：
        持续消费指定 topic 的消息，属于指定消费者组 group，演示批量读取（COUNT=batch_size）和阻塞（BLOCK=timeout）。

    参数描述：
        topic: 主题（Stream）。
        group: 消费者组名；不同组之间为广播，同一组内多消费者为负载均衡。
        consumer_id: 消费者 ID；为空时自动生成。
        batch_size: 每次最多读取的消息条数（XREADGROUP COUNT）。
        timeout: 阻塞超时时间（支持 int/float/str，如 "1000"、"1.5s"、"200ms"）。
        host/port/db/password: Redis 连接配置。

    返回值说明：
        None。函数持续运行直到用户中断（Ctrl+C）。

    可能抛出的异常：
        无（内部捕获并输出日志）。
    """
    manager = build_manager(host, port, db, password, stream_maxlen=None)
    consumer = RedisStreamsConsumer(queue_manager=manager, topic=topic, consumer_group=group, consumer_id=consumer_id)
    block_ms = parse_block_to_ms(timeout, default=1000)

    logger.info(f"消费者启动：topic={topic}，group={group}，consumer_id={consumer.consumer_id}，batch_size={batch_size}，BLOCK={block_ms}ms")
    logger.info("提示：不同 group 会同时收到同一条消息；同一 group 内多实例会做负载均衡。按 Ctrl+C 退出。")

    try:
        def handler(msg: Dict[str, Any]) -> None:
            """
            功能说明：
                单条消息处理回调。解析 payload 并输出详细内容。异常时不确认该消息。

            参数描述：
                msg: 从消费者读到的单条消息字典，包含 id、data（fields）、topic、consumer_group。

            返回值说明：
                None。

            可能抛出的异常：
                无（内部捕获日志）。
            """
            payload = _parse_stream_payload(msg.get("data", {}))
            key = msg.get("data", {}).get("key")
            if payload is None:
                raise ValueError("payload 解析失败")
            logger.info(f"收到消息：id={msg['id']}，key={key}，payload={payload}")

        # 启动消费线程，内部按批读取并逐条 XACK
        consumer.start_consuming(message_handler=handler, batch_size=batch_size)

        # 主线程保持运行，便于 Ctrl+C 退出
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("收到退出指令，正在停止消费者...")
    except Exception as e:
        logger.error(f"消费者运行异常：{e}")
    finally:
        consumer.stop_consuming()
        logger.info("消费者已停止")


def build_arg_parser() -> argparse.ArgumentParser:
    """
    功能说明：
        构建命令行参数解析器，提供生产者/消费者两种模式，以及 Redis 连接与 Streams/消费相关配置。

    参数描述：
        无。

    返回值说明：
        argparse.ArgumentParser：参数解析器实例。

    可能抛出的异常：
        无。
    """
    parser = argparse.ArgumentParser(description="Redis Streams 生产者/消费者测试脚本（中文日志）")
    parser.add_argument("--mode", choices=["produce", "consume"], default="produce", help="运行模式：produce 或 consume")
    parser.add_argument("--topic", default="test_topic", help="主题名（Stream key）")

    # Producer 专用参数
    parser.add_argument("--count", type=int, default=10, help="生产者发送的消息条数")
    parser.add_argument("--interval", type=float, default=1.0, help="生产者发送间隔（秒）")
    parser.add_argument("--key-prefix", default="msg_", help="持久化 Hash 的键前缀（messages:{topic}）")
    parser.add_argument("--stream-maxlen", type=int, default=None, help="Streams 近似最大长度（XADD 裁剪），默认不裁剪")

    # Consumer 专用参数
    parser.add_argument("--group", default="group_A", help="消费者组名")
    parser.add_argument("--consumer-id", default=None, help="消费者 ID（默认自动生成）")
    parser.add_argument("--batch-size", type=int, default=10, help="每次最多读取的条数（COUNT）")
    parser.add_argument("--timeout", default="1000", help="阻塞时长（如 1000、200ms、1.5s）")

    # Redis 连接参数
    parser.add_argument("--host", default="localhost", help="Redis 地址")
    parser.add_argument("--port", type=int, default=6379, help="Redis 端口")
    parser.add_argument("--db", type=int, default=0, help="Redis 数据库编号")
    parser.add_argument("--password", default=None, help="Redis 密码（如无则留空）")

    return parser


def main() -> None:
    """
    功能说明：
        脚本入口，根据命令行参数选择生产者或消费者模式运行。

    参数描述：
        无。

    返回值说明：
        None。

    可能抛出的异常：
        无（内部捕获并打印中文日志）。
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.mode == "produce":
        run_producer(
            topic=args.topic,
            count=args.count,
            interval=args.interval,
            key_prefix=args.key_prefix,
            host=args.host,
            port=args.port,
            db=args.db,
            password=args.password,
            stream_maxlen=args.stream_maxlen,
        )
    else:
        run_consumer(
            topic=args.topic,
            group=args.group,
            consumer_id=args.consumer_id,
            batch_size=args.batch_size,
            timeout=args.timeout,
            host=args.host,
            port=args.port,
            db=args.db,
            password=args.password,
        )


if __name__ == "__main__":
    main()