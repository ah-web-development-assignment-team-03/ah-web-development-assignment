from pydantic import BaseModel, Field

# 조회 가능 목록 
class User(BaseModel):
    id: int = Field(..., description="회원의 고유 ID")
    name: str = Field(..., min_length=2, max_length=20, description="회원의 이름")
    age: int = Field(..., ge=0, description="회원의 나이")
    email: str = Field(..., min_length=5, max_length=100, description="회원의 이메일 주소")