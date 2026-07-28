# 프로젝트 진행 단계 정리 — 한금준

> 흉부 X-Ray AI 진단 서비스 개발 과제(팀 03)의 진행 단계별 회고 정리입니다.
> AWS 배포는 미진행으로 제외합니다.

---

## 1. Team Rule 정의

`docs/1일차/1일차_team_rules.md`에 팀 운영 규칙을 문서화했습니다.

### 주요 규칙 항목

| 항목 | 내용 |
|---|---|
| 코어 타임 | 평일 오후 3시 20분 ~ 4시. 진행 상황 공유 및 이슈 논의 |
| 회의 방식 | 안건 사전 작성, 결정 사항은 Notion 또는 GitHub Issue/PR에 기록 |
| 불참 공유 | 사전 안내 원칙, 작업 상태와 예상 복귀 시점 작성 |
| Git Branch | `develop` 직접 push 자제, 모든 작업은 기능 브랜치 생성 후 PR로 병합 |
| Commit 메시지 | `[#이슈번호] 변경 내용` 형식 준수 |
| Pull Request | 최소 1인 코드 리뷰 후 merge, merge 후 브랜치 삭제 |
| 코드 리뷰 | 코드와 구현 방식 검토, `[필수]` / `[제안]` / `[질문]` 구분 |
| 업무 기록 | 담당자·상태·관련 PR을 Notion 또는 Discord에 기록 |

### 커밋 타입 규칙

```
feat    새로운 기능 추가
fix     버그 수정
docs    문서 수정
refactor 기능 변경 없는 코드 구조 개선
test    테스트 코드
chore   설정·패키지·Docker 등 개발 환경 변경
style   코드 동작과 무관한 형식 수정
```

### Git & GitHub Workflow 흐름

```
GitHub Issue 생성 → develop 최신화 → 작업 브랜치 생성 → 기능 구현
→ 로컬 테스트 → commit → push → PR 생성 → 코드 리뷰 → 수정 반영
→ develop merge → 브랜치 삭제 → 업무 기록 업데이트
```

---

## 2. 사용자 요구사항 정의

본 프로젝트의 사용자 요구사항은 팀에서 사전 제공된 명세를 기반으로 합니다.

### 서비스 개요

사내 의료인·연구원·개발자가 흉부 X-Ray 이미지를 업로드하고, AI 모델로 폐렴 여부를 예측하는 시스템입니다.

### 사용자 유형

| 역할 | 설명 |
|---|---|
| `PENDING` | 가입 직후 대기 상태. 마이페이지 외 서비스 접근 불가 |
| `STAFF` | 관리자 승인 완료. 환자·진료기록·AI 예측 기능 사용 가능 |
| `ADMIN` | 시스템 전체 접근 가능. 회원 권한 관리 포함 |

### 요구사항 도메인

| 도메인 | 요구사항 ID | 내용 |
|---|---|---|
| 사용자 | REQ-USER-001 | 회원가입 |
| 사용자 | REQ-USER-002~003 | 로그인 / 로그아웃 |
| 사용자 | REQ-USER-004~005 | 관리자 회원 목록 조회 및 권한 변경 |
| 사용자 | REQ-USER-006~008 | 마이페이지 조회·수정·비밀번호 변경 |
| 사용자 | REQ-USER-009 | 회원 탈퇴 |
| 환자 | REQ-PTNT-001 | 환자 정보 등록 |
| 환자 | REQ-PTNT-002 | 환자 목록 조회 (페이지네이션) |
| 환자 | REQ-PTNT-003~005 | 환자 상세 조회·수정·삭제 |
| 진료기록 | REQ-MED-001~004 | 진료기록 등록·조회·수정·삭제 (X-Ray 이미지 업로드 포함) |
| 예측 | REQ-PRED-001 | AI 폐렴 예측 실행 (캐시 정책 적용) |
| 예측 | REQ-PRED-002 | 예측 결과 목록 조회 |

### 비기능 요구사항 (NFR)

- 모든 API는 3초 이내 응답
- 비밀번호는 절대 응답에 노출 금지 (NFR-USER-002)
- Refresh Token은 HTTP-only Cookie로 발급 (NFR-USER-001)
- 폐렴 예측 모델 Recall ≥ 0.90 (NFR-PRED-001)

