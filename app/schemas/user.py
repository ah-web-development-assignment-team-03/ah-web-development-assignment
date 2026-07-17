from pydantic import BaseModel, Field


class UserDeleteRequest(BaseModel):
    current_password: str = Field(min_length=1)
