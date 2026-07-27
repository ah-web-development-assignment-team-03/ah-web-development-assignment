import asyncio
import json
import os
from collections.abc import Mapping
from typing import Any

from redis.asyncio import Redis


TASK_QUEUE = "xray:task_queue"
RESULT_CHANNEL_PREFIX = "xray:result:"
DEFAULT_RESULT_TIMEOUT_SECONDS = 60.0


class ResultTimeoutError(TimeoutError):
    """Worker 결과가 제한 시간 안에 도착하지 않은 경우."""


def _redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://redis:6379/0")


def _result_timeout_seconds() -> float:
    value = os.getenv(
        "PREDICTION_TIMEOUT_SECONDS",
        str(DEFAULT_RESULT_TIMEOUT_SECONDS),
    )
    try:
        timeout = float(value)
    except ValueError:
        return DEFAULT_RESULT_TIMEOUT_SECONDS
    return timeout if timeout > 0 else DEFAULT_RESULT_TIMEOUT_SECONDS


redis = Redis.from_url(_redis_url(), decode_responses=True)


async def publish_task(task: Mapping[str, Any]) -> None:
    """AI 추론 작업을 Worker가 소비하는 Queue에 등록한다."""

    await redis.lpush(
        TASK_QUEUE,
        json.dumps(dict(task), ensure_ascii=False),
    )


async def _wait_for_message(pubsub, channel: str, timeout: float) -> dict[str, Any]:
    try:
        async with asyncio.timeout(timeout):
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is None or message["channel"] != channel:
                    continue

                payload = json.loads(message["data"])
                if not isinstance(payload, dict):
                    raise ValueError("Redis 결과 메시지는 JSON 객체여야 합니다.")
                return payload
    except TimeoutError as exc:
        raise ResultTimeoutError(
            f"Worker 결과 대기 시간이 {timeout:g}초를 초과했습니다."
        ) from exc


async def subscribe_result(
    task_id: str,
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    """task_id 전용 채널을 구독하여 Worker 결과를 한 건 수신한다."""

    channel = f"{RESULT_CHANNEL_PREFIX}{task_id}"
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(channel)
        return await _wait_for_message(
            pubsub,
            channel,
            timeout if timeout is not None else _result_timeout_seconds(),
        )
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


async def enqueue_and_wait(
    task: Mapping[str, Any],
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    """결과 채널을 먼저 구독한 뒤 작업을 등록하여 메시지 유실을 막는다."""

    task_id = str(task["task_id"])
    channel = f"{RESULT_CHANNEL_PREFIX}{task_id}"
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(channel)
        await publish_task(task)
        return await _wait_for_message(
            pubsub,
            channel,
            timeout if timeout is not None else _result_timeout_seconds(),
        )
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