---

## 3. API 명세서 작성

`docs/4일차` ~ `docs/6일차`에 걸쳐 팀원별로 API 명세서를 작성했습니다.

### 명세서 작성 목록

| 일차 | 파일 | 내용 |
|---|---|---|
| 4일차 | `4일차_회원가입_API_명세서_REQ-USER-001.md` | 회원가입 API |
| 4일차 | `4일차_USER_API_설계_REQ_USER_02_03.md` | 로그인·로그아웃 API |
| 4일차 | `4일차_USER_API_설계.md` | 관리자 회원 목록·권한 변경·마이페이지·비밀번호 변경 API |
| 4일차 | `4일차_공통인증인가_회원탈퇴_설계서.md` | 공통 인증 Dependency 및 회원 탈퇴 API |
| 4일차 | `4일차_REQ-USER-009_회원탈퇴_API_명세서.md` | 회원 탈퇴 API 명세 |
| 5일차 | `5일차_환자관리_API_설계_REQ_PTNT_01_03.md` | 환자 등록·목록 조회·상세 조회 API |
| 5일차 | `5일차_환자관리_API_설계_REQ_PTNT_04_05.md` | 환자 수정·삭제 API |
| 5일차 | `5일차_REQ-PTNT-002_환자목록조회_API_명세서.md` | 환자 목록 조회 API 명세 |
| 5일차 | `5일차_진료기록등록_API_설계.md` | 진료기록 등록 API |
| 5일차 | `5일차_Medical Record API_설계.md` | 진료기록 전체 API 설계 |
| 6일차 | `6일차_폐렴예측_API_설계_REQ_PRED_001.md` | 폐렴 예측 실행 API (캐시·동시성 정책 포함) |
| 6일차 | `6일차_폐렴예측_API_설계.md` | 예측 결과 목록 조회 API |

### API 명세서 작성 형식

각 명세서는 아래 구조로 작성했습니다.

```
1. API 개요 (엔드포인트, 메서드, 인증 여부)
2. 요청 (Headers, Request Body, Query Parameter)
3. 응답 (성공 응답 예시 및 필드 설명, 실패 응답 목록)
4. 비고 (구현 시 주의 사항, 프론트엔드 연동 조건)
```

### 핵심 엔드포인트 목록

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| POST | `/api/v1/users/signup` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 |
| POST | `/api/v1/auth/logout` | 로그아웃 |
| GET | `/api/v1/users/me` | 마이페이지 조회 |
| PATCH | `/api/v1/users/me` | 회원 정보 수정 |
| PATCH | `/api/v1/users/me/password` | 비밀번호 변경 |
| DELETE | `/api/v1/users/me` | 회원 탈퇴 |
| GET | `/api/v1/admin/users` | 관리자 회원 목록 조회 |
| PATCH | `/api/v1/admin/users/{user_id}/role` | 회원 권한 변경 |
| POST | `/api/v1/patients` | 환자 등록 |
| GET | `/api/v1/patients` | 환자 목록 조회 |
| GET | `/api/v1/patients/{patient_id}` | 환자 상세 조회 |
| PATCH | `/api/v1/patients/{patient_id}` | 환자 정보 수정 |
| DELETE | `/api/v1/patients/{patient_id}` | 환자 삭제 |
| POST | `/api/v1/patients/{patient_id}/medical-records` | 진료기록 등록 |
| GET | `/api/v1/patients/{patient_id}/medical-records` | 진료기록 목록 조회 |
| POST | `/api/v1/medical-records/{record_id}/predictions` | AI 폐렴 예측 실행 |
| GET | `/api/v1/medical-records/{record_id}/predictions` | 예측 결과 목록 조회 |

---

## 4. Git & Github Branch 전략 구성

`docs/2일차/2일차_git_branch_전략.md`에 Git Flow 브랜치 전략을 정의했습니다.

### 전략 선택: Git Flow

초기 Team Rule에서는 GitHub Flow(main 기준)를 적용했으나, 릴리스 단계 관리와 QA 분리의 필요성으로 Git Flow로 전환했습니다.

### 브랜치 구조

