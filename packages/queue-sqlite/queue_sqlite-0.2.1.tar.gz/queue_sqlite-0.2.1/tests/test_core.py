import queue_sqlite_core as core
from queue_sqlite.mounter.task_mounter import TaskMounter
from queue_sqlite.model import MessageItem


class TestCore:
    queue_operation = core.QueueOperation("./cache/test.db")

    @classmethod
    def test_task_mounter(cls):
        task_mounter = core.TaskMounter(TaskMounter)
        task_mounter.get_task_list()
        print(
            task_mounter.get_task_function("task")({"num": 1})(lambda x: x + 1).meta[  # type: ignore
                "num"
            ]
        )
        from tasks import example

        task_mounter.get_task_list()
        print(task_mounter.get_task_function("<lambda>"))

    @classmethod
    def test_queue_operation_init_db(cls):
        cls.queue_operation.init_db()

    @classmethod
    def test_queue_operation_enqueue(cls):
        message_item = MessageItem(content={"num": 1}, destination="test")  # type: ignore
        cls.queue_operation.enqueue(message_item.to_dict_by_core())

    @classmethod
    def test_queue_operation_dequeue(cls):
        message_item = MessageItem(content={"num": 1}, destination="test")
        cls.queue_operation.enqueue(message_item.to_dict_by_core())
        print(cls.queue_operation.dequeue(1))
