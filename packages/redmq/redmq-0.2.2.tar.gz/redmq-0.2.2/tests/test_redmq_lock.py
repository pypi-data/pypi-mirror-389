
import threading
import uuid
import time

import unittest

import redis
from redmq.lock import RedisLock

class TestRedmqLock(unittest.TestCase):

    def setUp(self):
        self.conn = redis.Redis("redis")

    def test01(self):
        self.conn.ping()
    
    def test02(self):
        lock_name = str(uuid.uuid4())
        worker_name = str(uuid.uuid4())
        with RedisLock(self.conn, lock_name, worker_name) as locked:
            assert locked
        with RedisLock(self.conn, lock_name, worker_name) as locked:
            assert locked
        with RedisLock(self.conn, lock_name, worker_name) as locked:
            assert locked
        assert len(self.conn.keys(f"redmq:locks:{lock_name}")) == 0

    def test03(self):
        lock_name = str(uuid.uuid4())
        worker_name1 = str(uuid.uuid4())
        worker_name2 = str(uuid.uuid4())
        with RedisLock(self.conn, lock_name, worker_name1) as locked:
            assert locked

            with RedisLock(self.conn, lock_name, worker_name2) as locked:
                assert locked is False
        assert len(self.conn.keys(f"redmq:locks:{lock_name}")) == 0

    def test04(self):
        lock_name = str(uuid.uuid4())
        worker_name1 = str(uuid.uuid4())
        worker_name2 = str(uuid.uuid4())
        with RedisLock(self.conn, lock_name, worker_name1, timeout=2) as locked:
            assert locked
            time.sleep(5)
            with RedisLock(self.conn, lock_name, worker_name2) as locked:
                assert locked is True
        assert len(self.conn.keys(f"redmq:locks:{lock_name}")) == 0

    def test05(self):
        lock_name = str(uuid.uuid4())
        results = []
        def worker(lock_name, results):
            worker_name = str(uuid.uuid4())
            with RedisLock(self.conn, lock_name, worker_name) as locked:
                results.append(locked)
        threads = []
        for _ in range(100):
            thread = threading.Thread(target=worker, args=[lock_name, results])
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        flag = True
        tvalue = 0
        fvalue = 0
        for result in results:
            if result:
                flag = True
                tvalue += 1
            else:
                fvalue += 1
        assert flag
