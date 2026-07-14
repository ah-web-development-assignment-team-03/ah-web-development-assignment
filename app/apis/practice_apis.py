import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional

# Initialize router
router = APIRouter(prefix="/practice_api", tags=["practice"])

# User Database
user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!"
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!"
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@"
    }
]


# 이메일 형식을 검사하기 위한 정규표현식
EMAIL_PATTERN = (
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

# 비밀번호를 검사하기 위한 정규표현식
# 영문 대문자, 소문자, 특수문자를 각각 1개 이상 포함
PASSWORD_PATTERN = (
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9\s]).{8,20}$"
)


# 회원 수정 요청에서 받을 데이터
class UserUpdate(BaseModel):
    # 나이는 입력하지 않아도 되지만 입력한다면 14세 이상
    age: int | None = Field(
        default=None,
        ge=14,
    )

    # 이메일은 입력하지 않아도 되지만 최대 30자
    email: str | None = Field(
        default=None,
        max_length=30,
    )

    # 비밀번호는 입력하지 않아도 되지만 8자 이상 20자 이하
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=20,
    )

    # 이메일 형식 검사
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if re.fullmatch(EMAIL_PATTERN, value) is None:
            raise ValueError("올바른 이메일 형식이 아닙니다.")

        return value

    # 비밀번호 형식 검사
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if re.fullmatch(PASSWORD_PATTERN, value) is None:
            raise ValueError(
                "비밀번호에는 대문자, 소문자, "
                "특수문자가 각각 1개 이상 필요합니다."
            )

        return value


# 회원 수정 API
@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    request: UserUpdate,
):
    # user_list에서 ID가 같은 회원을 찾습니다.
    user = next(
        (
            user
            for user in user_list
            if user["id"] == user_id
        ),
        None,
    )

    # ID가 같은 회원이 없다면 404 오류를 반환합니다.
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다.",
        )

    # Request Body에 실제로 입력된 값만 가져옵니다.
    update_data = request.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    # age, email, password가 모두 입력되지 않았다면
    # 400 Bad Request를 반환합니다.
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="수정할 항목을 하나 이상 입력해야 합니다.",
        )

    # 입력된 내용만 기존 회원 정보에 반영합니다.
    user.update(update_data)

    # 수정 결과를 반환합니다.
    # 비밀번호는 응답에서 제외합니다.
    return {
        "id": user["id"],
        "name": user["name"],
        "age": user["age"],
        "email": user["email"],
    }