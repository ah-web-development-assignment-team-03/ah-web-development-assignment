# api 명세서

---

# 환자 정보 등록 API 명세서 (REQ-PTNT-001)

## 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 환자 정보 등록 API |
| 설명 | 사내 의료인 역할을 가진 유저가 환자의 기본 정보를 시스템에 등록한다. |
| 엔드포인트(Endpoint) | `/api/v1/patients` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | Y |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
|---|---|---|
| Content-Type | application/json | 요청 타입 |
| Authorization | Bearer {access_token} | 로그인 후 발급된 Access Token |

### 본문 예시

```json
{
  "name": "홍길동",
  "age": 45,
  "gender": "M",
  "phone": "01012345678"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 (Y / N) | 설명 |
|---|---|---|---|
| name | string | Y | 환자 이름. 최대 30자 |
| age | integer | Y | 환자 나이. 0 이상 150 이하 |
| gender | string | Y | 환자 성별. `M`(남성) / `F`(여성) 중 하나 |
| phone | string | Y | 환자 연락처. 숫자만 입력, 최대 11자 (예: `01012345678`) |

### 쿼리 파라미터

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | N | 환자 등록 API는 쿼리 파라미터를 사용하지 않음 |

---

## 3. 응답(Response)

### 성공

- **201 Created**

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 45,
  "gender": "M",
  "phone": "01012345678",
  "created_at": "2026-07-20T10:00:00",
  "updated_at": null
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 환자 고유 ID |
| name | string | 환자 이름 |
| age | integer | 환자 나이 |
| gender | string | 환자 성별 (`M` / `F`) |
| phone | string | 환자 연락처 |
| created_at | string | 환자 정보 등록 일시 (ISO 8601) |
| updated_at | string \| null | 환자 정보 수정 일시 (ISO 8601). 수정 전에는 `null` |

### 응답 Headers

| Key | 예시 값 | 설명 |
|---|---|---|
| 없음 | - | 별도의 응답 헤더를 사용하지 않음 |

### 실패

- **401 Unauthorized (인증 실패 - 토큰 없음 또는 만료)**

```json
{
  "detail": "유효하지 않거나 만료된 Access Token입니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 토큰이 없거나 유효하지 않을 때의 오류 메시지 |

- **403 Forbidden (권한 없음 - PENDING 계정 또는 비의료인)**

```json
{
  "detail": "의료인만 접근 가능합니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 접근 권한이 없을 때의 오류 메시지 |

- **422 Unprocessable Entity (필수 값 누락 또는 입력 형식 오류)**

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | array | 입력값 검증 오류 목록 |
| detail[].loc | array | 오류가 발생한 필드 위치 |
| detail[].msg | string | 오류 내용 |
| detail[].type | string | 오류 종류 |

---

## 4. 비고

- 요청 유저의 Role이 `PENDING`(대기자)이거나 부서(Department)가 `MEDICAL`이 아닌 경우 403을 반환한다.
- 모든 로직은 3초 이내에 처리하고 응답한다. (NFR-PTNT-001)

---
---

# 환자 정보 상세 조회 API 명세서 (REQ-PTNT-003)

## 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 환자 정보 상세 조회 API |
| 설명 | 로그인된 사내 개발진·의료 실무진·연구진이 특정 환자의 상세 정보를 조회한다. |
| 엔드포인트(Endpoint) | `/api/v1/patients/{patient_id}` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
|---|---|---|
| Authorization | Bearer {access_token} | 로그인 후 발급된 Access Token |

### 경로 파라미터 (Path Parameter)

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| patient_id | integer | Y | 조회할 환자의 고유 ID |

### 쿼리 파라미터

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | N | 환자 상세 조회 API는 쿼리 파라미터를 사용하지 않음 |

### 본문 예시

없음 (GET 요청이므로 요청 본문을 사용하지 않음)

---

## 3. 응답(Response)

### 성공

- **200 OK**

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 45,
  "gender": "M",
  "phone": "01012345678",
  "created_at": "2026-07-20T10:00:00",
  "updated_at": null
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 환자 고유 ID |
| name | string | 환자 이름 |
| age | integer | 환자 나이 |
| gender | string | 환자 성별 (`M` / `F`) |
| phone | string | 환자 연락처 |
| created_at | string | 환자 정보 등록 일시 (ISO 8601) |
| updated_at | string \| null | 환자 정보 수정 일시 (ISO 8601). 수정 전에는 `null` |

### 응답 Headers

| Key | 예시 값 | 설명 |
|---|---|---|
| 없음 | - | 별도의 응답 헤더를 사용하지 않음 |

### 실패

- **401 Unauthorized (인증 실패 - 토큰 없음 또는 만료)**

```json
{
  "detail": "유효하지 않거나 만료된 Access Token입니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 토큰이 없거나 유효하지 않을 때의 오류 메시지 |

- **403 Forbidden (권한 없음 - PENDING 계정)**

```json
{
  "detail": "접근 권한이 없습니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 접근 권한이 없을 때의 오류 메시지 |

- **404 Not Found (환자를 찾을 수 없음)**

```json
{
  "detail": "환자를 찾을 수 없습니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 해당 ID의 환자가 존재하지 않을 때의 오류 메시지 |

---

## 4. 비고

- 요청 유저의 Role이 `PENDING`(대기자)인 경우 403을 반환한다.
- 부서(Department)에 관계없이 `STAFF` 또는 `ADMIN` Role을 가진 유저라면 조회 가능하다.
- 모든 로직은 3초 이내에 처리하고 응답한다. (NFR-PTNT-001)
