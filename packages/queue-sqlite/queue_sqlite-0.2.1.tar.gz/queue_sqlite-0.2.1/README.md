# SQLite 任务队列系统

这个项目是一个基于 SQLite 的高性能任务队列系统，使用 Rust 和 Python 混合编程实现。系统提供了任务调度、消息队列管理和任务生命周期管理的完整解决方案。

## 主要特性
- 🚀 高性能：使用 Rust 实现核心操作，确保高性能

- 📚 多分片支持：支持数据库分片，提高并发处理能力

- ⏱️ 智能调度：提供接收调度器、任务调度器和清理调度器

- 🔒 任务生命周期管理：支持任务状态跟踪、重试机制和过期处理

- 📊 监控支持：内置资源监控功能

- 🧩 任务挂载系统：通过装饰器轻松添加新任务

## 项目结构
```
src/
├── core/                # Rust 核心实现
│   ├── lib.rs           # 主模块
│   ├── queue_operation.rs # 队列操作实现
│   └── task_mounter.rs  # 任务挂载实现
│
├── queue_sqlite/        # Python 实现
│   ├── constant/        # 常量定义（消息优先级、状态、类型）
│   ├── core/            # 核心接口
│   ├── model/           # 数据模型
│   ├── queue_operation/ # 队列操作封装
│   ├── scheduler/       # 调度器实现
│   └── task_cycle/      # 任务生命周期管理
│
tests/                  # 测试代码
```

## 核心组件

1. 消息模型 (MessageItem)
   
   定义了任务消息的数据结构，包含：

    - 消息ID、类型、状态

    - 内容、创建时间、更新时间

    - 优先级、来源、目标

    - 重试次数、过期时间

    - 标签和元数据

2. 队列操作 (QueueOperation)
    
   提供对 SQLite 队列的基本操作：

    - 初始化数据库

    - 入队和出队操作

    - 获取队列长度和已完成消息

    - 更新状态和结果

    - 删除消息和清理过期消息

3. 调度系统

    包含三个主要调度器：

    ***接收调度器 (ReceiveScheduler)***
    - 处理消息发送

    - 管理回调函数

    - 接收已完成消息

    ***任务调度器 (TaskScheduler)***
    - 从队列中获取任务

    - 调用任务函数

    - 更新任务状态和结果

    ***清理调度器 (CleanupScheduler)***
    - 清理过期消息

    - 删除旧消息（默认清理7天前的消息）

4. 任务挂载系统 (TaskMounter)
    提供装饰器挂载任务函数：

    ```python
    @TaskMounter.task(meta={"task_name": "example"})
    def example_task(message_item: MessageItem):
        # 任务逻辑
        return result
    ```
## 使用示例

### 基本使用
```python
from queue_sqlite.scheduler import QueueScheduler
from queue_sqlite.model import MessageItem

# 初始化调度器
scheduler = QueueScheduler(
    receive_thread_num=4, 
    task_thread_num=8, 
    shard_num=12
)

# 启动调度器
scheduler.start_queue_scheduler()

# 创建消息
message = MessageItem(
    content={"data": "example"},
    destination="task_name"
)

# 定义回调函数
def callback(message_item):
    print(f"任务完成: {message_item.id}")

# 发送消息
scheduler.send_message(message, callback)

# ... 程序运行 ...

# 停止调度器
scheduler.stop_queue_scheduler()
```

### 压力测试

```python
# tests/test_stress.py
class TestStress:
    @classmethod
    def test_stress(cls):
        TASK_NUM = 10000
        scheduler = QueueScheduler(receive_thread_num=4, task_thread_num=8, shard_num=12)
        scheduler.start_queue_scheduler()
        
        # 发送大量任务
        for i in range(TASK_NUM):
            message = MessageItem(content={"num": i}, destination="example")
            scheduler.send_message(message, cls._callback)
        
        # 等待所有任务完成
        while scheduler.queue_operation.get_queue_length() > 0:
            time.sleep(0.5)
        
        scheduler.stop_queue_scheduler()
```

## 安装与运行

### 前提条件
Python 3.7+

Rust 工具链

SQLite 开发文件

### 安装步骤
1. 克隆仓库：

    ```bash
    git clone https://gitee.com/cai-xinpenge/queue_sqlite.git
    cd sqlite-task-queue
    ```

2. 安装 Python 依赖：

    ```bash
    pip install -r requirements.txt
    ```

3. 构建 Rust 核心模块：

    ```bash
    cd src/core
    maturin develop --release
    ```
    将会在 `src/core/target/release` 目录下生成 `core.dll` 或 `core.so` 文件。
    将该文件复制到 `queue_sqlite/core` 目录下（dll文件需改名为pyd后缀）。

4. 运行测试：

    ```bash
    pytest tests/
    ```

5. 性能指标

    在标准开发机器上（8核CPU，16GB内存）：

    可处理 10,000+ 任务(斐波那契数列前500项计算)/分钟

    平均任务延迟 < 50ms

    CPU 使用率 < 60%

    内存占用 < 500MB

### 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 仓库

    创建新分支 (git checkout -b feature/your-feature)

    提交更改 (git commit -am 'Add some feature')

    推送到分支 (git push origin feature/your-feature)

2. 创建 Pull Request

### 许可证

本项目采用 MIT 许可证。

