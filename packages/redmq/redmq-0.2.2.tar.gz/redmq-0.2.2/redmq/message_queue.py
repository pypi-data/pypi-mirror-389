
import re
import uuid
import json
import time
import random
import logging
import threading

import bizerror
import requests

from .lock import RedisLock

logger = logging.getLogger(__name__)

# #############################################################################
# 从队列中取出一条消息
# 1. 将msgid放在channel_running_ids的排序集中，以便能在消息处理超时时回收该消息。
# 2. 将msg体放在channel_running_msgs的字典中，以便能回收该消息。
# #############################################################################
REDMQ_MESSAGE_QUEUE_POP_MSG = """
    local msgs = redis.call("LPOP", KEYS[1], 1)
    if msgs ~= false then
        local data = cjson.decode(msgs[1])
        local msgid = data["id"]
        local timeout = data["timeout"]
        local nowtimes = redis.call('TIME')
        local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
        data["start_time"] = nowtime
        data["recovery_time"] = nowtime + timeout
        local new_data_value = cjson.encode(data)
        redis.call("zadd", KEYS[2], data["recovery_time"], msgid)
        redis.call("hset", KEYS[3], msgid, new_data_value)
        return new_data_value
    else
        return nil
    end
"""

# #############################################################################
# 从running库中回收指定的1条消息
# #############################################################################
REDMQ_MESSAGE_QUEUE_RECOVER_MSG = """
    local nowtimes = redis.call('TIME')
    local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
    local data = redis.call("HGET", KEYS[2], ARGV[1])
    local flag1 = false
    if data ~= false then
        data = cjson.decode(data)
        if data["retry"] ~= nil then
            data["retry"] = data["retry"] + 1
        else
            data["retry"] = 1
        end
        data["retry_time"] = nowtime
        local new_data = cjson.encode(data)
        local push_result = redis.call("RPUSH", KEYS[3], new_data)
        if push_result == 1 then
            flag1 = true
        end
    end
    redis.call("ZREM", KEYS[1], ARGV[1])
    redis.call("HDEL", KEYS[2], ARGV[1])
    if flag1 then
        return 1
    else
        return 0
    end
"""

# #############################################################################
# 从running库中回收所有超时消息
# #############################################################################
REDMQ_MESSAGE_QUEUE_RECOVER_MSGS = """
    local nowtimes = redis.call('TIME')
    local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
    local msgids = redis.call("ZRANGEBYSCORE", KEYS[1], 0, nowtimes[1])
    local counter = 0
    for k, v in ipairs(msgids) do
        local data = redis.call("HGET", KEYS[2], v)
        data = cjson.decode(data)
        if data["retry"] ~= nil then
            data["retry"] = data["retry"] + 1
        else
            data["retry"] = 1
        end
        data["retry_time"] = nowtime
        local new_data = cjson.encode(data)
        redis.call("RPUSH", KEYS[3], new_data)
        redis.call("ZREM", KEYS[1], v)
        redis.call("HDEL", KEYS[2], v)
        counter = counter + 1
    end
    return counter
"""

# #############################################################################
# 确认消息已正确处理，并提交结果
# 1. 保存结果信息
# 2. 从running库中删除消息记录
# #############################################################################
REDMQ_MESSAGE_QUEUE_ACKNOWLEDGE = """
    local result = cjson.decode(ARGV[2])
    local nowtimes = redis.call('TIME')
    local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
    local data = redis.call("HGET", KEYS[2], ARGV[1])
    if data ~= false then
        data = cjson.decode(data)
    else
        data = {}
        data["id"] = ARGV[1]
        data["meta_broken"] = true
    end
    data["acknowledged_time"] = nowtime
    data["result"] = result
    local new_data = cjson.encode(data)
    local flag1 = redis.call("SET", KEYS[3], new_data)
    local flag2 = redis.call("EXPIRE", KEYS[3], ARGV[3])
    local flag3 = redis.call("ZREM", KEYS[1], ARGV[1])
    local flag4 = redis.call("HDEL", KEYS[2], ARGV[1])
    if flag1 ~= nil and flag1["ok"] == "OK" and flag2 == 1 then
        return 1
    else
        return 0
    end
"""

