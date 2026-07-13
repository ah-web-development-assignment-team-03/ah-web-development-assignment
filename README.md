# AH Web Development Assignment

AH 웹 개발 과제 공식 레포지토리입니다.

---

## 기술 스택

**Backend**
- Python
- FastAPI
- SQLAlchemy (ORM)
- Alembic (DB 마이그레이션)
- pydantic-settings

**Frontend**
- HTML / CSS / JavaScript

---

## 프로젝트 구조

```
ah-web-development-assignment/
├── .env.example                # 환경 변수 예시 파일
├── .github/
│   ├── ISSUE_TEMPLATE/         # 이슈 템플릿 모음
│   └── PULL_REQUEST_TEMPLATE.md
├── alembic/
│   ├── env.py                  # Alembic 마이그레이션 환경 설정
│   └── script.py.mako          # 마이그레이션 파일 템플릿
├── alembic.ini                 # Alembic 설정 파일
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── apis/                   # API 라우터
│   ├── core/
│   │   ├── config.py           # 앱 환경 변수 설정 (pydantic-settings)
│   │   └── db/                 # DB 연결 및 Base 선언
│   │       ├── databases.py    # DB 세션 설정
│   │       └── models.py       # SQLAlchemy Base 모델
│   ├── models/                 # SQLAlchemy ORM 모델
│   ├── repositories/           # DB 접근 계층 (Repository 패턴)
│   ├── schemas/                # 요청/응답 스키마 (Pydantic)
│   └── services/               # 비즈니스 로직 계층
├── docs/
│   └── 1일차_team_rules.md
├── docker-compose.yml          # Docker 컨테이너 설정
├── pyproject.toml              # 프로젝트 의존성 및 설정
├── static/
│   ├── index.html              # 메인 HTML 페이지
│   ├── app.js                  # 프론트엔드 앱 진입점 및 상태 관리
│   ├── apis.js                 # API 호출 함수 모음
│   ├── pages.js                # 페이지 렌더링 로직
│   ├── utils.js                # 공통 유틸리티 함수
│   ├── style.css               # 스타일시트
│   └── templates/              # HTML 페이지 템플릿
│       ├── admin-users.html
│       ├── home.html
│       ├── login.html
│       ├── my-page.html
│       ├── patient-create.html
│       ├── patient-detail.html
│       ├── patients.html
│       ├── record-create.html
│       ├── record-detail.html
│       └── signup.html
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
  ┌─────▼──────────┐
  │  core/db/      │  ← DB 세션 및 Base 설정
  └─────┬──────────┘
        │
   [Database]
```

## Alembic Migration Guide

이 프로젝트는 데이터베이스 마이그레이션을 위해 Alembic을 사용합니다.

### 1. 마이그레이션 파일 생성 (자동 생성)
모델(`app/models/`)이 변경된 경우 다음 명령어를 실행하여 마이그레이션 파일을 생성합니다.
```bash
uv run alembic revision --autogenerate -m "변경 내용 설명"
```

### 2. 데이터베이스에 반영
생성된 마이그레이션을 데이터베이스에 적용하려면 다음 명령어를 실행합니다.
```bash
uv run alembic upgrade head
```

### 3. 이전 상태로 되돌리기 (Rollback)
마지막 마이그레이션을 취소하려면 다음 명령어를 실행합니다.
```bash
uv run alembic downgrade -1
```
