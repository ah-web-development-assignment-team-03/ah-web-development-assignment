# AI Health - 폐렴 예측 및 환자 진료 기록 관리 서비스

의료진이 환자와 진료 기록을 관리하고 흉부 X-ray 이미지를 기반으로 폐렴 예측 결과를 확인할 수 있는 AI 웹 서비스입니다.

이 문서는 Stage 4 과제의 요구사항에 따라 팀 규칙 수립부터 API·AI 워커 구현, 아키텍처 설계, Docker 인프라와 QA까지 프로젝트 진행 과정을 종합하여 정리한 문서입니다.

## 1. 프로젝트 개요

### 1.1 목표

- 의료진이 환자 정보와 진료 기록을 한 곳에서 관리할 수 있도록 합니다.
- 진료 기록에 등록된 흉부 X-ray 이미지로 폐렴 여부와 신뢰도를 예측합니다.
- 인증·인가를 적용하여 일반 의료진과 관리자 기능을 구분합니다.
- API 서버와 무거운 AI 추론 작업을 분리하여 동시 요청에 대응합니다.
- Docker Compose로 애플리케이션과 인프라를 동일한 환경에서 실행할 수 있도록 구성합니다.

### 1.2 주요 기능

| 영역 | 주요 기능 |
|---|---|
| 인증 | 로그인, 토큰 갱신, 로그아웃 |
| 회원 | 회원가입, 마이페이지 조회·수정, 비밀번호 변경, 회원 탈퇴 |
| 관리자 | 회원 목록 조회, 회원 권한 변경 |
| 환자 | 환자 등록·목록·상세·수정·삭제, 검색·필터·페이지네이션 |
| 진료 기록 | 진료 기록 및 X-ray 이미지 등록, 목록·상세 조회 |
| AI 예측 | 폐렴 예측 요청, 캐시된 결과 재사용, 예측 결과 목록 조회 |
| 웹 화면 | SPA 방식의 로그인, 환자·진료 기록·관리자 화면 |

## 2. 기술 스택

| 구분 | 기술 |
|---|---|
| Backend | Python 3.13, FastAPI, Pydantic |
| Database | MySQL 8.0, SQLAlchemy Async ORM, Alembic |
| Authentication | JWT, HttpOnly Cookie, 역할 기반 접근 제어 |
| AI | PyTorch, Torchvision, DenseNet121 5-fold Ensemble |
| Message Queue | Redis List, Redis Pub/Sub |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Infrastructure | Docker, Docker Compose |
| Test | unittest, HTTPX, SQLite in-memory DB |
| Package Management | uv |

## 3. 프로젝트 과정 총정리

### 3.1 Team Rule 정의

프로젝트 시작 시 협업 기준을 먼저 맞추기 위해 다음 규칙을 정의했습니다.

- 평일 코어 타임 운영과 진행 상황 공유
- 회의 전 안건 작성 및 회의 후 결정 사항 기록
- 기능 단위 브랜치와 이슈 번호 기반 커밋 메시지 사용
- Pull Request에 작업 내용, 테스트 방법, 관련 이슈 작성
- 최소 1명 이상의 리뷰 후 병합
- `main` 직접 push 금지 및 충돌 해결 절차 준수
- 코드 작성자가 아닌 코드와 구현 방식 중심으로 리뷰

자세한 내용은 [Team Rules](docs/1일차/1일차_team_rules.md)에서 확인할 수 있습니다.

### 3.2 사용자 요구사항 정의

제공된 사용자 요구사항을 기능 영역별로 분석하고 구현 단위로 나누었습니다.