| 브랜치 | 역할 | 분기 위치 | merge 대상 |
|---|---|---|---|
| `main` | 배포 가능한 안정 버전 | - | - |
| `develop` | 다음 릴리스 통합 브랜치 | `main` | - |
| `feat/*`, `fix/*`, `docs/*` 등 | 실제 작업 단위 | `develop` | `develop` |
| `release/vX.Y.Z` | 배포 준비 (QA·버전 정리) | `develop` | `main` + `develop` |
| `hotfix/*` | 운영 중 긴급 버그 수정 | `main` | `main` + `develop` |

### 일반 기능 개발 워크플로우

```bash
git checkout develop
git pull origin develop
git checkout -b feat/기능명

# 기능 구현 후
git commit -m "[#12] feat: 기능 설명"
git push origin feat/기능명
# → develop 대상으로 PR 생성 → 1인 이상 리뷰 승인 → merge
```

### GitHub Flow 대비 Git Flow 채택 이유

| 항목 | GitHub Flow | Git Flow (채택) |
|---|---|---|
| 릴리스 관리 | main merge = 즉시 배포 | release 브랜치에서 QA 후 승격 |
| 긴급 대응 | 별도 개념 없음 | hotfix 브랜치로 운영 이슈 분리 |
| 브랜치 수 | main + 작업 브랜치 | main / develop / feat / release / hotfix |

### 저장소 보호 규칙

- `main` 브랜치: 직접 push 금지, PR 필수, 승인 1인 이상
- `develop` 브랜치: 직접 push 금지, PR 필수
- default branch를 `develop`으로 설정 (PR 기본 타깃)

---

## 5. 프로젝트 세팅

### 기술 스택

| 구분 | 기술 |
|---|---|
| 언어 | Python 3.13 |
| 웹 프레임워크 | FastAPI |
| ORM | SQLAlchemy (async) |
| DB 마이그레이션 | Alembic |
| 데이터베이스 | MySQL 8.0 (개발 초기: SQLite) |
| 메시지 큐 | Redis 7 |
| 패키지 관리 | uv |
| 인증 | JWT (python-jose), bcrypt (passlib) |
| AI 추론 | PyTorch, DenseNet121 5-fold 앙상블 |

### 의존성 그룹 구조 (`pyproject.toml`)

```toml
[dependency-groups]
app = [
    "fastapi[standard]", "sqlalchemy[asyncio]", "alembic",
    "asyncmy", "pydantic-settings", "passlib[bcrypt]",
    "python-jose[cryptography]", ...
]
ai = [
    "torch", "torchvision", "pillow", "numpy",
    "opencv-python-headless", "albumentations"
]
```

앱 서버와 AI 워커의 의존성을 그룹으로 분리하여 Docker 이미지 빌드 시 불필요한 패키지 설치를 방지했습니다.

### 프로젝트 디렉터리 구조

```
ah-web-development-assignment/
├── app/
│   ├── apis/           # FastAPI 라우터 (엔드포인트)
│   ├── core/           # 공통 설정, DB 연결, 보안
│   ├── dependencies/   # 인증 Dependency
│   ├── models/         # SQLAlchemy ORM 모델
│   ├── repositories/   # DB 접근 계층
│   ├── schemas/        # Pydantic 요청/응답 스키마
│   ├── services/       # 비즈니스 로직
│   └── main.py         # FastAPI 진입점
├── worker/
│   ├── main.py         # AI 워커 실행 루프
│   ├── model.py        # DenseNet121 추론 함수
│   ├── redis_client.py # Redis 큐 클라이언트
│   └── models/         # fold0~4.pth 모델 파일
├── alembic/            # DB 마이그레이션 파일
├── docs/               # 팀 문서
├── static/             # 프론트엔드 정적 파일
├── docker-compose.yml
└── pyproject.toml
```

### 요청 처리 계층 흐름

```
클라이언트
  └─ app/apis/        HTTP 요청 수신, 라우팅
  └─ app/schemas/     Pydantic 요청 검증
  └─ app/services/    비즈니스 로직 (중복 확인, 해싱 등)
  └─ app/repositories/ AsyncSession으로 DB CRUD
  └─ app/models/      SQLAlchemy ↔ DB 테이블 매핑
```

### DB 마이그레이션 (Alembic)

