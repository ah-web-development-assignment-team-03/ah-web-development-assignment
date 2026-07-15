import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional

# 유저 조회 스키마 정의
from app.apis.schema import User

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

# 모든 회원 조회 api
@router.get(
    "/users",
    summary="모든 회원 조회 api",
    response_model=list[User],
    status_code=200
)
def get_all_users_handler():
    return user_list

# 특정 회원 조회 api
@router.get(
    "/users/{user_id}",
    summary="특정 회원 조회 api",
    response_model=User,
    status_code=200
)
def get_user_handler(
    user_id: int
):
    for user in user_list:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="404 not found")
# API 5: Delete user
@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """회원의 정보를 삭제"""
    global user_list
    for i, user in enumerate(user_list):
        if user["id"] == user_id:
            user_list.pop(i)
            return
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없음")

# 이메일 형식을 검사하기 위한 정규표현식
EMAIL_PATTERN = (
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

# 비밀번호를 검사하기 위한 정규표현식
# 영문 대문자, 소문자, 특수문자를 각각 1개 이상 포함
PASSWORD_PATTERN = (
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9\s]).{8,20}$"
)


# 회원 생성 요청에서 받을 데이터
class UserCreate(BaseModel):
    # 이름은 최소 2글자, 최대 10글자
    name: str = Field(
        min_length=2,
        max_length=10,
    )

    # 나이는 최소 14세 이상
    age: int = Field(
        ge=14,
    )

    # 이메일은 최대 30자 (중복 검사는 API 함수에서 수행)
    email: str = Field(
        max_length=30,
    )

    # 비밀번호는 최소 8자, 최대 20자
    password: str = Field(
        min_length=8,
        max_length=20,
    )

    # 이메일 형식 검사
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if re.fullmatch(EMAIL_PATTERN, value) is None:
            raise ValueError("올바른 이메일 형식이 아닙니다.")

        return value

    # 비밀번호 형식 검사
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if re.fullmatch(PASSWORD_PATTERN, value) is None:
            raise ValueError(
                "비밀번호에는 대문자, 소문자, "
                "특수문자가 각각 1개 이상 필요합니다."
            )

        return value


# 회원 생성 API
@router.post(
    "/users",
    summary="회원 생성 api",
    status_code=201,
)
async def create_user(
    request: UserCreate,
):
    """회원의 정보를 Request Body로 입력받아 user_list에 추가"""
    # 이메일 중복 검사 (중복 불가능)
    for user in user_list:
        if user["email"] == request.email:
            raise HTTPException(
                status_code=400,
                detail="이미 사용 중인 이메일입니다.",
            )

    # id는 자동으로 1씩 증가
    new_id = max(
        (user["id"] for user in user_list),
        default=0,
    ) + 1

    # 새 회원을 user_list에 추가합니다.
    new_user = {
        "id": new_id,
        **request.model_dump(),
    }
    user_list.append(new_user)

    # 생성 결과를 반환합니다.
    # 비밀번호는 응답에서 제외합니다.
    return {
        "id": new_user["id"],
        "name": new_user["name"],
        "age": new_user["age"],
        "email": new_user["email"],
    }


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
