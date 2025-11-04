import redis
import uuid
import time

import unittest

from redmq.schedule import Schedule
from redmq.schedule import Scheduler
from redmq.message_queue import MessageQueue, PingPongHandler
from redmq.message_queue import Consumer

class TestRedmqSchedule(unittest.TestCase):

    def setUp(self):
        self.conn = redis.Redis("redis", decode_responses=True)
        self.channel = str(uuid.uuid4())

    def test01(self):
        self.conn.ping()

    def test02(self):
        task1 = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_interval_task(task1, 1)
        task2 = sd.get_most_recent_task()
        time.sleep(2)
        tasks = sd.get_wakeup_tasks()
        assert task1 in tasks

        task3 = tasks[task1]
        assert task2["id"] == task1
        assert task3["id"] == task1
        assert task3["schedule_time"] == task2["schedule_time"]

    def test03(self):
        task1 = str(uuid.uuid4())
        task_name = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_interval_task(task1, 1, {"name": task_name})
        task2 = sd.get_most_recent_task()
        time.sleep(2)
        tasks = sd.get_wakeup_tasks()
        assert task1 in tasks

        task3 = tasks[task1]
        assert task2["id"] == task1
        assert task3["id"] == task1
        assert task3["schedule_time"] == task2["schedule_time"]
        assert task3["name"] == task_name
        assert task2["name"] == task_name

    def test04(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_interval_task(task_id, 1)
        task2 = sd.get_most_recent_task()
        sd.add_interval_task(task_id, 1)
        task3 = sd.get_most_recent_task()
        assert task3["next_schedule_time"] > task2["next_schedule_time"]

    def test05(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_runonce_task(task_id, 1)
        task2 = sd.get_most_recent_task()
        sd.add_runonce_task(task_id, 1)
        task3 = sd.get_most_recent_task()
        assert task3["next_schedule_time"] > task2["next_schedule_time"]

    def test06(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_crontab_task(task_id, "* * * * *")
        task2 = sd.get_most_recent_task()
        sd.add_crontab_task(task_id, "* * * * *")
        task3 = sd.get_most_recent_task()
        assert task3["next_schedule_time"] > task2["next_schedule_time"]
        assert task3["next_schedule_time"] - task2["next_schedule_time"] >= 60

    def test07(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_crontab_task(task_id, "*/5 * * * *")
        task2 = sd.get_most_recent_task()
        sd.add_crontab_task(task_id, "*/5 * * * *")
        task3 = sd.get_most_recent_task()
        assert task3["next_schedule_time"] > task2["next_schedule_time"]
        assert task3["next_schedule_time"] - task2["next_schedule_time"] >= 60*5

    def test08(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_crontab_task(task_id, "1 9 * * *")
        task2 = sd.get_most_recent_task()
        sd.add_crontab_task(task_id, "1 9 * * *")
        task3 = sd.get_most_recent_task()
        assert task3["next_schedule_time"] > task2["next_schedule_time"]
        assert task3["next_schedule_time"] - task2["next_schedule_time"] >= 60*60*24

    def test09(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_crontab_task(task_id, "1 9 * * *")
        tasks1 = sd.get_all_tasks()
        sd.delete_task(task_id)
        tasks2 = sd.get_all_tasks()
        assert len(tasks1) == 1
        assert len(tasks2) == 0

    def test10(self):
        sd = Schedule(self.conn, channel=self.channel)

        tasks = sd.get_all_tasks()
        assert len(tasks) == 0

        task = sd.get_most_recent_task()
        assert task is None

    def test11(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)

        sd.add_crontab_task(task_id, "1 9 * * *")
        task1 = sd.get_task(task_id)

        sd.add_next_schedule(task_id) # if use task1 here, task1 dict will be updated
        task2 = sd.get_task(task_id)

        assert task2["next_schedule_time"] > task1["next_schedule_time"]


    def test12(self):
        task_id = str(uuid.uuid4())
        task = {
            "handler": "test12",
            "task_id": task_id,
        }

        handled_task_ids = []
        def test12_handler(msg):
            handled_task_ids.append(msg["message"]["task_id"])
    
        schedule = Schedule(self.conn, channel=self.channel)
        mq = MessageQueue(self.conn, channel=self.channel)
        consumer = Consumer(mq)
        consumer.register_handler("test12", test12_handler)
        consumer.start()

        scheduler = Scheduler(schedule, mq)
        scheduler.start()

        time.sleep(2)

        scheduler.schedule.add_interval_task(task_id, 1, task)

        time.sleep(5)

        assert len(handled_task_ids) > 0
        assert len(handled_task_ids) < 5 + 1
        assert handled_task_ids[0] == task_id

        consumer.stop()
        consumer.wait()
    
    def test13(self):

        pingpong_handler = PingPongHandler()
        task_id = str(uuid.uuid4())
        task = {
            "handler": pingpong_handler.name,
        }


        schedule = Schedule(self.conn, channel=self.channel)
        mq = MessageQueue(self.conn, channel=self.channel)
        consumer = Consumer(mq)
        consumer.register_handler(pingpong_handler.name, pingpong_handler)
        consumer.start()

        scheduler = Scheduler(schedule, mq)
        scheduler.start()

        time.sleep(2)

        scheduler.schedule.add_interval_task(task_id, 1, task)

        time.sleep(5)

        assert scheduler.schedule.get_task_events_count(task_id) > 0
        assert scheduler.schedule.get_task_events_count(task_id) < 5 + 1

        event_ids = scheduler.schedule.get_task_events(task_id)
        assert len(event_ids) > 0
        assert len(event_ids) < 5 + 1
        assert len(set(event_ids)) == len(event_ids)

        for event_id in event_ids:
            result = mq.get_result_nowait(event_id)
            assert result

        consumer.stop()
        consumer.wait()

    def test14(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_interval_task(task_id, 1)
        task1 = sd.get_task(task_id)
        sd.add_interval_task(task_id, 1)
        task2 = sd.get_task(task_id)
        assert task1["next_schedule_time"] < task2["next_schedule_time"]
        sd.add_interval_task(task_id, 1, update=False)
        task3 = sd.get_task(task_id)
        assert task3["next_schedule_time"] == task2["next_schedule_time"]

    def test15(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_crontab_task(task_id, "* * * * *")
        task1 = sd.get_task(task_id)
        sd.add_crontab_task(task_id, "* * * * *")
        task2 = sd.get_task(task_id)
        assert task1["next_schedule_time"] < task2["next_schedule_time"]
        sd.add_crontab_task(task_id, "* * * * *", update=False)
        task3 = sd.get_task(task_id)
        assert task3["next_schedule_time"] == task2["next_schedule_time"]

    def test16(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)

        sd.add_interval_task(task_id, 10)
        task1 = sd.get_task(task_id)

        sd.add_interval_task(task_id, 10) # update by force
        task2 = sd.get_task(task_id)
        assert task2["next_schedule_time"] > task1["next_schedule_time"]

        sd.add_interval_task(task_id, 15, update=False) # DON'T update by force, but rule changed, so will do update, doesn't means later than old schedule
        task3 = sd.get_task(task_id)
    
        assert task3["next_schedule_time"] != task2["next_schedule_time"]

    def test17(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)
        sd.add_crontab_task(task_id, "1 * * * *")
        task1 = sd.get_task(task_id)
        sd.add_crontab_task(task_id, "1 * * * *") # update by force
        task2 = sd.get_task(task_id)
        assert task2["next_schedule_time"] > task1["next_schedule_time"]
        sd.add_crontab_task(task_id, "2 * * * *", update=False) # DON'T update by force, but rule changed, so will do update, but doesn't means later than old schedule
        task3 = sd.get_task(task_id)
        assert task3["next_schedule_time"] != task2["next_schedule_time"]

    def test18(self):
        task_id = str(uuid.uuid4())
        sd = Schedule(self.conn, channel=self.channel)

        sd.add_interval_task(task_id, 10)
        task1 = sd.get_task(task_id)
        sd.add_interval_task(task_id, 10)
        task2 = sd.get_task(task_id)
        assert task2["next_schedule_time"] > task1["next_schedule_time"]

        sd.add_interval_task(task_id, 5, update=False) # rule changed, re-schedule from now.
        task3 = sd.get_task(task_id)
        assert task3["next_schedule_time"] != task2["next_schedule_time"] # re-schedule from now, doesn't means later than old schedule

        assert abs(task3["next_schedule_time"] - 5 - time.time()) < 1
