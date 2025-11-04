
import uuid
import time

REDMQ_LOCK_RELEASE_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then 
        return redis.call("del", KEYS[1]) 
    else 
        return 0
    end
"""

class RedisLock(object):

    def __init__(self, conn, lock_name, worker_name=None, timeout=60, lock_key_prefix="redmq:locks:"):
        self.conn = conn
        self.lock_name = lock_name
        self.worker_name = worker_name or str(uuid.uuid4())
        self.timeout = timeout
        self.lock_key = lock_key_prefix + lock_name

    def acquire(self):
        expire_at = int(time.time() + self.timeout)
        flag = self.conn.setnx(self.lock_key, self.worker_name)
        if flag:
            self.conn.expireat(self.lock_key, expire_at)
        elif self.conn.get(self.lock_key) == self.worker_name:
            flag = True
            self.conn.expireat(self.lock_key, expire_at)
        return flag

    def release(self):
        return self.conn.eval(REDMQ_LOCK_RELEASE_LOCK_SCRIPT, 1, self.lock_key, self.worker_name)

    def __enter__(self, *args, **kwargs):
        return self.acquire()
    
    def __exit__(self, *args, **kwargs):
        self.release()

    def renew(self):
        expire_at = int(time.time() + self.timeout)
        self.conn.expireat(self.lock_key, expire_at)
