
import redis
import logging

from fastutils import funcutils
from fastutils import logutils
from daemon_application import DaemonApplication

from .message_queue import RequestsConsumer
from .message_queue import MessageQueue
from .schedule import Schedule
from .schedule import Scheduler

logger = logging.getLogger(__name__)

class RequestsServer(DaemonApplication):
    
    def main(self):
        logutils.setup(**self.config)
        logger.info(f"{self.__class__.__name__} starting...")

        self.redis_config = self.config.get("redis", "redis://localhost:6379/0")
        self.channel = self.config.get("channel", "default")
        self.mq_config = self.config.get("mq", {})
        self.woker_config = self.config.get("worker", {})
        self.schedule_config = self.config.get("schedule", {})

        if isinstance(self.redis_config, str):
            self.conn = redis.Redis.from_url(self.redis_config)
        else:
            self.conn = funcutils.call_with_inject(redis.Redis, self.redis_config)

        self.mq_config["conn"] = self.conn
        self.mq_config["channel"] = self.channel
        self.mq = funcutils.call_with_inject(MessageQueue, self.mq_config)

        self.woker_config["mq"] = self.mq
        self.consumer = funcutils.call_with_inject(RequestsConsumer, self.woker_config)
        self.consumer.start()

        self.schedule_config["conn"] = self.conn
        self.schedule_config["channel"] = self.channel
        self.schedule = funcutils.call_with_inject(Schedule, self.schedule_config)
        self.scheduler = Scheduler(self.schedule, self.mq)
        self.scheduler.start()

        self.scheduler.wait()
        self.consumer.wait()

        logger.info("{self.__class__.__name__} ended.")

application = RequestsServer()
application_ctrl = application.get_controller()

if __name__ == "__main__":
    application_ctrl()
