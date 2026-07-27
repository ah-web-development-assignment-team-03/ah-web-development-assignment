import logging
import sys
import time
from http import HTTPStatus

from worker.model import predict
from worker.redis_client import WorkerRedisClient

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_RECONNECT_DELAY = 5


def _process_task(client: WorkerRedisClient, task: dict) -> None:
    task_id = task.get("task_id")
    image_path = task.get("image_path")
    logger.info("task_id=%s image=%s", task_id, image_path)

    try:
        prediction = predict(image_path)
        result = {
            "task_id": task_id,
            "is_pneumonia": prediction["is_pneumonia"],
            "confidence": prediction["confidence"],
            "ai_model": prediction["ai_model"],
            "heatmap_url": prediction.get("heatmap_url"),
        }
        client.publish_result(task_id, result)
        logger.info(
            "task_id=%s done  is_pneumonia=%s confidence=%s",
            task_id, result["is_pneumonia"], result["confidence"],
        )
    except Exception as exc:
        logger.error("task_id=%s failed: %s", task_id, exc, exc_info=True)
        client.publish_result(task_id, {"task_id": task_id, "status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "detail": str(exc)})


def run() -> None:
    logger.info("AI Worker starting...")
    while True:
        try:
            client = WorkerRedisClient()
            logger.info("Connected to Redis. Waiting for tasks...")
            while True:
                task = client.dequeue_task()
                if task is None:
                    continue
                _process_task(client, task)
        except Exception as exc:
            logger.error("Worker error: %s. Reconnecting in %ds...", exc, _RECONNECT_DELAY)
            time.sleep(_RECONNECT_DELAY)


if __name__ == "__main__":
    run()