class MessageQueue(object):

    def __init__(self, 
            conn, 
            channel="default",
            channel_prefix="redmq:message_queue:channels:",
            channel_running_msgs_prefix="redmq:message_queue:running:msgs:",
            channel_running_ids_prefix="redmq:message_queue:running:ids:",
            channel_results_prefix="redmq:message_queue:results:",
            result_timeout=60*60, # keep the result in redis for one hour by default.
            default_timeout=60*5, # msg executing timeout. If a worker fetched a msg, it must handle the msg within the `timeout` seconds.
            ):
        self.conn = conn
        self.channel = channel
        self.channel_key = channel_prefix + channel
        self.channel_running_msgs_key = channel_running_msgs_prefix + channel
        self.channel_running_ids_key = channel_running_ids_prefix + channel
        self.channel_results_prefix = channel_results_prefix
        self.default_timeout = default_timeout
        self.result_timeout = result_timeout

    def push(self, message, timeout=None, high_priority=False):
        if timeout is None:
            timeout = self.default_timeout
        data = {
            "id": str(uuid.uuid4()),
            "create_time": time.time(),
            "timeout": timeout,
            "message": message,
            "retry": 0,
            "retry_time": None,
            "meta_broken": False,
        }
        if high_priority:
            self.conn.lpush(self.channel_key, json.dumps(data))
        else:
            self.conn.rpush(self.channel_key, json.dumps(data))
        return data

    def pushwait(self, message, timeout=None, high_priority=True, wait_timeout=60, pull_result_interval=0.1):
        stime = time.time()
        msg = self.push(message, timeout=timeout, high_priority=high_priority)
        time.sleep(random.random()/5)
        while True:
            if time.time() - stime > wait_timeout:
                return msg
            result = self.get_result_nowait(msg)
            if result:
                return result
            time.sleep(pull_result_interval + random.random()/10)

    def pop_nowait(self):
        data = self.conn.eval(
            REDMQ_MESSAGE_QUEUE_POP_MSG,
            3,
            self.channel_key,
            self.channel_running_ids_key,
            self.channel_running_msgs_key,
            )
        if data:
            return json.loads(data)
        else:
            return None

    def pop(self, timeout=5, pop_interval=0.5):
        stime = time.time()
        while True:
            if timeout > 0:
                if time.time() - stime > timeout:
                    return None
            result = self.pop_nowait()
            if result:
                return result
            time.sleep(pop_interval + random.random()/10)

    def recover(self, msgid=None):
        if isinstance(msgid, dict):
            msgid = msgid["id"]
        if msgid is None:
            return self.conn.eval(
                REDMQ_MESSAGE_QUEUE_RECOVER_MSGS,
                3,
                self.channel_running_ids_key,
                self.channel_running_msgs_key,
                self.channel_key,
                )
        else:
            return self.conn.eval(
                REDMQ_MESSAGE_QUEUE_RECOVER_MSG,
                3,
                self.channel_running_ids_key,
                self.channel_running_msgs_key,
                self.channel_key,
                msgid,
            )

    def acknowledge(self, msgid, result_data=None, success=None, error_code=None, error_message=None):
        if isinstance(msgid, dict):
            if success is None:
                success = msgid.get("success", True)
            if result_data is None:
                result_data = msgid.get("result_data", None)
            if error_code is None:
                error_code = msgid.get("error_code", 0)
            if error_message is None:
                error_message = msgid.get("error_message", None)
            msgid = msgid["id"]
        if success is None:
            success = True
        if error_code is None:
            error_code = 0
        if error_message is None:
            error_message = "OK"
        result_data = json.dumps({
            "success": success,
            "error_code": error_code,
            "error_message": error_message,
            "result_data": result_data,
        })
        flag = self.conn.eval(
            REDMQ_MESSAGE_QUEUE_ACKNOWLEDGE,
            3,
            self.channel_running_ids_key,
            self.channel_running_msgs_key,
            self.channel_results_prefix + msgid,
            msgid,
            result_data,
            self.result_timeout,
            )
        if flag == 0:
            return False
        else:
            return True

    def get_result_nowait(self, msgid):
        if isinstance(msgid, dict):
            msgid = msgid["id"]
        result_key = self.channel_results_prefix + msgid
        result = self.conn.get(result_key)
        if result:
            return json.loads(result)
        else:
            return None

    def delete_result(self, msgid):
        if isinstance(msgid, dict):
            msgid = msgid["id"]
        result_key = self.channel_results_prefix + msgid
        return self.conn.delete(result_key)

