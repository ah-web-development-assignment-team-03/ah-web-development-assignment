# 환자 목록 조회 API 명세서 (REQ-PTNT-002)

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 목록 조회 API |
| 설명 | 승인된 사내 사용자가 환자 목록을 조회하고 이름 검색, 성별·나이 범위 필터 및 페이지네이션을 사용할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/patients` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | `Bearer <access_token>` | JWT Access Token |

### 본문 필드

| 파라미터명 | 타입 | 필수 (Y / N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 환자 목록 조회 API는 요청 Body를 사용하지 않음 |

### 쿼리 파라미터

| 쿼리 파라미터명 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `name` | string | N | `null` | 환자 이름 부분 일치 검색. 앞뒤 공백 제거 후 1~30자 |
| `gender` | string | N | `null` | 성별 필터. `M`, `F` 중 하나 |
| `min_age` | integer | N | `null` | 최소 나이. 0~150, 경계값 포함 |
| `max_age` | integer | N | `null` | 최대 나이. 0~150, 경계값 포함 |
| `page` | integer | N | `1` | 조회할 페이지 번호. 1 이상 |
| `size` | integer | N | `20` | 페이지당 환자 수. 1~100 |

### 요청 예시

```http
GET /api/v1/patients?name=홍&gender=M&min_age=20&max_age=40&page=1&size=20 HTTP/1.1
Authorization: Bearer <access_token>
```

---

## 3. 응답(Response)

### 성공

- **200 OK**

```json
{
  "items": [
    {
      "id": 1,
      "name": "홍길동",
      "age": 32,
      "gender": "M",
      "phone": "01012345678",
      "created_at": "2026-07-20T10:30:00",
      "updated_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `items` | array | 현재 페이지의 환자 목록 |
| `items[].id` | integer | 환자 고유 ID |
| `items[].name` | string | 환자 이름 |
| `items[].age` | integer | 환자 나이 |
| `items[].gender` | string 또는 null | 환자 성별. `M`, `F` 또는 `null` |
| `items[].phone` | string | 환자 연락처 |
| `items[].created_at` | string(datetime) | 환자 정보 생성일시, ISO 8601 형식 |
| `items[].updated_at` | string(datetime) 또는 null | 환자 정보 수정일시. 수정 이력이 없으면 `null` |
| `total` | integer | 검색·필터 조건에 맞는 전체 환자 수 |
| `page` | integer | 현재 페이지 번호 |
| `size` | integer | 페이지당 요청 건수 |

조회 결과가 없으면 `200 OK`와 빈 `items`를 반환한다. 요청한 페이지가 전체 범위를 벗어나도 `total`은 검색·필터 조건에 맞는 전체 건수를 유지한다.

### 응답 Headers

| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | `application/json` | 응답 데이터 타입 |

### 실패

- **401 Unauthorized (Access Token 누락 또는 유효하지 않음)**

```json
{
  "detail": "유효하지 않거나 만료된 Access Token입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `detail` | string | 인증 실패 사유 |

- **403 Forbidden (접근 권한 없음)**

```json
{
  "detail": "접근 권한이 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `detail` | string | 허용되지 않은 역할에 대한 오류 메시지 |

비활성 사용자는 공통 인증 Dependency의 정책에 따라 `{"detail": "비활성화된 계정입니다."}`를 반환한다.

- **404 Not Found (인증 사용자 없음)**

```json
{
  "detail": "사용자를 찾을 수 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `detail` | string | Token의 사용자 ID와 일치하는 사용자가 없다는 오류 메시지 |

- **422 Unprocessable Entity (쿼리 파라미터 검증 실패)**

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "page"],
      "msg": "Input should be greater than or equal to 1",
      "input": "0"
    }
  ]
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `detail` | array 또는 string | 쿼리 파라미터 형식 또는 나이 범위 검증 오류 |
| `detail[].loc` | array | 오류가 발생한 파라미터 위치 |
| `detail[].msg` | string | 오류 내용 |
| `detail[].type` | string | 오류 종류 |

---

## 4. 비고

- 기존 `_require_staff_or_admin` Dependency를 사용하며 `Role.STAFF`, `Role.ADMIN` 사용자만 조회할 수 있다.
- 검색·필터 조건을 함께 전달하면 `AND` 조건으로 결합한다.
- 이름은 앞뒤 공백 제거 후 부분 일치로 검색한다.
- `min_age`가 `max_age`보다 크면 `422 Unprocessable Entity`를 반환한다.
- 기본 정렬은 환자 ID 오름차순(`id ASC`)이다.
- 목록의 각 환자 항목은 기존 `PatientDetailResponse`와 동일한 필드 구조를 사용한다.
- 환자 성별은 현재 모델과 Schema에 따라 `null`일 수 있다.
- 전체 조회 후 애플리케이션에서 필터링하지 않고 Database query에 검색·필터와 `LIMIT/OFFSET`을 적용한다.
- 모든 로직은 3초 이내에 처리하고 응답한다. (`NFR-PTNT-001`)
