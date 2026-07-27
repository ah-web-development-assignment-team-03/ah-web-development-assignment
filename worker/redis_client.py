import json
import os

import redis

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
TASK_QUEUE = "xray:task_queue"
RESULT_CHANNEL_PREFIX = "xray:result:"


class WorkerRedisClient:
    def __init__(self):
        self._client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
        )

    def dequeue_task(self) -> dict | None:
        """BRPOP으로 Queue에서 작업을 가져온다 (무한 대기, timeout=0)."""
        result = self._client.brpop(TASK_QUEUE, timeout=0)
        if result is None:
            return None
        _, value = result
        return json.loads(value)

    def publish_result(self, task_id: str, result: dict) -> None:
        """추론 결과를 xray:result:{task_id} 채널로 Publish."""
        channel = f"{RESULT_CHANNEL_PREFIX}{task_id}"
        self._client.publish(channel, json.dumps(result))
