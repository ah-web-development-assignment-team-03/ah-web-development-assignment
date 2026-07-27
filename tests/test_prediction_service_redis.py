import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.redis_client import ResultTimeoutError
from app.services import prediction_service


def _saved_result(*, record_id: int = 1):
    return SimpleNamespace(
        id=10,
        record_id=record_id,
        is_pneumonia=True,
        confidence=87.5,
        heatmap_url=None,
        ai_model=prediction_service.MODEL_TAG,
        created_at=datetime(2026, 7, 27, 12, 0, 0),
    )


class PredictionServiceRedisTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_cached_result_does_not_enqueue_task(self) -> None:
        cached = _saved_result()

        with (
            patch.object(
                prediction_service.medical_record_repository,
                "get_medical_record_by_id",
                AsyncMock(return_value=object()),
            ),
            patch.object(
                prediction_service.prediction_repository,
                "get_xray_image_by_record_id",
                AsyncMock(return_value=SimpleNamespace(image_url="media/xray/test.png")),
            ),
            patch.object(
                prediction_service.prediction_repository,
                "get_cached_result",
                AsyncMock(return_value=cached),
            ),
            patch.object(
                prediction_service.redis_client,
                "enqueue_and_wait",
                AsyncMock(),
            ) as enqueue,
        ):
            response = await prediction_service.run_prediction(AsyncMock(), 1)

        self.assertTrue(response.cached)
        enqueue.assert_not_awaited()

    async def test_enqueues_contract_payload_and_saves_worker_result(self) -> None:
        db = AsyncMock()
        saved = _saved_result()

        async def worker_result(task):
            return {
                "task_id": task["task_id"],
                "status_code": 200,
                "is_pneumonia": True,
                "confidence": 87.5,
                "ai_model": prediction_service.MODEL_TAG,
                "heatmap_url": None,
            }

        with (
            patch.object(
                prediction_service.medical_record_repository,
                "get_medical_record_by_id",
                AsyncMock(return_value=object()),
            ),
            patch.object(
                prediction_service.prediction_repository,
                "get_xray_image_by_record_id",
                AsyncMock(return_value=SimpleNamespace(image_url="media/xray/test.png")),
            ),
            patch.object(
                prediction_service.prediction_repository,
                "get_cached_result",
                AsyncMock(return_value=None),
            ),
            patch.object(
                prediction_service.redis_client,
                "enqueue_and_wait",
                AsyncMock(side_effect=worker_result),
            ) as enqueue,
            patch.object(
                prediction_service.prediction_repository,
                "save_result",
                AsyncMock(return_value=saved),
            ) as save_result,
        ):
            response = await prediction_service.run_prediction(db, 1)

        task = enqueue.await_args.args[0]
        self.assertEqual(
            set(task),
            {"task_id", "image_path", "model_name"},
        )
        self.assertEqual(task["model_name"], prediction_service.MODEL_TAG)
        self.assertTrue(task["image_path"].endswith("media/xray/test.png"))
        save_result.assert_awaited_once()
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(saved)
        self.assertFalse(response.cached)

    async def test_worker_error_status_is_returned_as_http_error(self) -> None:
        async def worker_error(task):
            return {
                "task_id": task["task_id"],
                "status_code": 422,
                "detail": "이미지를 읽을 수 없습니다.",
            }

        with self._prediction_dependencies(worker_error):
            with self.assertRaises(HTTPException) as context:
                await prediction_service.run_prediction(AsyncMock(), 1)

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(context.exception.detail, "이미지를 읽을 수 없습니다.")

    async def test_worker_timeout_returns_504(self) -> None:
        with self._prediction_dependencies(ResultTimeoutError()):
            with self.assertRaises(HTTPException) as context:
                await prediction_service.run_prediction(AsyncMock(), 1)

        self.assertEqual(context.exception.status_code, 504)

    async def test_redis_connection_failure_returns_503(self) -> None:
        with self._prediction_dependencies(RedisConnectionError()):
            with self.assertRaises(HTTPException) as context:
                await prediction_service.run_prediction(AsyncMock(), 1)

        self.assertEqual(context.exception.status_code, 503)

    def _prediction_dependencies(self, worker_side_effect):
        return _PatchGroup(
            patch.object(
                prediction_service.medical_record_repository,
                "get_medical_record_by_id",
                AsyncMock(return_value=object()),
            ),
            patch.object(
                prediction_service.prediction_repository,
                "get_xray_image_by_record_id",
                AsyncMock(return_value=SimpleNamespace(image_url="media/xray/test.png")),
            ),
            patch.object(
                prediction_service.prediction_repository,
                "get_cached_result",
                AsyncMock(return_value=None),
            ),
            patch.object(
                prediction_service.redis_client,
                "enqueue_and_wait",
                AsyncMock(side_effect=worker_side_effect),
            ),
        )


class _PatchGroup:
    def __init__(self, *patchers):
        self.patchers = patchers

    def __enter__(self):
        return [patcher.start() for patcher in self.patchers]

    def __exit__(self, exc_type, exc_value, traceback):
        for patcher in reversed(self.patchers):
            patcher.stop()


if __name__ == "__main__":
    unittest.main()
