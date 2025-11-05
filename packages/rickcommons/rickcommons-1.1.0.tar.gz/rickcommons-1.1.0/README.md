# rickcommons 使用说明（Windows 11 / uv）

> 描述：一个基于 Redis 的简易分布式消息实现，提供 Redis Streams 的生产者/消费者能力（近似 Kafka 的主题/组模型），支持持久化、批量读取、阻塞消费与逐条确认。项目依赖与运行统一通过 uv 管理。

## 环境要求

- 操作系统：Windows 11（PowerShell 环境）
- 已安装并可用的 Redis 服务（本地或远程）
- Python ≥ 3.8.6（无需手动创建虚拟环境，使用 uv 管理）
- uv 包管理与运行工具（下面提供安装方式）

## 安装 uv（如未安装）

1. 打开 PowerShell（管理员或普通均可）。
2. 执行以下命令安装 uv（官方安装脚本）：

   ```powershell
   irm https://astral.sh/uv/install.ps1 | iex
   ```

3. 重新打开一个新的 PowerShell 窗口，确认安装成功：

   ```powershell
   uv --version
   ```

## 项目结构

```
e:\mis
├── README.md
├── pyproject.toml
├── uv.lock
└── src\
    └── rickcommons\
        ├── __init__.py
        ├── server.py    # Redis 队列与示例入口（可直接运行）
        └── test.py      # 生产者/消费者 CLI 测试脚本
```

## 依赖安装（使用 uv）

项目已包含 `pyproject.toml` 与 `uv.lock`，推荐使用以下命令安装依赖：

```powershell
uv sync
```

说明：

- `uv sync` 会根据 `pyproject.toml` 与 `uv.lock` 同步依赖至隔离的虚拟环境（无须手动创建 venv）。
- 本项目已配置清华 PyPI 源镜像（见 `pyproject.toml` 中 `[[tool.uv.index]]`），国内网络建议直接使用。

## 快速运行

> 注意：所有运行命令必须使用 `uv run`，禁止直接使用 `python` 命令。

### 方式一：运行内置示例（server.py）

`server.py` 在末尾包含一个演示入口（`if __name__ == "__main__": ...`），可启动生产与消费的简单示例：

```powershell
uv run python -m rickcommons.server
```

如需指定 Redis 连接参数，请编辑 `server.py` 中的 `RedisQueueConfig` 初始化部分（示例代码行 716 起）。

### 方式二：命令行测试脚本（test.py）

`test.py` 提供更灵活的 CLI 参数，支持生产者与消费者两种模式：

- 生产者示例：向主题 `test_topic` 连续发送 5 条消息（0.5 秒间隔），并带键前缀 `msg_`。

  ```powershell
  uv run python -m rickcommons.test --mode produce --topic test_topic --count 5 --interval 0.5 --key-prefix msg_
  ```

- 消费者示例：在消费者组 `group_A` 下批量（每次最多 10 条）阻塞读取（1000ms），持续打印消息内容。

  ```powershell
  uv run python -m rickcommons.test --mode consume --topic test_topic --group group_A --batch-size 10 --timeout 1000
  ```

常用参数说明（摘自 `test.py`）：

- 通用：
  - `--topic`：主题（对应 Redis Stream 的 key，默认 `test_topic`）。
  - `--host` / `--port` / `--db` / `--password`：Redis 连接参数。

- 生产者：
  - `--count`：发送条数。
  - `--interval`：发送间隔秒数。
  - `--key-prefix`：持久化 Hash 键前缀（写入 `messages:{topic}`）。
  - `--stream-maxlen`：Streams 近似最大长度（用于 XADD 裁剪，默认不裁剪）。

- 消费者：
  - `--group`：消费者组名（不同组之间为广播，同组内多消费者为负载均衡）。
  - `--consumer-id`：消费者 ID（不填则自动生成）。
  - `--batch-size`：每次最多读取条数（XREADGROUP COUNT）。
  - `--timeout`：阻塞时长，支持 `1000`、`200ms`、`1.5s` 等格式。

## 开发与规范

- 语言与环境：
  - 全程中文交流与日志输出。
  - 操作系统为 Windows 11。
  - 依赖与运行统一使用 uv；禁止直接使用 `python` 命令。

- 代码质量与命名规范（Python）：
  - 文件：小写加下划线（如 `user_service.py`）。
  - 类名：大驼峰（如 `UserService`）。
  - 函数/变量：小写加下划线（如 `get_user_info`）。
  - 常量：全大写加下划线（如 `MAX_LOGIN_ATTEMPTS`）。

- 注释规范（建议）：
  - 文件头注释需包含文件描述、作者、创建日期与版本号。
  - 函数需使用标准 docstring，包含功能说明、参数、返回值与可能异常。
  - 类注释需说明类的功能、职责与使用方法。
  - 复杂逻辑需添加详细解释性注释。

## 常见问题（FAQ）

1. Redis 连接失败或超时？
   - 确认 Redis 进程已启动、地址与端口可达，必要时设置 `--password`。
   - Windows 防火墙或网络策略可能阻止连接，尝试允许 Redis 端口（默认 6379）。

2. 消费者无消息或阻塞过久？
   - 确认已有生产者向相同 `--topic` 发送消息。
   - 调整 `--timeout` 参数（支持 `ms`/`s`），或增大 `--batch-size`。

3. 如何持久化查询指定键的消息？
   - 本库会以 `messages:{topic}` 的 Hash 持久化消息，键为生产时传入的 `key`。
   - 在 `server.py` 中可调用 `get_message_by_key(key)` 进行检索示例。

## 许可证与作者

- 作者：li2810081
- 版本：v1.0.0
- 许可证：未明确声明（默认保留所有权利）。如需开源协议，请补充至本节。
