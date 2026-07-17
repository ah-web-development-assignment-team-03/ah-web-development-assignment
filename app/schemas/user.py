import enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Department, Gender, Role
from app.models.user import User


# --- 프런트엔드 값 (API 경계에서 주고받는 사람이 읽기 쉬운 문자열) ---
class GenderAPI(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class DepartmentAPI(str, enum.Enum):
    DEVELOPER = "developer"
    MEDICAL = "medical team"
    RESEARCHER = "researcher"


class RoleAPI(str, enum.Enum):
    PENDING = "pending"
    STAFF = "staff"
    ADMIN = "admin"


# --- DB Enum ↔ 프런트엔드 값 매핑 (DB Enum 정의는 변경하지 않는다) ---
GENDER_DB_TO_API: dict[Gender, GenderAPI] = {
    Gender.M: GenderAPI.MALE,
    Gender.F: GenderAPI.FEMALE,
}
DEPARTMENT_DB_TO_API: dict[Department, DepartmentAPI] = {
    Department.DEV: DepartmentAPI.DEVELOPER,
    Department.MEDICAL: DepartmentAPI.MEDICAL,
    Department.RESEARCH: DepartmentAPI.RESEARCHER,
}
ROLE_DB_TO_API: dict[Role, RoleAPI] = {
    Role.PENDING: RoleAPI.PENDING,
    Role.STAFF: RoleAPI.STAFF,
    Role.ADMIN: RoleAPI.ADMIN,
}
DEPARTMENT_API_TO_DB: dict[DepartmentAPI, Department] = {
    api: db for db, api in DEPARTMENT_DB_TO_API.items()
}


class MyPageResponse(BaseModel):
    """REQ-USER-006 / 007 응답. 비밀번호·해시는 포함하지 않는다."""

    # 직렬화 시 Enum이 아닌 프런트엔드 문자열 값으로 내려간다.
    model_config = ConfigDict(use_enum_values=True)

    id: int
    email: str
    name: str
    department: DepartmentAPI
    gender: GenderAPI
    phone_number: str
    role: RoleAPI

    @classmethod
    def from_user(cls, user: User) -> "MyPageResponse":
        """User(DB Enum) → 마이페이지 응답(프런트엔드 값)으로 변환한다."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            department=DEPARTMENT_DB_TO_API[user.department],
            gender=GENDER_DB_TO_API[user.gender],
            phone_number=user.phone_number,
            role=ROLE_DB_TO_API[user.role],
        )


class MyInfoUpdateRequest(BaseModel):
    """REQ-USER-007 요청. Partial 수정이라 두 필드 모두 선택 항목이다.

    이름·이메일·성별 등 다른 필드가 포함되어도 무시한다(기본 pydantic 동작).
    """

    department: DepartmentAPI | None = None
    phone_number: str | None = None


class PasswordChangeRequest(BaseModel):
    """REQ-USER-008 요청.

    새 비밀번호 정책 검증은 서비스(change_my_password)에서 수행하며,
    위반 시 400으로 응답한다. (Pydantic validator로 검증하면 422가 나가므로 사용하지 않는다)
    """

    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    """단순 결과 메시지 응답 (예: 비밀번호 변경 완료)."""

    detail: str


class UserDeleteRequest(BaseModel):
    current_password: str = Field(min_length=1)
