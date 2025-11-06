from queue_sqlite.mounter import task
from queue_sqlite.model import MessageItem


@task(meta={"task_name": "test"})
async def async_example(message_item: MessageItem):
    def fibonacci_generator():
        a, b = 0, 1
        while True:
            yield a
            a, b = b, a + b

    # 示例：获取前10项
    fib = fibonacci_generator()
    message_item.result = {"fibonacci": [next(fib) for _ in range(500)]}
    return message_item.to_json()


# 输出：[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
