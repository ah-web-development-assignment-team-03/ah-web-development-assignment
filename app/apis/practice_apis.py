import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, ConfigDict
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
