## 프런트엔드 값 ↔ DB Enum 변환 (REQ-USER-006 / 007 / 008 공통)

API는 프런트엔드와 사람이 읽기 쉬운 문자열을 주고받고, DB에는 기존 Enum 코드를 그대로 저장한다. 변환은 마이페이지 API의 **스키마 / 서비스 경계에서만** 수행하며 DB Enum 정의(`app/models/enums.py`)는 변경하지 않는다.

| 구분 | 프런트엔드 값 | DB Enum |
| --- | --- | --- |
| gender | `male`, `female` | `M`, `F` |
| department | `developer`, `medical team`, `researcher` | `DEV`, `MEDICAL`, `RESEARCH` |
| role | `pending`, `staff`, `admin` | `PENDING`, `STAFF`, `ADMIN` |

- 응답: DB Enum → 프런트엔드 값으로 변환해 내려준다.
- 요청: 프런트엔드 값 → DB Enum으로 변환해 저장한다. 허용되지 않은 값은 422로 응답한다.

---

# REQ-USER-006 마이페이지 조회 API

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 마이페이지 조회 API |
| 설명 | 모든 로그인 유저는 마이페이지에서 본인의 정보를 확인할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y |

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | `Bearer <access_token>` | 액세스 토큰 |

### 본문 예시

GET 요청이므로 본문을 사용하지 않는다.

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 본문을 사용하지 않음 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 마이페이지 조회는 쿼리 파라미터를 사용하지 않음 |

## 3. 응답(Response)

### 성공

- 200 OK

