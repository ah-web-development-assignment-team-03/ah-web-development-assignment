import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, ConfigDict
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