| 요구사항 영역 | 식별자 예시 | 반영 내용 |
|---|---|---|
| 회원 | `REQ-USER-001` - `REQ-USER-009` | 가입, 인증, 내 정보 관리, 관리자 기능, 탈퇴 |
| 환자 | `REQ-PTNT-001` - `REQ-PTNT-005` | 환자 CRUD, 검색·필터·페이지네이션 |
| 진료 기록 | `REQ-MDR-001` - `REQ-MDR-003` | 진료 기록과 X-ray 등록 및 조회 |
| 폐렴 예측 | `REQ-PRED-001` - `REQ-PRED-002` | 예측 실행, 캐시, 결과 조회 |
| 비기능 | `NFR-*` | 응답 시간, 데이터 검증, 동시 요청 대응 |

요구사항을 분석할 때 정상 흐름뿐 아니라 인증 실패, 권한 부족, 잘못된 입력, 데이터 미존재, 처리 시간 초과와 같은 예외 흐름도 함께 정의했습니다.

### 3.3 API 명세서 작성

구현 전에 각 API의 경로, 권한, 요청·응답 필드, 상태 코드, 오류 응답과 테스트 기준을 문서화했습니다.

- 회원: [회원가입 API](docs/4일차/4일차_회원가입_API_명세서_REQ-USER-001.md), [회원 API 설계](docs/4일차/4일차_USER_API_설계.md), [공통 인증·인가 및 회원 탈퇴](docs/4일차/4일차_공통인증인가_회원탈퇴_설계서.md)
- 환자: [환자 등록·상세 조회](docs/5일차/5일차_환자관리_API_설계_REQ_PTNT_01_03.md), [환자 목록 조회](docs/5일차/5일차_REQ-PTNT-002_환자목록조회_API_명세서.md), [환자 수정·삭제](docs/5일차/5일차_환자관리_API_설계_REQ_PTNT_04_05.md)
- 진료 기록: [진료 기록 등록](docs/5일차/5일차_진료기록등록_API_설계.md), [진료 기록 조회](docs/5일차/5일차_Medical%20Record%20API_설계.md)
- 폐렴 예측: [예측 실행](docs/6일차/6일차_폐렴예측_API_설계_REQ_PRED_001.md), [예측 결과 조회](docs/6일차/6일차_폐렴예측_API_설계.md)

### 3.4 Git & GitHub Branch 전략 구성

`main`과 `develop`을 중심으로 하는 Git Flow를 채택했습니다.

```text
main
 ├── hotfix/*
 └── develop
      ├── feat/*
      ├── fix/*
      ├── docs/*
      └── release/*
```

- `main`: 배포 가능한 안정 버전
- `develop`: 다음 릴리스를 위한 통합 브랜치
- `feat/*`, `fix/*`, `docs/*`: 기능·수정·문서 작업 브랜치
- `release/*`: QA와 릴리스 준비
- `hotfix/*`: 운영 환경의 긴급 수정

작업 브랜치는 `develop`에서 분기하고 Pull Request와 리뷰를 거쳐 다시 `develop`에 병합합니다. 릴리스 준비가 끝난 결과만 `main`으로 승격합니다. 자세한 흐름은 [Git Flow 브랜치 전략](docs/2일차/2일차_git_branch_전략.md)에 정리했습니다.

### 3.5 프로젝트 세팅

FastAPI 프로젝트를 레이어드 아키텍처로 구성하고 `uv`로 의존성을 관리했습니다.

```text
Client
  ↓ HTTP
API Router
  ↓
Service
  ↓
Repository
  ↓
SQLAlchemy Model
  ↓
MySQL
```

- `apis`: HTTP 요청·응답과 상태 코드 처리
- `schemas`: Pydantic 요청·응답 데이터 검증
- `services`: 비즈니스 규칙과 트랜잭션 흐름
- `repositories`: 데이터베이스 조회·저장
- `models`: SQLAlchemy ORM 모델
- `core`: 환경 설정, DB 연결, 보안, Redis 클라이언트

데이터베이스 스키마 변경은 Alembic 마이그레이션으로 관리했습니다. 프로젝트 구조와 마이그레이션 과정은 [프로젝트 구조 분석](docs/3일차/3일차_프로젝트_뜯어보기.md)과 [DB 마이그레이션](docs/3일차/3일차_db_migration.md)에 기록했습니다.