```json
{
  "id": 1,
  "email": "hong@example.com",
  "name": "홍길동",
  "department": "developer",
  "gender": "male",
  "phone_number": "01012345678",
  "role": "staff"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 사용자 고유 ID |
| email | string | 사용자 이메일 |
| name | string | 사용자 이름 |
| department | string | 부서. `medical team`, `developer`, `researcher` 중 하나 |
| gender | string | 성별. `male`, `female` 중 하나 |
| phone_number | string | 휴대폰 번호. 하이픈 없는 숫자 문자열 |
| role | string | 권한. `pending`, `staff`, `admin` 중 하나 |

### 실패

- 401 Unauthorized

```json
{
  "detail": "인증이 필요합니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 토큰이 없거나 유효하지 않은 경우의 오류 메시지 |

### 4. 비고

- 요구사항의 조회 항목에는 고유 ID가 없으나 응답에 `id`를 포함한다. `static/pages.js:246`의 회원 관리 화면이 `u.id === state.user.id`로 본인 여부를 판별해 자기 자신의 권한 변경을 막고 있어, `id`가 없으면 REQ-USER-005 화면이 동작하지 않는다.
- `role`이 `pending`인 사용자도 접근을 허용한다. REQ-USER-005 비고에 "대기자는 마이페이지 외 모든 서비스 접근 불가"로 명시되어 있어 마이페이지는 대기자에게 열려 있어야 한다. 따라서 인증 Dependency는 `role`을 검사하지 않아야 하며, 권한 검사가 필요한 API는 별도 Dependency를 사용한다.
- 프론트엔드는 `static/pages.js:197~206`에서 `email`, `name`, `department`, `gender`, `phone_number`, `role`을 모두 참조한다. 하나라도 누락되면 마이페이지가 비어 보인다.
- 로그인 직후와 정보 수정 직후 `checkAuth()`가 이 API를 호출해 클라이언트 상태를 갱신한다. 이 API의 응답이 프론트엔드 전역 상태의 기준이 된다.

---

# REQ-USER-007 회원 정보 수정 API

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 정보 수정 API |
| 설명 | 모든 로그인 유저는 마이페이지에서 본인의 정보(부서, 휴대폰 번호)를 수정할 수 있다. 수정은 Partial로 이루어진다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |
| Authorization | `Bearer <access_token>` | 액세스 토큰 |

### 본문 예시

```json
{
  "department": "medical team",
  "phone_number": "01012345678"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| department | string | N | 부서. `medical team`, `developer`, `researcher` 중 하나 |
| phone_number | string | N | 휴대폰 번호. 하이픈 없는 숫자 문자열 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 회원 정보 수정은 쿼리 파라미터를 사용하지 않음 |

## 3. 응답(Response)

### 성공

- 200 OK

```json
{
  "id": 1,
  "email": "hong@example.com",
  "name": "홍길동",
  "department": "medical team",
  "gender": "male",
  "phone_number": "01012345678",
  "role": "staff"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 사용자 고유 ID |
| email | string | 사용자 이메일 |
| name | string | 사용자 이름 |
| department | string | 수정이 반영된 부서 |
| gender | string | 성별 |
| phone_number | string | 수정이 반영된 휴대폰 번호 |
| role | string | 권한 |

### 실패

- 401 Unauthorized

```json
{
  "detail": "인증이 필요합니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 토큰이 없거나 유효하지 않은 경우의 오류 메시지 |

- 409 Conflict

```json
{
  "detail": "이미 사용 중인 휴대폰 번호입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 다른 사용자가 이미 사용 중인 휴대폰 번호로 수정을 시도한 경우의 오류 메시지 |

- 422 Unprocessable Entity (입력 형식 오류)

```json
{
  "detail": [
    {
      "loc": ["body", "department"],
      "msg": "Input should be 'medical team', 'developer' or 'researcher'",
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

### 4. 비고

- 요구사항이 Partial 수정으로 명시하고 있어 두 필드 모두 선택 항목이다. 다만 `static/pages.js:287~289`는 실제로 두 필드를 항상 함께 전송한다.
- 프론트엔드가 `.replace(/[^\d]/g, '')`로 하이픈을 제거한 뒤 전송하므로 서버는 숫자 문자열을 받는다.
- 휴대폰 번호는 ERD에서 unique 제약이 걸려 있어 중복 시 409로 응답한다. `static/pages.js:296~300`은 500만 별도 처리하고 나머지는 `detail`을 그대로 노출하므로 409의 메시지가 사용자에게 그대로 전달된다.
- 휴대폰 번호 중복 검사는 **자기 자신을 제외하고** 수행한다. 같은 번호를 그대로 다시 저장하는 경우는 충돌로 보지 않는다.
- 이름, 이메일, 성별은 수정 대상이 아니다. 요청 본문에 포함되더라도 무시한다.
- 수정 성공 후 프론트엔드가 `checkAuth()`로 REQ-USER-006을 다시 호출해 상태를 갱신하므로 응답 본문을 참조하지는 않는다. 다만 Swagger UI에서 반영 결과를 확인할 수 있도록 수정된 사용자 정보를 반환한다.

---

# REQ-USER-008 비밀번호 변경 API

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 비밀번호 변경 API |
| 설명 | 모든 로그인 유저는 마이페이지에서 계정의 비밀번호를 변경할 수 있다. 기존 비밀번호가 일치하는지 검증한 후 새로운 비밀번호를 적용한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me/password` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |
| Authorization | `Bearer <access_token>` | 액세스 토큰 |

### 본문 예시

```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| current_password | string | Y | 기존 비밀번호 |
| new_password | string | Y | 새 비밀번호. 대문자, 소문자, 숫자, 특수문자를 각 1개 이상 포함한 8자 이상 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 비밀번호 변경은 쿼리 파라미터를 사용하지 않음 |

## 3. 응답(Response)

### 성공

- 200 OK

```json
{
  "detail": "비밀번호가 변경되었습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 처리 결과 메시지 |

### 실패

- 400 Bad Request (새 비밀번호 정책 위반)

```json
{
  "detail": "비밀번호는 대소문자, 특수문자, 숫자를 각 1개씩 포함한 8자리 이상이어야 합니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 새 비밀번호가 정책을 충족하지 못한 경우의 오류 메시지 |

- 403 Forbidden (기존 비밀번호 불일치)

```json
{
  "detail": "기존 비밀번호가 일치하지 않습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 입력한 기존 비밀번호가 저장된 비밀번호와 다른 경우의 오류 메시지 |

- 401 Unauthorized

```json
{
  "detail": "인증이 필요합니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 토큰이 없거나 유효하지 않은 경우의 오류 메시지 |

- 422 Unprocessable Entity (필수 값 누락)

```json
{
  "detail": [
    {
      "loc": ["body", "current_password"],
      "msg": "Field required",
      "type": "missing"
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

- 기존 비밀번호 불일치는 반드시 403으로 응답한다. 400과 401은 사용할 수 없으며 이유는 다음과 같다.
  - 400을 사용하면 `static/pages.js:317~318`이 상태 코드만 보고 서버가 보낸 `detail`을 버린 뒤 "비밀번호는 대소문자, 특수문자, 숫자를 각 1개씩 포함한 8자리 이상이어야 합니다."로 덮어쓴다. 기존 비밀번호를 틀린 사용자에게 새 비밀번호 정책 안내가 나가게 된다.
  - 401을 사용하면 `static/apis.js:31~81`이 이를 토큰 만료로 간주해 리프레시를 시도하고 실패 시 `logout()`을 호출한다. 비밀번호를 한 번 잘못 입력했을 뿐인 사용자가 로그아웃된다.
- 400은 새 비밀번호 정책 위반 전용으로 사용한다. 이 경우 프론트엔드가 정책 안내 문구를 자동으로 출력한다.
- 새 비밀번호 정책 검증과 해싱은 REQ-USER-001 담당자가 작성하는 공용 모듈(비밀번호 정책·해싱 함수)을 사용한다. 마이페이지 API는 이 공용 모듈이 병합되면 연결한다.
- 비밀번호 변경 후 기존 발급 토큰의 무효화 여부는 요구사항에 명시되어 있지 않다. 프론트엔드는 `static/pages.js:314`에서 폼만 초기화하고 로그인 상태를 유지하므로 현 설계에서는 토큰을 무효화하지 않는다.
- NFR-USER-002(비밀번호 입력 마스킹, 보기 아이콘)는 이 API의 화면인 `static/templates/my-page.html:39,42`도 적용 대상이다. 다만 서버 측 작업은 없다.
