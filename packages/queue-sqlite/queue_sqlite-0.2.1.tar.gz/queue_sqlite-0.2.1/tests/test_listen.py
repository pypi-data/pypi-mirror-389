from listen import *
from queue_sqlite.scheduler import QueueScheduler
import time


class TestListen:
    def test_listen_data(self):
        scheduler = QueueScheduler(scheduler_type="qt")
        scheduler.start()
        scheduler.update_listen_data("key_1", "value_1")
        time.sleep(0.001)
        scheduler.update_listen_data("key_1", "value_2")
        time.sleep(0.001)
        scheduler.update_listen_data("key_1", "value_3")
        time.sleep(0.001)
        scheduler.update_listen_data("key_1", "value_4")
        time.sleep(0.001)
        scheduler.stop()
        print(scheduler.get_listen_datas())
        print(scheduler.get_listen_data("key_1"))
