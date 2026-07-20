# app/schemas/user.py
"""User API 요청/응답 스키마.

명세서 기준: REQ-USER-001 회원가입
- 요청: email, password, name, department, gender, phone_number
- 응답: 비밀번호(해시 포함)를 절대 포함하지 않는다 (NFR-USER-002)
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Department, Gender, Role


class UserCreate(BaseModel):
    """회원가입 요청 Body."""

    email: EmailStr = Field(..., max_length=255, description="사용자 이메일")
    password: str = Field(
        ..., min_length=8, description="사용자 비밀번호 (8자 이상)"
    )
    name: str = Field(..., min_length=1, max_length=20, description="사용자 이름")
    department: Department = Field(..., description="부서 (MEDICAL/DEV/RESEARCH)")
    gender: Gender = Field(..., description="성별 (M/F)")
    phone_number: str = Field(..., max_length=20, description="휴대폰 번호")


class UserResponse(BaseModel):
    """회원가입 성공 응답 (201 Created).

    hashed_password는 의도적으로 제외한다.
    """

    model_config = ConfigDict(from_attributes=True)  # SQLAlchemy 객체 -> 스키마 변환

    id: int
    email: EmailStr
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: Role
    is_active: bool