class Consumer(object):

    def __init__(self, mq, worker_number=5, worker_recover_interval=5, msg_pop_interval=0.1):
        self.mq = mq
        self.worker_number = worker_number
        self.worker_recover_interval = worker_recover_interval
        self.workers = []
        self.stop_flag = False
        self.msg_pop_interval = msg_pop_interval
        self.class_name = self.__class__.__name__
        self.handlers = {}
        self.setup()

    def setup(self):
        pass

    def dispatch(self, msg):
        raise NotImplementedError()

    def work_loop(self):
        thread_number = threading.get_ident()
        logger.info(f"{self.class_name} worker loop starting {thread_number}")
        while not self.stop_flag:
            try:
                msg = self.mq.pop_nowait()
            except Exception as error:
                logger.exception("Calling mq.pop_nowait failed in Consumer.work_loop...")
                time.sleep(5*random.random())
                continue
            if msg:
                try:
                    result = self.dispatch(msg)
                    self.mq.acknowledge(msg, result)
                except Exception as error:
                    error = bizerror.BizError(error)
                    try:
                        self.mq.acknowledge(msg, None, success=False, error_code=error.code, error_message=error.message)
                    except Exception as error:
                        logger.exception("Calling mq.acknowledge failed while reporting msg dispatch failed...")
            time.sleep(self.msg_pop_interval + random.random()/10)
        logger.info(f"{self.class_name} worker loop ended {thread_number}.")

    def recover_loop(self):
        thread_number = threading.get_ident()
        logger.info(f"{self.class_name} recover loop starting {thread_number}")
        lock_name = f"{self.class_name}:locks:{self.mq.channel}"
        while not self.stop_flag:
            with RedisLock(self.mq.conn, lock_name) as locked:
                if locked:
                    result = self.mq.recover()
                    logger.info(f"{self.class_name}.recover result: {result}")
            time.sleep(self.worker_recover_interval + random.random())

    def start(self):
        self.workers = []
        self.stop_flag = False

        self.recover_worker = threading.Thread(target=self.recover_loop)
        self.recover_worker.setDaemon(True)
        self.recover_worker.start()

        for _ in range(self.worker_number):
            worker = threading.Thread(target=self.work_loop)
            worker.setDaemon(True)
            worker.start()
            self.workers.append(worker)

    def stop(self):
        self.stop_flag = True

    def wait(self):
        for worker in self.workers:
            worker.join()

    def register_handler(self, handler_name, handler):
        self.handlers[handler_name] = handler

    def dispatch(self, msg):
        data = msg["message"]
        handler_name = data.get("handler", "")
        if not handler_name:
            raise bizerror.BadParameter("A valid msg must be a dict with handler field...")
        if not handler_name in self.handlers:
            raise bizerror.BadParameter(f"Msg's handler {handler_name} is not registered...")
        handler = self.handlers[handler_name]
        return handler(msg)

class MessageHandlerBase(object):
    
    def handle(self, msg):
        raise NotImplementedError()

    def __call__(self, msg):
        return self.handle(msg)

class PingPongHandler(MessageHandlerBase):

    name = "pingpong"

    def handle(self, msg):
        return "pong"

class RequestsHandler(MessageHandlerBase):

    name = "requests"

    default_allowed_methods = []
    default_allowed_urls = [".+"]

    def __init__(self, allowed_methods=None, allowed_urls=None):
        self.allowed_methods = allowed_methods or self.default_allowed_methods
        self.allowed_urls = allowed_urls or self.default_allowed_urls
        self.class_name = self.__class__.__name__

    def handle(self, msg):
        logger.info(f"{self.class_name} handling start, msg={msg}...")
        data = msg["message"]
        if not isinstance(data, dict):
            raise bizerror.BadParameterType("A validate Request Msg must be a dict with url field...")
        method = data.get("method", "GET")
        url = data.get("url", "")
        if not url:
            raise bizerror.MissingParameter("url field missing in Request msg...")
        if not self.check_method(method):
            raise bizerror.AccessDenied(f"method {method} is not allowed...")
        if not self.check_url(url):
            raise bizerror.AccessDenied(f"url {url} is not allowed...")
        params = data.get("params", {})
        headers = data.get("headers", {})
        cookies = data.get("cookies", {})
        timeout = data.get("timeout", None)
        json_data = data.get("json", {})
        response = requests.request(method, url, params=params, headers=headers, cookies=cookies, timeout=timeout, json=json_data)
        result = response.status_code, response.text
        logger.info(f"{self.class_name} handling done, msg={msg}, result={result}.")
        return result

    def check_method(self, method):
        if not self.allowed_methods:
            return True
        if method.upper() in self.allowed_methods:
            return True
        return False
    
    def check_url(self, url):
        for url_pattner in self.allowed_urls:
            if re.findall(url_pattner, url):
                return True
        return False

class RequestsConsumer(Consumer):

    def __init__(self, mq, worker_number=5, worker_recover_interval=5, msg_pop_interval=0.1, allowed_methods=None, allowed_urls=None):
        self.allowed_methods = allowed_methods
        self.allowed_urls = allowed_urls
        super().__init__(mq, worker_number, worker_recover_interval, msg_pop_interval)

    def setup(self):
        super().setup()
        self.requests_handler = RequestsHandler(allowed_methods=self.allowed_methods, allowed_urls=self.allowed_urls)
        self.pingpong_handler = PingPongHandler()
        self.register_handler(self.requests_handler.name, self.requests_handler)
        self.register_handler(self.pingpong_handler.name, self.pingpong_handler)

