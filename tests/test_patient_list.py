import unittest

from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401  # SQLAlchemy 관계 모델 등록
from app.apis import patients as patients_api
from app.core.db.databases import Base, async_get_db
from app.main import app
from app.models.patients import GenderEnum, Patient
from app.services.patient_service import list_patients


class PatientListTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with self.session_factory() as session:
            session.add_all(
                [
                    Patient(name="김하나", age=20, gender=GenderEnum.F, phone="01000000001"),
                    Patient(name="김두리", age=30, gender=GenderEnum.M, phone="01000000002"),
                    Patient(name="이세나", age=40, gender=GenderEnum.F, phone="01000000003"),
                    Patient(name="박네모", age=50, gender=None, phone="01000000004"),
                    Patient(name="최다섯", age=60, gender=GenderEnum.M, phone="01000000005"),
                ]
            )
            await session.commit()

    async def asyncTearDown(self) -> None:
        app.dependency_overrides.clear()
        await self.engine.dispose()

    async def test_filters_name_gender_and_age_with_and_condition(self) -> None:
        async with self.session_factory() as session:
            response = await list_patients(
                session,
                name=" 김 ",
                gender=GenderEnum.M,
                min_age=20,
                max_age=40,
                page=1,
                size=20,
            )

        self.assertEqual(response.total, 1)
        self.assertEqual([patient.name for patient in response.items], ["김두리"])

    async def test_pagination_is_ordered_by_id_and_keeps_total(self) -> None:
        async with self.session_factory() as session:
            response = await list_patients(
                session,
                name=None,
                gender=None,
                min_age=None,
                max_age=None,
                page=2,
                size=2,
            )

        self.assertEqual(response.total, 5)
        self.assertEqual(response.page, 2)
        self.assertEqual(response.size, 2)
        self.assertEqual([patient.id for patient in response.items], [3, 4])
        self.assertIsNone(response.items[1].gender)

    async def test_out_of_range_page_returns_empty_items(self) -> None:
        async with self.session_factory() as session:
            response = await list_patients(
                session,
                name=None,
                gender=None,
                min_age=None,
                max_age=None,
                page=10,
                size=20,
            )

        self.assertEqual(response.items, [])
        self.assertEqual(response.total, 5)

    async def test_invalid_age_range_is_rejected(self) -> None:
        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await list_patients(
                    session,
                    name=None,
                    gender=None,
                    min_age=50,
                    max_age=20,
                    page=1,
                    size=20,
                )

        self.assertEqual(context.exception.status_code, 422)

    async def test_whitespace_only_name_is_rejected(self) -> None:
        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await list_patients(
                    session,
                    name="   ",
                    gender=None,
                    min_age=None,
                    max_age=None,
                    page=1,
                    size=20,
                )

        self.assertEqual(context.exception.status_code, 422)

    async def test_api_returns_list_response(self) -> None:
        async def override_db():
            async with self.session_factory() as session:
                yield session

        async def override_user():
            return object()

        app.dependency_overrides[async_get_db] = override_db
        app.dependency_overrides[patients_api._require_staff_or_admin] = override_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/patients",
                params={"gender": "F", "page": 1, "size": 1},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["gender"], "F")

    async def test_api_rejects_invalid_query_values(self) -> None:
        async def override_user():
            return object()

        app.dependency_overrides[patients_api._require_staff_or_admin] = override_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/patients",
                params={"gender": "UNKNOWN", "page": 0, "size": 101},
            )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