```bash
# 마이그레이션 파일 자동 생성
uv run alembic revision --autogenerate -m "create initial tables"

# 데이터베이스에 적용
uv run alembic upgrade head
```

생성된 테이블: `users`, `patients`, `medical_records`, `xray_images`, `ai_analysis_results`

---

## 6. API 및 AI 워커 코드 작성 후 Branch 전략을 통한 코드 병합

### 구현 파일 목록

**FastAPI 서버 (`app/`)**

| 파일 | 구현 내용 |
|---|---|
| `apis/auth.py` | 로그인, 로그아웃, 토큰 갱신 |
| `apis/users.py` | 회원가입, 마이페이지 조회·수정·비밀번호 변경·탈퇴 |
| `apis/admin_users.py` | 관리자 회원 목록 조회, 권한 변경 |
| `apis/patients.py` | 환자 CRUD |
| `apis/medical_records.py` | 진료기록 등록·조회 (X-Ray 이미지 업로드) |
| `apis/predictions.py` | 폐렴 예측 실행 (REQ-PRED-001), 결과 목록 (REQ-PRED-002) |
| `core/security.py` | 비밀번호 해싱, JWT 생성·검증 |
| `core/redis_client.py` | Redis 큐 enqueue 및 결과 대기 |
| `dependencies/auth.py` | 공통 인증 Dependency (`get_current_user`) |

**AI 워커 (`worker/`)**

| 파일 | 구현 내용 |
|---|---|
| `worker/main.py` | Redis 큐 폴링 루프, 태스크 처리, 결과 publish |
| `worker/model.py` | DenseNet121 5-fold 앙상블 추론 (`predict()`) |
| `worker/redis_client.py` | 큐에서 태스크 dequeue, 결과 publish |

### 주요 Branch PR 병합 이력 (git log 기반)

| PR | 브랜치 | 내용 |
|---|---|---|
| #88 | `feat/redis-api` | FastAPI Redis 연동 API 구현 |
| #90 | `feat/stage03-ai-worker` | AI 워커 + Redis Queue 폴링 및 추론 결과 publish |
| #86 | `feature/#85-add-redis-worker` | Redis Worker 서비스 추가 |
| #81 | `docs/day9-eda-ey` | 9일차 EDA 설계 문서 |
| #92 | `fix/#91` | SQLite 호환 타입 제거, Dockerfile 개선, Redis BRPOP 타임아웃 수정 |

### 코드 병합 시 충돌 해결 원칙

- 충돌 발생 시 해당 코드를 작성한 팀원과 먼저 의도 확인
- `develop` 최신화 후 작업 브랜치에서 merge하여 해결
- 해결 결과는 PR에 기록

### 폐렴 예측 동시성 처리 (캐시 정책)

```
POST /medical-records/{record_id}/predictions

1. 진료기록 존재 확인
2. X-Ray 이미지 존재 확인
3. 캐시 조회 (record_id + ai_model 조합)
   ├─ 캐시 히트: 저장된 결과 즉시 반환 (200, cached: true)
   └─ 캐시 미스: Redis Queue에 추론 태스크 등록 → Worker 결과 대기
      └─ 결과 수신 후 DB 저장 → 응답 (201, cached: false)
         └─ IntegrityError 발생 시 (동시 요청 충돌): rollback 후 재조회 → 200, cached: true
```

---

## 7. 아키텍처 설계 및 적용

`docs/9일차/`에 각 팀원이 EDA 아키텍처 설계 문서를 작성했습니다.

### 동시성 문제 배경

폐렴 예측 모델(DenseNet121 5-fold 앙상블)의 CPU 추론 시간은 약 1.7~2.0초입니다.  
FastAPI가 추론을 요청 처리 흐름 안에서 직접 수행하면 동시 요청 시 응답 지연이 누적되어 NFR-PRED-002(3초 이내 응답)를 충족하기 어렵습니다.

### 해결 방향: Event-Driven Architecture (EDA)

```
클라이언트
  └─ POST /predictions → FastAPI (작업 큐에 등록 후 즉시 응답 반환)
                              └─ Redis List (작업 대기열)
                                    └─ AI 워커 (BLPOP으로 태스크 dequeue → predict() 실행)
                                          └─ Redis (결과 publish)
                                    └─ FastAPI (결과 구독 → DB 저장 → 최종 응답 반환)
                              └─ MySQL (예측 결과 저장)
```

