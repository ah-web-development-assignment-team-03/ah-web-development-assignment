# AH Web Development Assignment

AH 웹 개발 과제 공식 레포지토리입니다.

---

## 기술 스택

**Backend**
- Python
- SQLAlchemy (ORM)
- Alembic (DB 마이그레이션)
- python-dotenv

**Frontend**
- HTML / CSS / JavaScript (Vanilla)

---

## 프로젝트 구조

```
ah-web-development-assignment/
├── alembic/
│   └── env.py              # Alembic 마이그레이션 환경 설정
│
├── app/
│   ├── core/               # 앱 설정, 공통 유틸리티
│   ├── db/                 # DB 연결 및 Base 선언 (app/db/base.py)
│   ├── models/             # SQLAlchemy ORM 모델
│   ├── repositories/       # DB 접근 계층 (Repository 패턴)
│   ├── schemas/            # 요청/응답 스키마 (Pydantic 등)
│   └── services/           # 비즈니스 로직 계층
│
├── static/
│   ├── index.html          # 메인 HTML 페이지
│   ├── index.js            # 프론트엔드 상태 관리 및 로직
│   └── style.css           # 스타일시트
│
└── README.md
```

---

## 아키텍처

이 프로젝트는 **레이어드 아키텍처(Layered Architecture)** 를 기반으로 합니다.

```
[Frontend: static/]
        ↕  HTTP
[API Layer: app/]
        │
  ┌─────▼──────┐
  │  schemas/  │  ← 요청/응답 데이터 검증
  └─────┬──────┘
        │
  ┌─────▼──────┐
  │  services/ │  ← 비즈니스 로직
  └─────┬──────┘
        │
  ┌─────▼──────────┐
  │ repositories/  │  ← DB 접근 (CRUD)
  └─────┬──────────┘
        │
  ┌─────▼──────┐
  │  models/   │  ← SQLAlchemy ORM 모델
  └─────┬──────┘
        │
   [Database]
```

---

## 환경 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 항목을 설정합니다.

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

---

## 시작하기

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. DB 마이그레이션 실행
alembic upgrade head

# 3. 서버 실행
python -m app
```

---

## DB 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "migration message"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1
```
