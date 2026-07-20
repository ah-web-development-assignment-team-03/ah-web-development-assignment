# 5일차 - 진료기록 등록 API 설계 (REQ-MDR-001, NFR-MDR-001)

> 「5일차 - 진료기록 사용자 요구사항 정의서」 중 담당 범위인 **진료기록 등록(파일 업로드)** 에 대한 API 명세를 작성한다.

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 담당 요구사항 | REQ-MDR-001 (진료기록 등록), NFR-MDR-001 (API 성능) |
| 요청 형식 | `multipart/form-data` (X-Ray 이미지 파일 업로드 포함) |
| 응답 형식 | `application/json` |
| 접근 권한 | 사내 **의료인**(MEDICAL 부서, PENDING 제외) 전용 — 공용 `require_medical_staff` 의존성 적용 |
| 이미지 저장 | 서버 실행 환경의 로컬 저장소 `media/xray/` 에 저장, DB에는 경로만 기록 |
| 업로더 기록 | 로그인한 사용자의 id를 `xray_images.uploader_id` 로 기록 |
| 성능 (NFR-MDR-001) | 최대 3초 이내 로직 처리 및 응답 |

---

## 2. 요구사항 - API 매핑

| 요구사항 ID | 기능 | Method | Endpoint | 상태 코드 |
|---|---|---|---|---|
| REQ-MDR-001 | 진료기록 등록 (X-Ray 포함) | `POST` | `/api/v1/patients/{patient_id}/medical-records` | 201 |

---

## 3. 데이터 모델

ERD 기준으로 진료기록과 X-Ray 이미지는 **별도 테이블로 분리**되어 있으며, 등록 시 두 테이블에 하나의 트랜잭션으로 INSERT한다. 두 모델 모두 **기존 모델을 그대로 사용**한다 (신규 모델 작성 없음).

### 3.1 medical_records (진료기록) — 기존 모델 사용

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | bigint | PK, auto increment | 진료 기록 ID |
| `patient_id` | bigint | FK → patients.id, `ondelete=CASCADE`, NOT NULL | 환자 정보 테이블 참조 |
| `chart_number` | varchar(50) | NOT NULL, **UNIQUE** | 진료 차트 넘버 |
| `symptoms` | text | NOT NULL | 진료된 증상 |
| `created_at` | datetime | NOT NULL, default: current_timestamp | 등록 일시 |
| `updated_at` | datetime | nullable, 수정 시 자동 갱신 | 수정 일시 |

### 3.2 xray_images (X-Ray 이미지) — 기존 모델 사용

| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | bigint | PK, auto increment | 이미지 ID |
| `record_id` | bigint | FK → medical_records.id, `ondelete=CASCADE`, NOT NULL | 진료 기록 참조 |
| `uploader_id` | int | FK → users.id, `ondelete=CASCADE`, NOT NULL | 이미지를 업로드한 사용자 |
| `image_url` | varchar(2048) | NOT NULL | 로컬 저장소 이미지 파일 경로 |
| `shooting_datetime` | datetime | NOT NULL | X-Ray 촬영 일시 (미입력 시 등록 시각으로 저장) |

> **삭제 정책 (REQ-PTNT-005 연계)**: 환자 삭제 → 진료기록 → X-Ray 이미지 순으로 DB 레벨 CASCADE로 연쇄 삭제된다. 파일 시스템의 이미지 파일은 환자 삭제 담당의 로직에서 `media/` 경로 기준으로 삭제한다.

---

## 4. API 상세 명세

### 진료기록 등록 — `POST /api/v1/patients/{patient_id}/medical-records`

#### Path Parameters

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `patient_id` | int | 환자 고유 ID |

#### Request — `multipart/form-data`

| 필드 | 타입 | 필수 | 제약 | 설명 |
|---|---|---|---|---|
| `chart_number` | str | ✅ | 최대 50자 | 진료 차트 넘버 (중복 불가) |
| `symptoms` | str | ✅ | - | 진료된 증상 |
| `xray_image` | file | ✅ | jpg/png, **10MB 이하** | 촬영된 흉부 X-Ray 이미지 |
| `shooting_datetime` | datetime | ❌ | - | X-Ray 촬영 일시 (미입력 시 등록 시각으로 저장) |

#### 처리 흐름

1. 환자 존재 확인 (`get_patient` 재사용) — 없으면 404
2. 차트 넘버 중복 검사 (UNIQUE 제약) — 중복이면 409
3. 이미지 검증 — Content-Type이 jpg/png가 아니면 422, 10MB 초과 시 413
4. 이미지를 `media/xray/` 에 비동기 저장
   - 파일명은 uuid로 충돌 방지
   - 저장 확장자는 업로드 파일명이 아닌 **Content-Type 기준**으로 결정하여 형식-확장자 불일치 방지
5. `medical_records` + `xray_images` 두 테이블 INSERT 후 commit
   - `uploader_id` 는 로그인 사용자의 id, `shooting_datetime` 미입력 시 등록 시각으로 대체
   - 동시 요청이 UNIQUE 제약에 걸리는 경우(IntegrityError)도 409로 처리
   - 실패 시 rollback 및 저장된 파일 삭제 (고아 파일 방지)

#### Response — `201 Created`

```json
{
  "id": 10,
  "patient_id": 1,
  "chart_number": "CH-2026-0001",
  "symptoms": "기침과 발열이 3일간 지속됨",
  "created_at": "2026-07-20T10:05:00",
  "updated_at": null,
  "xray_image": {
    "id": 3,
    "image_url": "media/xray/1_a1b2c3d4.png",
    "shooting_datetime": "2026-07-20T09:30:00"
  }
}
```

> 응답의 `xray_image` 는 중첩 객체 구조를 사용한다. X-Ray가 별도 테이블인 ERD 구조와 일치하며, 추후 이미지 다중화·AI 판독 결과 추가 시 확장이 용이하다. (목록 조회 API(REQ-MDR-002)는 이미지 필드가 불필요하므로 해당 담당 설계를 따른다)

#### Error

| 상태 코드 | 조건 |
|---|---|
| 401 | 로그인하지 않은 사용자 |
| 403 | 의료인이 아닌 사용자 (MEDICAL 부서 외 또는 PENDING 역할) |
| 404 | 해당 ID의 환자가 존재하지 않음 |
| 409 | 이미 존재하는 차트 넘버 (동시 요청의 UNIQUE 위반 포함) |
| 413 | 이미지 파일 크기 10MB 초과 |
| 422 | 필수 항목 누락, chart_number 50자 초과, 이미지 형식 오류 (jpg/png 외) |

---

## 5. 비기능 요구사항 반영 (NFR-MDR-001)

| 요구사항 | 반영 방안 |
|---|---|
| 모든 API 3초 이내 응답 | 파일 저장을 스레드 위임 방식으로 비동기 처리하여 이벤트 루프 블로킹 방지, 파일 크기 10MB 제한으로 처리 시간 상한 확보, 로컬 파일 시스템 저장으로 네트워크 지연 제거, 트랜잭션 내 단순 INSERT 2건으로 로직 최소화 |