### 컴포넌트별 역할

| 컴포넌트 | 역할 |
|---|---|
| FastAPI (Producer) | 예측 요청을 Redis 큐에 등록하고 결과를 대기, 완료 후 DB 저장 및 응답 |
| Redis (Broker) | 작업 대기열(List) 및 결과 채널(Pub/Sub) 역할 |
| AI 워커 (Consumer) | Redis에서 태스크를 꺼내 DenseNet121 추론 수행 후 결과 publish |
| MySQL (Storage) | 예측 결과 영구 저장 |

### Redis Streams vs Redis List (BLPOP) 선택

| 항목 | Redis Streams | Redis List + BLPOP (채택) |
|---|---|---|
| 메시지 저장 | O | X (소비 후 제거) |
| ACK / 재시도 | O (Consumer Group) | X (직접 구현 필요) |
| 학습 곡선 | 중간 | 낮음 |
| 적합 상황 | 고가용성 실무 이벤트 | 단순 비동기 태스크 큐 |

단순한 태스크 큐 용도이므로 Redis List + BLPOP 방식을 채택했습니다.

### EDA 구조 도식

```
Client → FastAPI → Redis List (enqueue)
                         ↑
                   AI 워커 (dequeue → predict → publish)
                         ↓
                   Redis (결과 채널)
                         ↓
              FastAPI (결과 수신 → DB 저장 → 응답)
```

### 설계 원칙

- FastAPI(요청 처리)와 AI 워커(추론 수행)의 역할이 명확히 분리
- Redis를 통한 작업 대기열로 동시 요청이 몰려도 FastAPI 응답 지연 방지
- 추론 결과는 `(record_id, ai_model)` UNIQUE 제약으로 중복 저장 방지
- 동시 요청 충돌 시 409 대신 캐시 결과 반환 (200) — 클라이언트 재시도 불필요

---

## 8. 도커 인프라 관련 파일 작성

`docker-compose.yml`과 `app/Dockerfile`, `worker/Dockerfile`을 작성하여 컨테이너 환경을 구성했습니다.

### 컨테이너 구성 (`docker-compose.yml`)

```yaml
services:
  fastapi:    # FastAPI 서버 (포트 8000)
  mysql:      # MySQL 8.0 (포트 3306)
  redis:      # Redis 7-alpine (포트 6379)
  ai-worker:  # AI 추론 워커
```

### 서비스별 역할과 설정

**FastAPI 컨테이너**
- 시작 시 `alembic upgrade head` 실행 후 uvicorn 서버 기동
- `media_volume` 마운트로 X-Ray 이미지 파일 공유
- `mysql`, `redis` 서비스의 `service_healthy` 조건 충족 후 시작

**MySQL 컨테이너**
- 환경 변수로 데이터베이스·사용자 설정 (`.env` 파일 주입)
- `mysql_volume`으로 데이터 영속성 보장
- healthcheck: `mysqladmin ping`

**Redis 컨테이너**
- `redis:7-alpine` 경량 이미지 사용
- `redis_volume`으로 데이터 영속성
- healthcheck: `redis-cli ping`

**AI 워커 컨테이너**
- `worker/Dockerfile`로 PyTorch 포함 별도 이미지 빌드
- `media_volume` 마운트로 FastAPI와 X-Ray 이미지 공유
- `redis` 서비스 healthy 조건 충족 후 시작
- `restart: unless-stopped`로 장애 시 자동 재시작

### 의존성 분리 전략

앱 서버와 AI 워커의 Python 의존성을 `uv` 그룹으로 분리하여 각 Dockerfile에서 필요한 그룹만 설치합니다.

```dockerfile
# FastAPI Dockerfile
RUN uv sync --group app

# AI 워커 Dockerfile
RUN uv sync --group ai
```

PyTorch(약 2GB)를 AI 워커 이미지에만 설치하여 FastAPI 이미지 크기를 최소화했습니다.

### 실행 명령어