### 3.6 API 및 AI 워커 코드 작성과 병합

기능을 회원, 환자, 진료 기록, 폐렴 예측 단위로 나누어 각 작업 브랜치에서 구현한 뒤 Pull Request를 통해 통합했습니다.

현재 FastAPI 애플리케이션이 제공하는 주요 API는 다음과 같습니다.

| Method | Endpoint | 기능 |
|---|---|---|
| `POST` | `/api/v1/auth/login` | 로그인 |
| `POST` | `/api/v1/auth/refresh` | 액세스 토큰 갱신 |
| `POST` | `/api/v1/auth/logout` | 로그아웃 |
| `POST` | `/api/v1/users` | 회원가입 |
| `GET/PATCH/DELETE` | `/api/v1/users/me` | 내 정보 조회·수정·탈퇴 |
| `PATCH` | `/api/v1/users/me/password` | 비밀번호 변경 |
| `GET` | `/api/v1/admin/users` | 관리자 회원 목록 조회 |
| `PATCH` | `/api/v1/admin/users/{user_id}` | 회원 권한 변경 |
| `GET/POST` | `/api/v1/patients` | 환자 목록·등록 |
| `GET/PATCH/DELETE` | `/api/v1/patients/{patient_id}` | 환자 상세·수정·삭제 |
| `POST/GET` | `/api/v1/patients/{patient_id}/medical-records` | 진료 기록 등록·목록 조회 |
| `GET` | `/api/v1/medical-records/{record_id}` | 진료 기록 상세 조회 |
| `POST/GET` | `/api/v1/medical-records/{record_id}/predictions` | 폐렴 예측 실행·결과 조회 |

AI 예측은 FastAPI가 Redis Queue에 작업을 등록하고 AI 워커가 작업을 소비하는 방식으로 구현했습니다. 동일 진료 기록과 모델에 대한 결과가 이미 존재하면 저장된 결과를 재사용하여 불필요한 추론을 줄입니다.

AI 워커 실행 파일과 Redis 통신 코드는 최신 `develop` 기준으로 통합되어 있습니다.

### 3.7 아키텍처 설계 및 적용

초기 구조에서는 FastAPI 요청 처리 과정 안에서 약 1.7 - 2.0초가 걸리는 AI 추론을 직접 수행하여, 동시 요청이 늘어날수록 API 처리 자원이 점유되는 문제가 있었습니다.

이를 해결하기 위해 API 서버와 AI 워커를 분리한 Event-Driven Architecture를 설계했습니다.

```text
Client
  ↓ 예측 요청
FastAPI
  ↓ 작업 등록
Redis Queue
  ↓ 작업 소비
AI Worker
  ↓ 결과 발행
Redis Pub/Sub
  ↓ 결과 저장
FastAPI → MySQL → Client
```

- FastAPI: 인증, 요청 검증, 캐시 확인, 작업 등록 및 결과 저장
- Redis List: AI 추론 작업 대기열
- AI Worker: DenseNet121 5-fold 앙상블 추론
- Redis Pub/Sub: 작업 ID별 추론 결과 전달
- MySQL: 환자, 진료 기록, 이미지, 예측 결과 영속화

설계 배경과 대안 비교는 [동시성 문제 해결을 위한 아키텍처 설계](docs/9일차/9일차_동시성문제_해결을위한_아키텍처설계.md)에서 확인할 수 있습니다.

### 3.8 Docker 인프라 관련 파일 작성

Docker Compose에 다음 서비스를 정의했습니다.

| 서비스 | 역할 | 포트 |
|---|---|---|
| `fastapi` | API 서버와 정적 웹 제공 | `8000` |
| `mysql` | 서비스 데이터 저장 | `3306` |
| `redis` | AI 작업 Queue와 결과 Pub/Sub | `6379` |
| `ai-worker` | 별도 프로세스에서 AI 추론 수행 | 내부 서비스 |

