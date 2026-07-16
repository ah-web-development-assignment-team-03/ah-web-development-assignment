# REQ-USER-004 회원 목록 조회 API

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 목록 조회 API |
| 설명 | 관리자 권한 사용자가 모든 회원을 목록으로 조회하고, 이메일 또는 이름 검색과 부서 필터를 사용할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/admin/users` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | `Bearer <access_token>` | 관리자 사용자의 JWT 액세스 토큰 |


### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| search | string | N | 이메일 또는 이름으로 회원 검색 |
| department | string | N | 부서별 회원 조회(`RESEARCH`, `MEDICAL`, `DEV`) |
| page | integer | N | 조회할 페이지 번호, 기본값 1 |
| size | integer | N | 페이지당 회원 수, 기본값 20 |

---

## 3. 응답(Response)

### 성공

- 200 OK

  ```json
  {
    "items": [
      {
        "id": 1,
        "email": "hong@example.com",
        "name": "홍길동",
        "department": "MEDICAL",
        "gender": "M",
        "phone_number": "01012345678",
        "is_active": true
      }
    ],
    "page": 1,
    "size": 20,
    "total": 1
  }
  ```

  | 필드명 | 타입 | 설명 |
  | --- | --- | --- |
  | items | array | 조회된 회원 목록 |
  | items[].id | integer | 회원 고유 ID |
  | items[].email | string | 회원 이메일 |
  | items[].name | string | 회원 이름 |
  | items[].department | string | 회원 부서 |
  | items[].gender | string | 회원 성별 |
  | items[].phone_number | string | 회원 휴대폰 번호 |
  | items[].is_active | boolean | 계정 활성화 여부 |
  | page | integer | 현재 페이지 번호 |
  | size | integer | 페이지당 회원 수 |
  | total | integer | 검색 및 필터 조건에 맞는 전체 회원 수 |

  ### 응답 Headers

  | Key | 예시 값 | 설명 |
  | --- | --- | --- |
  | Content-Type | `application/json` | 응답 데이터 타입 |

  ---

### 실패

- 401 Unauthorized

  ```json
  {
    "detail": "인증이 필요합니다."
  }
  ```

  | 필드명 | 타입 | 설명 |
  | --- | --- | --- |
  | detail | string | 액세스 토큰이 없거나 유효하지 않은 경우의 오류 메시지 |

- 403 Forbidden

  ```json
  {
    "detail": "관리자 권한이 필요합니다."
  }
  ```

  | 필드명 | 타입 | 설명 |
  | --- | --- | --- |
  | detail | string | 관리자 권한이 없어 회원 목록을 조회할 수 없는 경우의 오류 메시지 |

- 422 Unprocessable Entity (쿼리 파라미터 입력 형식 오류)

  ```json
  {
    "detail": [
      {
        "loc": ["query", "page"],
        "msg": "Input should be greater than or equal to 1",
        "type": "greater_than_equal"
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

---

### 4. 비고

- 관리자 권한(`ADMIN`) 사용자만 접근할 수 있다.
- `search`는 이메일 또는 이름 검색에 사용한다.
- `department`는 `RESEARCH`, `MEDICAL`, `DEV` 중 하나를 사용한다.
- 비밀번호와 해시된 비밀번호는 응답에 포함하지 않는다.
- 모든 로직은 최대 3초 이내에 처리하고 응답해야 한다.

---

# REQ-USER-005 회원 권한 변경 API

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 권한 변경 API |
| 설명 | 관리자 권한 사용자가 선택한 회원의 권한을 변경할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/admin/users/{user_id}/role` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |
| Authorization | `Bearer <access_token>` | 관리자 사용자의 JWT 액세스 토큰 |

### 본문 예시

```json
{
  "role": "STAFF"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| role | string | Y | 변경할 권한(`PENDING`, `STAFF`, `ADMIN`) |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 회원 권한 변경 API는 쿼리 파라미터를 사용하지 않음 |

---

## 3. 응답(Response)

### 성공

- 200 OK

  ```json
  {
    "id": 2,
    "email": "staff@example.com",
    "name": "김직원",
    "role": "STAFF"
  }
  ```

  | 필드명 | 타입 | 설명 |
  | --- | --- | --- |
  | id | integer | 권한을 변경한 회원의 고유 ID |
  | email | string | 회원 이메일 |
  | name | string | 회원 이름 |
  | role | string | 변경된 회원 권한 |

  ### 응답 Headers

  | Key | 예시 값 | 설명 |
  | --- | --- | --- |
  | Content-Type | `application/json` | 응답 데이터 타입 |

  ---

### 실패

- 401 Unauthorized

  ```json
  {
    "detail": "인증이 필요합니다."
  }
  ```

  | 필드명 | 타입 | 설명 |
  | --- | --- | --- |
  | detail | string | 액세스 토큰이 없거나 유효하지 않은 경우의 오류 메시지 |

- 403 Forbidden

  ```json
  {
    "detail": "관리자 권한이 필요합니다."
  }
  ```

  | 필드명 | 타입 | 설명 |
  | --- | --- | --- |
  | detail | string | 관리자 권한이 없어 회원 권한을 변경할 수 없는 경우의 오류 메시지 |

- 404 Not Found

  ```json
  {
    "detail": "회원을 찾을 수 없습니다."
  }
  ```

  | 필드명 | 타입 | 설명 |
  | --- | --- | --- |
  | detail | string | 입력한 `user_id`에 해당하는 회원이 없는 경우의 오류 메시지 |

- 422 Unprocessable Entity (필수 값 누락 또는 입력 형식 오류)

  ```json
  {
    "detail": [
      {
        "loc": ["body", "role"],
        "msg": "Input should be 'PENDING', 'STAFF' or 'ADMIN'",
        "type": "enum"
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

---

### 4. 비고

- 관리자 권한(`ADMIN`) 사용자만 접근할 수 있다.
- `{user_id}`에는 권한을 변경할 회원의 고유 ID를 입력한다.
- 변경 가능한 권한은 `PENDING`, `STAFF`, `ADMIN`이다.
- `PENDING`은 마이페이지 외 모든 서비스에 접근할 수 없다.
- `STAFF`는 흉부 X-ray 관련 읽기, 쓰기, 수정 작업을 수행할 수 있다.
- `ADMIN`은 시스템의 모든 항목에 접근할 수 있다.
- 모든 로직은 최대 3초 이내에 처리하고 응답해야 한다.
