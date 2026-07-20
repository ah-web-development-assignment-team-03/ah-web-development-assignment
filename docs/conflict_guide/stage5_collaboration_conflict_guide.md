# Stage 5 환자 도메인 협업 충돌 예상 정리

## 담당 범위 요약

| 담당 | 요구사항 | 기능 |
|------|----------|------|
| **A** (금준) | REQ-PTNT-001, REQ-PTNT-003 | 환자 등록 + 상세조회 ✅ 완료 |
| **B** | REQ-PTNT-002 | 환자 목록조회 (검색·필터·페이지네이션) |
| **C** | REQ-PTNT-004, REQ-PTNT-005 | 환자 수정 + 삭제 (cascade) |

---

## 겹치는 파일 목록

아래 5개 파일에 A, B, C 모두 손댈 가능성이 있다.

| 파일 | A | B | C | 위험도 |
|------|---|---|---|--------|
| `app/apis/patients.py` | ✅ 기존 작성 | 추가 필요 | 추가 필요 | **높음** |
| `app/services/patient_service.py` | ✅ 기존 작성 | 추가 필요 | 추가 필요 | **높음** |
| `app/repositories/patient_repository.py` | ✅ 기존 작성 | 추가 필요 | 추가 필요 | **높음** |
| `app/schemas/patient.py` | ✅ 기존 작성 | 추가 필요 | 추가 필요 | **중간** |
| `app/models/patients.py` | ✅ 기존 작성 | 읽기만 | C 주의 필요 | **낮음** |

---

## 파일별 상세 충돌 내용

### 1. `app/apis/patients.py` ← 가장 충돌 위험 높음

A가 작성한 내용:
- `POST /api/v1/patients` → `register_patient_handler` (REQ-PTNT-001)
- `GET /api/v1/patients/{patient_id}` → `get_patient_handler` (REQ-PTNT-003)
- `_require_medical_staff` 의존성 함수 (MEDICAL 부서 전용)
- `_require_staff_or_admin` 의존성 함수 (전 직군 접근용)

**B의 예상 추가 기능:**
- `GET /api/v1/patients` (빈 path, `@router.get("")`) — A의 `POST ""` 와 HTTP 메서드가 달라 코드 충돌은 없지만 **같은 파일에 추가**해야 함
- `_require_staff_or_admin`은 이미 A가 정의해 두었으므로 **그대로 재사용 가능**

**C의 예상 추가 기능:**
- `PATCH /api/v1/patients/{patient_id}` → 수정 핸들러
- `DELETE /api/v1/patients/{patient_id}` → 삭제 핸들러
- 두 엔드포인트 모두 A의 `GET /{patient_id}`와 path가 동일하므로 **같은 파일에 추가**해야 함

> **협업 규칙**: 라우터 파일을 새로 만들지 않는다. 반드시 기존 `patients.py` 파일에 핸들러 함수를 추가한다. 동시에 수정하면 git merge conflict 발생 가능 — **작업 순서 또는 작업 구간 분리** 필요.

---

### 2. `app/services/patient_service.py` ← 충돌 위험 높음

A가 작성한 내용:
- `register_patient(db, data)` — 환자 등록
- `get_patient(db, patient_id)` — 환자 조회, 없으면 404 raise

**B의 예상 추가 기능:**
- `list_patients(db, *, name, gender, age_min, age_max, page, size)` 등 목록 조회 함수

**C의 예상 추가 기능:**
- `update_patient(db, patient_id, data)` — 수정
- `delete_patient(db, patient_id)` — 삭제
- **주의**: C는 환자 존재 여부 확인을 위해 A가 이미 만든 `get_patient()`를 내부적으로 호출하게 될 것이라 예상한다. A의 `get_patient` 시그니처가 바뀌면 C 코드도 영향을 받는다.

---

### 3. `app/repositories/patient_repository.py` ← 충돌 위험 높음