MySQL과 Redis에는 healthcheck를 적용하고, FastAPI와 AI 워커는 의존 서비스가 정상 상태가 된 후 실행되도록 구성했습니다. Docker 작업 기록은 [Docker 컨테이너화](docs/8일차/8일차%20Docker%20컨테이너화.md)에 정리했습니다.

현재 브랜치 기준으로 Compose 문법과 네 서비스 정의를 검증했습니다. 전체 이미지 빌드와 E2E 실행은 릴리스 QA에서 다시 확인해야 합니다.

### 3.9 AWS 배포

현재 저장소에서는 AWS 배포 구성과 배포 완료 근거를 확인할 수 없습니다. 따라서 이 단계는 완료로 표시하지 않으며 후속 작업으로 관리합니다.

배포 시 다음 항목을 결정하고 기록해야 합니다.

1. 배포 대상 서비스 선정: EC2, ECS 또는 기타 실행 환경
2. MySQL과 Redis의 운영 구성 및 네트워크 접근 제어
3. 환경 변수와 JWT 비밀 키를 AWS Secrets Manager 또는 Parameter Store로 관리
4. Docker 이미지 빌드와 레지스트리 배포
5. HTTPS, 도메인, healthcheck와 로그 수집 구성
6. 배포 URL과 실행 화면, 장애 대응 절차 기록

### 3.10 QA 진행

현재 자동화 테스트는 환자 목록과 Redis 기반 예측 서비스의 핵심 흐름을 검증합니다.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

2026-07-28 최신 `develop` 기준 실행 결과:

- Redis 기반 예측 서비스 테스트 5개 통과
- 환자 목록 테스트 7개 오류
- 예측 캐시 재사용, Redis 작업 메시지 계약과 결과 저장 검증
- AI 워커 오류, 시간 초과, Redis 연결 실패 응답 검증
- 환자 테스트는 MySQL용 `BigInteger` 기본 키가 SQLite in-memory DB에서 자동 증가하지 않아 `NOT NULL constraint failed: patients.id` 오류 발생

웹 화면의 주요 기능 실행 결과는 [앱 실행 화면](docs/7일차/7일차_앱_실행화면.md)에 기록했습니다.

아직 필요한 QA:

- 최신 `develop` 통합 후 Docker Compose 전체 빌드 및 healthcheck
- 테스트 DB별 기본 키 타입 차이를 처리하여 환자 목록 테스트 복구
- 회원·인증·환자·진료 기록 API의 자동화 테스트 확대
- FastAPI - Redis - AI Worker - MySQL 전체 E2E 테스트
- 동시 예측 요청과 3초 응답 요구사항 부하 테스트
- 브라우저별 화면·권한·오류 메시지 검증
- AWS 배포 후 smoke test와 운영 로그 확인

## 4. 실행 방법

### 4.1 사전 요구사항

- Docker와 Docker Compose
- 로컬 개발 시 Python 3.13과 `uv`
- AI 워커가 통합된 최신 `develop` 브랜치

### 4.2 환경 변수

예시 파일을 복사해 로컬 환경 파일을 생성합니다.

```bash
cp .env.example .env
```

운영 환경에서는 `.env.example`의 기본 비밀번호를 사용하지 말고 DB 비밀번호와 `JWT_SECRET_KEY`를 안전한 값으로 변경해야 합니다.

### 4.3 Docker Compose 실행

```bash
docker compose --env-file .env up --build -d
docker compose --env-file .env ps
```

정상 실행 후 다음 주소를 사용할 수 있습니다.

