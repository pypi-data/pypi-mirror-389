使用方法（基于 Redis Streams 的分布式生产/消费）

一、环境准备
- 操作系统：Windows 11
- 依赖管理与执行：uv（禁止直接使用 python 命令）
- Redis：确保可访问（默认示例使用 192.168.2.251:6379，db=6，密码 redis_Q8zTm7）

二、启动生产者（一个终端）
- 命令：
  uv run src/rickcommons/main.py --topic test_topic --key-prefix test_key --interval 1,3 --host 192.168.2.251 --port 6379 --db 6 --password redis_Q8zTm7
- 说明：
  - 将消息写入指定主题（topic）的 Redis Stream（XADD）。
  - 每 1–3 秒发送一条消息，Hash 持久化键形如 test_key_时间戳。

三、启动消费者 A（第二个终端）
- 命令：
  uv run src/rickcommons/client.py --topic test_topic --group group_A --timeout 1s --host 192.168.2.251 --port 6379 --db 6 --password redis_Q8zTm7
- 说明：
  - 从消费者组 group_A 读取消息（XREADGROUP），收到后打印并确认（XACK）。

四、启动消费者 B（第三个终端）
- 命令：
  uv run src/rickcommons/client.py --topic test_topic --group group_B --timeout 1s --host 192.168.2.251 --port 6379 --db 6 --password redis_Q8zTm7
- 说明：
  - 与消费者 A 订阅同一主题但不同组。两者将分别收到同一条消息，实现“同一消息被不同消费者处理（跨组广播）”。

五、参数快速说明（常用）
- --topic：消息主题（Stream 名称），如 test_topic。
- --group：消费者组名称。不同组之间相互独立，能够各自获取到同一条消息；同一组内多个实例会对消息做负载均衡。
- --timeout：阻塞超时，支持 1000、"1s"、"200ms" 等格式。
- --key-prefix（生产者）：Hash 持久化键前缀。
- --interval（生产者）：发送间隔范围，格式 "低,高"，如 "1,3"。
- --host/--port/--db/--password：Redis 连接参数。

六、退出
- 按 Ctrl+C 停止对应终端的生产者或消费者进程。

七、提示
- 想要横向扩展同一类处理逻辑：在同一个组内启动多个消费者实例（不同 consumer_id），实现组内负载均衡。
- 想要让同一消息被不同处理器独立处理：为同一主题创建不同的组（如 group_A、group_B），实现跨组广播。