A가 작성한 내용:
- `create_patient(db, *, name, age, gender, phone)` — INSERT
- `get_patient_by_id(db, patient_id)` — SELECT by PK

**B의 예상 추가 기능:**
- `get_patients(db, *, name, gender, age_min, age_max, offset, limit)` 등 필터·페이지네이션 쿼리 함수

**C의 예상 추가 기능:**
- `update_patient(db, patient, data)` — UPDATE (name, phone)
- `delete_patient(db, patient)` — DELETE
- **주의**: C의 update/delete 함수는 Patient 객체를 받는 형태로 구현하는 것이 일반적이므로, A의 `get_patient_by_id` 반환값(`Patient | None`)을 그대로 사용 가능 예상

---

### 4. `app/schemas/patient.py` ← 충돌 위험 중간

A가 작성한 내용:
- `PatientCreateRequest` — 등록 요청 body
- `PatientDetailResponse` — 단건 조회 응답 (id, name, age, gender, phone, created_at, updated_at 포함)

**B의 예상 추가 기능:**
- 목록 조회 쿼리 파라미터 스키마 (예: `PatientListQuery`)
- 목록 응답 스키마 (예: `PatientListResponse`) — 내부 아이템은 `PatientDetailResponse`를 재사용 가능

**C의 예상 추가 기능:**
- `PatientUpdateRequest` — 수정 요청 body (name, phone 필드만 포함, 모두 Optional)
- 수정 응답은 A의 `PatientDetailResponse` 그대로 재사용 가능

---

### 5. `app/models/patients.py` ← 충돌 위험 낮음

A가 작성한 내용:
- `GenderEnum` (M/F)
- `Patient` 모델 (id, name, age, gender, phone, created_at, updated_at, medical_records 관계)
- `medical_records` relationship에 `passive_deletes=True` 설정 — DB 레벨 CASCADE에 위임

**B**: 읽기만 하면 됨, 수정 불필요

**C 주의사항**:
- 환자 삭제 시 진료기록·X-Ray도 함께 삭제하는 cascade는 **이미 DB 레벨에서 설정 완료**됨
  - `medical_records.patient_id` FK: `ondelete="CASCADE"` (MedicalRecord 모델)
  - `Patient.medical_records`: `passive_deletes=True`
- 따라서 C는 `db.delete(patient)` + `await db.commit()` 만 하면 진료기록까지 자동 삭제됨
- X-Ray 파일은 **파일 시스템에서도 직접 삭제**해야 함 (`media/` 폴더) — DB cascade로는 처리 안 됨

---

## A → B, C 인터페이스 계약 (변경 금지 항목)

A가 작성한 아래 항목은 B, C가 의존하므로 **유의해서 수정할 수 있도록 한다**.

| 항목 | 위치 | 의존하는 담당 |
|------|------|--------------|
| `get_patient(db, patient_id)` 시그니처 | `patient_service.py` | C (수정·삭제 전 존재 확인) |
| `get_patient_by_id(db, patient_id)` 시그니처 | `patient_repository.py` | C |
| `PatientDetailResponse` 필드 구조 | `schemas/patient.py` | B (목록 아이템 재사용), C (수정 응답 재사용) |
| `_require_staff_or_admin` 의존성 | `apis/patients.py` | B (목록조회 권한 체크) |
| `router` 변수명 및 prefix | `apis/patients.py` | B, C (같은 router에 추가) |

---

## 권장 작업 

파일 내 섹션을 명시적으로 구분하여 작업 구간을 분리한다:

```python
# ── A 구현 영역 ──────────────────────────
# POST /api/v1/patients
# GET  /api/v1/patients/{patient_id}

# ── B 구현 영역 ──────────────────────────
# GET  /api/v1/patients

# ── C 구현 영역 ──────────────────────────
# PATCH  /api/v1/patients/{patient_id}
# DELETE /api/v1/patients/{patient_id}
```
