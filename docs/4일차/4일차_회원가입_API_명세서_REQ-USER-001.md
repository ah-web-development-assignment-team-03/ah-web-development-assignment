# 회원가입 API 명세서 (REQ-USER-001)

## 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원가입 API |
| 설명 | 사내 의료인·개발 실무진이 회원가입을 통해 흉부 X-Ray AI 진단 서비스를 이용할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/users/signup` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
|---|---|---|
| Content-Type | application/json | 요청 타입 |

### 본문 예시

```json
{
  "email": "example@example.com",
  "password": "Password1234!",
  "name": "홍길동",
  "department": "DEVELOPMENT",
  "gender": "M",
  "phone_number": "010-1234-5678"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 (Y / N) | 설명 |
|---|---|---|---|
| email | string | Y | 사용자 이메일. 이메일 형식 검증, 중복 불가 |
| password | string | Y | 사용자 비밀번호. 8자 이상, 영문·숫자·특수문자 각 1개 이상 포함 |
| name | string | Y | 사용자 이름 |
| department | string | Y | 부서. `RESEARCH`(연구) / `MEDICAL`(의료) / `DEVELOPMENT`(개발) 중 하나 |
| gender | string | Y | 성별. `M` / `F` 중 하나 |
| phone_number | string | Y | 휴대폰 번호. `010-XXXX-XXXX` 형식 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | N | 회원가입 API는 쿼리 파라미터를 사용하지 않음 |

---

## 3. 응답(Response)

### 성공

- **201 Created**

```json
{
  "id": 1,
  "email": "example@example.com",
  "name": "홍길동",
  "department": "DEVELOPMENT",
  "gender": "M",
  "phone_number": "010-1234-5678",
  "role": "PENDING",
  "is_active": true,
  "created_at": "2026-07-17T21:00:00"
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 사용자 고유 ID |
| email | string | 사용자 이메일 |
| name | string | 사용자 이름 |
| department | string | 부서 (RESEARCH / MEDICAL / DEVELOPMENT) |
| gender | string | 성별 (M / F) |
| phone_number | string | 휴대폰 번호 |
| role | string | 사용자 권한. 가입 직후 기본값 `PENDING`(대기자) |
| is_active | boolean | 계정 활성화 여부. 가입 직후 기본값 `true` |
| created_at | string | 가입 일시 (ISO 8601) |

※ **비밀번호는 응답에 절대 포함하지 않는다. (NFR-USER-002)**

### 응답 Headers

| Key | 예시 값 | 설명 |
|---|---|---|
| 없음 | - | 회원가입 API는 별도의 응답 헤더를 사용하지 않음 |

### 실패

- **409 Conflict (이메일 중복)**

```json
{
  "detail": "이미 가입된 이메일입니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 동일한 이메일로 가입된 계정이 이미 존재한다는 오류 메시지 |

- **422 Unprocessable Entity (필수 값 누락 또는 입력 형식 오류)**

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Value error, 비밀번호는 8자 이상, 영문·숫자·특수문자를 각각 포함해야 합니다.",
      "type": "value_error"
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

- 가입 직후 사용자 권한은 `PENDING`(대기자)으로 부여되며, 관리자의 권한 변경(REQ-USER-005) 전까지 마이페이지 외 서비스 접근이 불가하다.
- **NFR-USER-002 (비밀번호 입력 보안)**
  - 백엔드는 비밀번호를 어떤 응답에도 포함하지 않는다. (해시 값 포함)
  - 비밀번호는 평문이 아닌 bcrypt 해시로 저장한다.
  - 입력 인풋의 마스킹 처리(●●●) 및 비밀번호 보기 아이콘 토글은 프론트엔드에서 처리한다.
- 이메일은 유니크 제약이 적용되며, 중복 가입 시도 시 409를 반환한다.
- 모든 로직은 3초 이내에 처리하고 응답한다. (NFR-USER-003)
