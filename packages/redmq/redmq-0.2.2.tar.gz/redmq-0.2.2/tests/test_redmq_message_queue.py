
import time
import uuid

import unittest

import redis
from redmq.message_queue import MessageQueue

class TestRedmqMessageQueue(unittest.TestCase):

    def setUp(self):
        self.conn = redis.Redis("redis")
        self.channel = str(uuid.uuid4())

    def test01(self):
        self.conn.ping()

    def test02(self):
        data1 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel)
        mq.push(data1)
        msg = mq.pop_nowait()
        assert data1 == msg["message"]
        assert mq.acknowledge(msg)
        mq.delete_result(msg)

    def test03(self):
        mq = MessageQueue(self.conn, channel=self.channel)
        assert mq.pop_nowait() is None

    def test03(self):
        data1 = str(uuid.uuid4())
        data2 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel, default_timeout=2)
        mq.push(data1)
        mq.push(data2)
        msg1 = mq.pop_nowait()
        msg2 = mq.pop_nowait()
        assert msg1["message"] == data1
        assert msg2["message"] == data2

        mq.acknowledge(msg1)
        mq.acknowledge(msg2)
        mq.delete_result(msg1)
        mq.delete_result(msg2)

    def test04(self):
        msgid = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel)
        result = mq.acknowledge(msgid)
        assert result
        msg1 = mq.get_result_nowait(msgid)
        assert msg1["meta_broken"]
        mq.delete_result(msgid)

    def test05(self):
        mq = MessageQueue(self.conn, channel=self.channel)
        total = 10000
        stime = time.time()
        for i in range(total):
            mq.push(i)
        for i in range(total):
            msg = mq.pop_nowait()
            assert msg["message"] == i
            mq.acknowledge(msg)
            mq.delete_result(msg)
        etime = time.time()
        rate = total / (etime - stime)
        assert rate > 1000

    def test06(self):
        data1 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel, default_timeout=1)
        msg1 = mq.push(data1)
        msg2 = mq.pop_nowait()
        assert msg1["id"] == msg2["id"]

        time.sleep(3)

        count = mq.recover()
        assert count >= 1
        
        msg3 = mq.pop_nowait()
        assert msg3["id"] == msg1["id"]
        assert mq.acknowledge(msg3["id"])

        mq.delete_result(msg1)

    def test07(self):
        data1 = str(uuid.uuid4())
        result1 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel)
        msg1 = mq.push(data1)
        msg2 = mq.pop_nowait()
        assert msg1["id"] == msg2["id"]
        assert mq.acknowledge(msg2, result1)
        msg3 = mq.get_result_nowait(msg2)
        assert msg3["result"]["result_data"] == result1
        assert msg3["result"]["success"]
        assert msg3["result"]["error_code"] == 0
        assert msg3["result"]["error_message"] == "OK"
        mq.delete_result(msg1)

    def test08(self):
        data1 = str(uuid.uuid4())
        result1 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel)
        msg1 = mq.push(data1)
        msg2 = mq.pop_nowait()
        mq.conn.delete(mq.channel_running_ids_key) # delete running ids key
        assert mq.acknowledge(msg2, result1)
        msg3 = mq.get_result_nowait(msg2)
        assert msg3["result"]["result_data"] == result1
        assert msg3["result"]["success"]
        assert msg3["result"]["error_code"] == 0
        assert msg3["result"]["error_message"] == "OK"
        mq.delete_result(msg1)

    def test09(self):
        data1 = str(uuid.uuid4())
        result1 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel)
        msg1 = mq.push(data1)
        msg2 = mq.pop_nowait()
        mq.conn.delete(mq.channel_running_msgs_key) # delete running msgs key
        flag = mq.acknowledge(msg2, result1)
        msg3 = mq.get_result_nowait(msg2)
        assert msg3["result"]["result_data"] == result1
        assert msg3["result"]["success"]
        assert msg3["result"]["error_code"] == 0
        assert msg3["result"]["error_message"] == "OK"
        mq.delete_result(msg1)

    def test10(self):
        data1 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel, default_timeout=1)
        msg1 = mq.push(data1)
        msg2 = mq.pop_nowait()
        assert msg1["id"] == msg2["id"]

        time.sleep(3)

        count = mq.recover(msg1)
        assert count == 1
        
        msg3 = mq.pop_nowait()
        assert msg3["id"] == msg1["id"]
        assert mq.acknowledge(msg3["id"])

        mq.delete_result(msg1)
    
    def test11(self):
        data1 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel, default_timeout=1)
        msg1 = mq.push(data1)
        assert mq.recover(msg1) == 0

    def test12(self):
        data1 = str(uuid.uuid4())
        data2 = str(uuid.uuid4())
        mq = MessageQueue(self.conn, channel=self.channel, default_timeout=1)
        mq.push(data1)
        mq.push(data2, high_priority=True)
        msg1 = mq.pop_nowait()
        msg2 = mq.pop_nowait()
        assert msg1["message"] == data2
        assert msg2["message"] == data1