```bash
# 로컬 개발 서버 실행
fastapi dev app/main.py

# 이미지 빌드 및 전체 컨테이너 시작
docker compose up --build

# 컨테이너 상태 확인
docker compose ps
```

### 실행 결과 확인

- FastAPI 이미지 빌드 성공
- FastAPI, MySQL, Redis, AI 워커 컨테이너 모두 `healthy` 상태 확인
- FastAPI: `localhost:8000` 접근 가능
- MySQL: 포트 `3306` 정상 연결

---

## 9. QA 진행

`docs/7일차/7일차_앱_실행화면.md`를 기반으로 주요 기능의 E2E 동작을 검증했습니다.

### 검증 환경

- FastAPI 로컬 서버 실행 (`fastapi dev app/main.py`)
- 브라우저에서 `localhost:8000` 접속
- Swagger UI (`/docs`)를 통한 API 직접 호출 병행

### 사용자 기능 QA

| 화면 | 엔드포인트 | 검증 결과 |
|---|---|---|
| 회원가입 | `POST /api/v1/users/signup` | 201 Created, role=PENDING 확인 |
| 로그인 | `POST /api/v1/auth/login` | 200 OK, access_token 발급 확인 |
| 로그아웃 | `POST /api/v1/auth/logout` | 클라이언트 세션 초기화 및 `/login` 이동 확인 |
| 홈 로그인 상태 | `GET /api/v1/users/me` | 200 OK, 사용자 정보 및 권한별 UI 분기 확인 |
| 마이페이지 조회 | `GET /api/v1/users/me` | 200 OK, 전체 필드 정상 표시 확인 |
| 내 정보 수정 | `PATCH /api/v1/users/me` | 200 OK, 부서·전화번호 수정 반영 확인 |
| 비밀번호 변경 | `PATCH /api/v1/users/me/password` | 200 OK, 폼 초기화 및 완료 알림 확인 |
| 회원 탈퇴 | `DELETE /api/v1/users/me` | 204 No Content, 세션 제거 후 `/login` 이동 확인 |

### 환자·진료기록 기능 QA

| 화면 | 엔드포인트 | 검증 결과 |
|---|---|---|
| 환자 정보 수정 | `PATCH /api/v1/patients/{id}` | 이름·전화번호 수정 정상 반영 확인 |
| 진료기록 등록 | `POST /api/v1/patients/{id}/medical-records` | X-Ray 이미지 업로드 및 등록 완료 확인 |
| 진료기록 목록 | `GET /api/v1/patients/{id}/medical-records` | 등록 후 목록 갱신 확인 |

### 관리자 기능 QA

| 화면 | 엔드포인트 | 검증 결과 |
|---|---|---|
| 회원 관리 | `GET /api/v1/admin/users` | `items` 배열 정상 렌더, 부서 필터 동작 확인 |
| 권한 변경 | `PATCH /api/v1/admin/users/{id}/role` | 200 OK, role 변경 반영 확인 |
| 진료 상세 | `GET /api/v1/medical-records/{id}/predictions` | `{items, page, size, total}` 구조, 예측 결과 표 렌더 확인 |
| AI 예측 실행 | `POST /api/v1/medical-records/{id}/predictions` | is_pneumonia, confidence, ai_model 응답 확인 |

### 발견된 버그 및 수정 사항

| 버그 | 원인 | 수정 |
|---|---|---|
| 부서 필터 422 오류 | 프론트가 `developer` 전송, 서버는 `DEV` 기대 | 프론트 option value를 `DEV`/`MEDICAL`/`RESEARCH`로 수정 |
| 회원 검색 미동작 | 프론트 쿼리 파라미터명 `query` 사용, 서버는 `search` 기대 | 파라미터명 `search`로 수정 |
| Redis BRPOP 소켓 타임아웃 | BRPOP 무한 블로킹으로 소켓 타임아웃 발생 | 타임아웃 값 설정으로 수정 (`fix/#91`) |
| SQLite 호환 타입 오류 | MySQL 전용 타입에 `with_variant` 사용 | SQLite 호환 코드 제거, MySQL 전용 타입으로 통일 |

### 테스트 코드

```
tests/
├── test_patient_list.py          # 환자 목록 조회 테스트
└── test_prediction_service_redis.py  # Redis 연동 예측 서비스 테스트
```
