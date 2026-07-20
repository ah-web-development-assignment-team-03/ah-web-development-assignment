# REQ-PTNT-004 환자 정보 수정 API

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 수정 API |
| 설명 | 로그인한 사내 개발진, 의료 실무진, 연구진은 환자 상세보기 페이지에서 환자의 이름과 연락처를 수정할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/patients/{patient_id}` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |
| Authorization | `Bearer <access_token>` | 액세스 토큰 |

### 경로 파라미터

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 수정할 환자의 고유 ID |

### 본문 예시

```json
{
  "name": "홍길동",
  "phone": "01012345678"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| name | string | N | 환자 이름. 1자 이상 30자 이하 |
| phone | string | N | 환자 연락처. 하이픈 없는 숫자, 최대 11자 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 환자 정보 수정은 쿼리 파라미터를 사용하지 않음 |

## 3. 응답(Response)

### 성공

- 200 OK

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 45,
  "gender": "M",
  "phone": "01012345678",
  "created_at": "2026-07-20T10:00:00",
  "updated_at": "2026-07-20T11:30:00"
}
```

응답 스키마는 REQ-PTNT-001 / REQ-PTNT-003에서 정의한 `PatientDetailResponse`를 그대로 사용한다.

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 환자 고유 ID |
| name | string | 수정이 반영된 환자 이름 |
| age | integer | 환자 나이 |
| gender | string | 성별. `M`, `F` 중 하나 |
| phone | string | 수정이 반영된 연락처 |
| created_at | string | 등록 일시 (ISO 8601) |
| updated_at | string | 수정 일시 (ISO 8601) |

### 실패

- 401 Unauthorized

```json
{
  "detail": "유효하지 않거나 만료된 Access Token입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 토큰이 없거나 유효하지 않은 경우의 오류 메시지 |

- 403 Forbidden

```json
{
  "detail": "접근 권한이 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 대기자(`PENDING`) 권한 사용자가 요청한 경우의 오류 메시지 |

- 404 Not Found

```json
{
  "detail": "환자를 찾을 수 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 해당 ID의 환자가 존재하지 않는 경우의 오류 메시지 |

- 422 Unprocessable Entity (입력 형식 오류)

```json
{
  "detail": [
    {
      "loc": ["body", "phone"],
      "msg": "String should have at most 11 characters",
      "type": "string_too_long"
    }
  ]
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 입력값 검증 오류 목록 |
| detail[].loc | array | 오류가 발생한 필드 위치 |
| detail[].msg | string | 오류 내용 |
| detail[].type | string | 오류 종류 |

### 4. 비고

- 요구사항상 수정 가능 항목은 이름과 연락처뿐이다. 나이와 성별은 수정 대상이 아니며, 요청 본문에 포함되더라도 무시한다.
- 두 필드 모두 선택 항목이다(Partial 수정). 둘 다 생략하면 아무것도 변경하지 않고 현재 값을 반환한다.
- 필드명과 타입은 REQ-PTNT-001 / REQ-PTNT-003의 `PatientCreateRequest`, `PatientDetailResponse`에 맞췄다. 같은 리소스에서 조회와 수정의 필드명이 달라지지 않도록 하기 위함이다.
- 연락처 중복은 검사하지 않는다. `Patient.phone` 컬럼에 unique 제약이 없어 동일 연락처를 가진 환자가 존재할 수 있다. 회원(`User.phone_number`)과 다른 점이다.
- 접근 권한은 로그인한 `STAFF`, `ADMIN`이다. 요구사항이 "로그인 된 사내 개발진, 의료 실무진, 연구진"이므로 부서로 제한하지 않는다. 환자 등록(REQ-PTNT-001)만 의료인으로 제한된다.
- 권한 검사는 REQ-PTNT-003에서 사용한 `_require_staff_or_admin`(`require_roles(Role.STAFF, Role.ADMIN)`)을 그대로 재사용한다.
- 존재하지 않는 환자에 대한 404는 REQ-PTNT-003의 `get_patient()`가 던지는 예외를 그대로 사용한다.
- `updated_at`은 모델의 `onupdate=func.now()`로 자동 갱신된다.
- 참고: 프런트엔드(`static/pages.js:439`)는 연락처를 `phone_number`라는 이름으로 전송하고, 성별을 `male` / `female`로 판별한다(`static/pages.js:65`, `:91`). 현재 명세는 백엔드 내부 일관성을 우선해 `phone`과 `M` / `F`를 사용하므로, 화면 연동 시점에 환자 API 전체를 한 번에 맞추는 편이 좋겠다.

---

# REQ-PTNT-005 환자 정보 삭제 API

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 삭제 API |
| 설명 | 로그인한 사내 개발진, 의료 실무진, 연구진은 환자 상세보기 페이지에서 환자를 삭제할 수 있다. 삭제 시 해당 환자의 진료기록과 X-Ray 이미지도 함께 영구 삭제한다. |
| 엔드포인트(Endpoint) | `/api/v1/patients/{patient_id}` |
| 메서드(Method) | `DELETE` |
| 인증 필요 여부 | Y |

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | `Bearer <access_token>` | 액세스 토큰 |

### 경로 파라미터

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 삭제할 환자의 고유 ID |

### 본문 예시

본문을 사용하지 않는다.

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 본문을 사용하지 않음 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 환자 삭제는 쿼리 파라미터를 사용하지 않음 |

## 3. 응답(Response)

### 성공

- 204 No Content

응답 본문이 없다.

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| 없음 | - | 본문 없이 상태 코드만 반환 |

### 실패

- 401 Unauthorized

```json
{
  "detail": "유효하지 않거나 만료된 Access Token입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 토큰이 없거나 유효하지 않은 경우의 오류 메시지 |

- 403 Forbidden

```json
{
  "detail": "접근 권한이 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 대기자(`PENDING`) 권한 사용자가 요청한 경우의 오류 메시지 |

- 404 Not Found

```json
{
  "detail": "환자를 찾을 수 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 해당 ID의 환자가 존재하지 않는 경우의 오류 메시지 |

### 4. 비고

- 성공 시 204로 응답하며 본문을 보내지 않는다. `static/apis.js:115`가 204를 받으면 본문을 파싱하지 않고 `null`을 반환한다.
- **연쇄 삭제 범위**는 다음과 같다.

```
Patient
 └─ MedicalRecord      (medical_records.patient_id, ON DELETE CASCADE)
     └─ XrayImage      (xray_images.record_id, ON DELETE CASCADE)
         └─ 로컬 X-Ray 이미지 파일
```

- **DB 레코드는 자동으로 삭제된다.** `MedicalRecord.patient_id`와 `XrayImage.record_id`에 `ondelete="CASCADE"`가 걸려 있고 `Patient.medical_records` 관계에 `passive_deletes=True`가 설정되어 있어, 환자 행 하나를 삭제하면 진료기록과 X-Ray 이미지 레코드가 DB 차원에서 함께 삭제된다. 애플리케이션에서 하나씩 순회 삭제하지 않는다.
- **로컬 이미지 파일은 자동으로 삭제되지 않는다.** 요구사항이 "X-Ray 이미지도 함께 영구 삭제"를 명시하므로, DB 삭제 전에 해당 환자에 속한 `XrayImage.image_url` 목록을 먼저 조회해 두고, DB 삭제가 성공한 뒤 파일을 제거한다.
- **삭제 순서와 실패 처리**
  1. 환자 조회 (없으면 404)
  2. 삭제 대상 `image_url` 목록 수집
  3. DB 삭제 후 커밋
  4. 커밋 성공 후 파일 삭제
  - DB 커밋이 실패하면 파일을 건드리지 않는다. 파일 삭제가 실패하면 이미 DB가 지워진 상태이므로 요청 자체는 204로 성공 처리하고 실패한 경로는 서버 로그로만 남긴다. 파일 삭제 실패를 이유로 DB를 되돌리면 그 파일을 다시 삭제할 수단이 사라지기 때문이다.
- **`image_url`을 실제 파일 경로로 바꾸는 규칙은 REQ-MDR-001 담당자가 정하는 저장 규약을 따른다.** 규약이 확정되기 전까지는 경로 변환을 한 함수에 모아 두어, 확정 시 그 함수만 수정하면 되도록 한다.
- 접근 권한과 404 처리는 REQ-PTNT-004와 동일하다.
- `static/pages.js:460~468`은 삭제 성공 시 "환자 정보와 관련 데이터가 모두 삭제되었습니다."를 표시하고 환자 목록으로 이동하며, 실패 시 `err.message`를 그대로 노출한다.
