# app/core/security.py
"""비밀번호 해싱/검증 공통 모듈.

NFR-USER-002 백엔드 대응: 비밀번호는 평문으로 저장하지 않는다.
회원가입(해싱)과 로그인(검증)에서 공통으로 사용한다.
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """평문 비밀번호를 bcrypt 해시로 변환한다."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호가 저장된 해시와 일치하는지 검증한다. (로그인 API에서 사용)"""
    return pwd_context.verify(plain_password, hashed_password)