- 웹 애플리케이션: `http://localhost:8000`
- Swagger API 문서: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/healthcheck`

종료:

```bash
docker compose --env-file .env down
```

데이터 볼륨까지 삭제하려면 데이터가 사라져도 되는지 확인한 뒤 `docker compose --env-file .env down -v`를 실행합니다.

### 4.4 Alembic 마이그레이션

```bash
uv run --group app alembic upgrade head
```

모델 변경 후 새 마이그레이션 생성:

```bash
uv run --group app alembic revision --autogenerate -m "변경 내용"
```

## 5. 프로젝트 구조

```text
ah-web-development-assignment/
├── app/
│   ├── apis/                  # FastAPI 라우터
│   ├── core/                  # 설정, 인증, DB, Redis
│   ├── dependencies/          # 인증·인가 Dependency
│   ├── models/                # SQLAlchemy ORM 모델
│   ├── repositories/          # 데이터 접근 계층
│   ├── schemas/               # Pydantic 스키마
│   ├── services/              # 비즈니스 로직
│   ├── Dockerfile
│   └── main.py
├── worker/
│   ├── model.py               # DenseNet121 추론 코드
│   └── models/                # 5-fold 가중치와 기준 데이터
├── static/                    # HTML, CSS, JavaScript SPA
├── alembic/                   # DB 마이그레이션
├── tests/                     # 자동화 테스트
├── docs/                      # 일자별 설계·구현 기록
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

## 6. 프로젝트 회고

### 잘 진행된 점

- 구현 전에 팀 규칙과 Git Flow를 정해 협업 기준을 통일했습니다.
- API별 요청·응답과 예외 흐름을 문서화한 후 레이어별로 구현했습니다.
- Repository와 Service 계층을 분리하여 데이터 접근과 비즈니스 로직의 책임을 나눴습니다.
- AI 추론의 동시성 문제를 발견하고 Redis 기반 비동기 구조로 개선했습니다.
- 일자별 설계 문서와 실행 화면을 남겨 작업 근거를 추적할 수 있도록 했습니다.

### 개선할 점

- 브랜치별 구현이 `develop`과 `main`에 모두 반영되었는지 릴리스 체크리스트로 확인해야 합니다.
- 일부 핵심 기능에만 존재하는 자동화 테스트를 전체 API와 E2E 범위로 확대해야 합니다.
- Docker 문서의 실행 결과와 현재 저장소 파일 상태를 항상 동일하게 유지해야 합니다.
- AWS 배포, 운영 보안, 모니터링과 장애 대응 절차를 실제 실행 근거와 함께 추가해야 합니다.

### 다음 프로젝트에 적용할 점

- 요구사항을 일정, 담당자, 완료 조건과 연결하여 관리합니다.
- 기능 완료의 기준에 코드 작성뿐 아니라 테스트, 문서, 리뷰, 통합을 포함합니다.
- 통합 브랜치에서 정기적으로 Docker 빌드와 E2E 테스트를 실행합니다.
- 배포와 QA를 마지막 단계에 몰지 않고 프로젝트 초기부터 반복 수행합니다.

## 7. 현재 완료 상태

| Stage 4 항목 | 상태 | 근거 또는 후속 조치 |
|---|---|---|
| Team Rule 정의 | 완료 | `docs/1일차/1일차_team_rules.md` |
| 사용자 요구사항 정의 | 완료 | 회원·환자·진료 기록·예측 설계 문서 |
| API 명세서 작성 | 완료 | `docs/4일차_*` - `docs/6일차_*` |
| Git & GitHub Branch 전략 | 완료 | `docs/2일차/2일차_git_branch_전략.md` |
| 프로젝트 세팅 | 완료 | FastAPI 레이어, Alembic, `pyproject.toml` |
| API 코드 작성 | 완료 | `app/` |
| AI 워커 코드 작성 | 완료 | `worker/` |
| 아키텍처 설계 및 적용 | 완료 | FastAPI - Redis - AI Worker 구조 |
| Docker 인프라 파일 작성 | 완료 | Compose 구성 유효, 릴리스 QA에서 전체 빌드 재검증 필요 |
| AWS 배포 | 미진행 | 배포 환경 선정 및 실행 근거 추가 필요 |
| QA | 부분 완료 | 예측 테스트 5개 통과, 환자 테스트 7개 DB 호환 오류, E2E·부하·배포 QA 필요 |
