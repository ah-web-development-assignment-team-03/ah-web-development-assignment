# app/apis/practice_apis.py
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/practice_api", tags=["practice"])

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

# email 검증용 정규표현식
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class UserCreate(BaseModel):
    # 이름: 최소 2글자, 최대 10글자
    name: str = Field(min_length=2, max_length=10)
    # 나이: 최소 14세 이상
    age: int = Field(ge=14)
    # email: 최대 30자 (중복 검사는 API 함수에서 수행)
    email: str = Field(max_length=30)
    # 비밀번호: 최소 8자, 최대 20자
    password: str = Field(min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        # 정규표현식을 활용한 email 형식 검증
        if not EMAIL_REGEX.match(v):
            raise ValueError("올바른 email 형식이 아닙니다.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # 대소문자 각 1개씩 필수
        if not re.search(r"[A-Z]", v):
            raise ValueError("비밀번호에 대문자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[a-z]", v):
            raise ValueError("비밀번호에 소문자가 최소 1개 포함되어야 합니다.")
        # 특수문자 1개 필수
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>~`_\-+=\[\]\\/;']", v):
            raise ValueError("비밀번호에 특수문자가 최소 1개 포함되어야 합니다.")
        return v


# 회원 정보를 Request Body로 입력받아 user_list에 추가하는 API
@router.post("/users", status_code=201)
def create_user(user: UserCreate):
    # email 중복 불가능
    for u in user_list:
        if u["email"] == user.email:
            raise HTTPException(status_code=400, detail="이미 사용 중인 email입니다.")

    # id는 자동으로 1씩 증가
    new_id = max((u["id"] for u in user_list), default=0) + 1
    new_user = {"id": new_id, **user.model_dump()}
    user_list.append(new_user)
    return new_user
