# REQ-USER-002

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 로그인 API |
| 설명 | 이메일과 비밀번호를 입력하여 로그인하고, Access Token 및 Refresh Token을 발급받는다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/login` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |

### 본문 예시

```json
{
  "email": "example@example.com",
  "password": "securepassword"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| email | string (EmailStr) | Y | 사용자 이메일 |
| password | string | Y | 사용자 비밀번호 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 로그인 API는 쿼리 파라미터를 사용하지 않음 |

---

## 3. 응답(Response)

### 성공

- 200 OK

    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | access_token | string | 30분 동안 유효한 JWT 액세스 토큰 |
    | token_type | string | 토큰 인증 방식, 항상 `bearer` |

    ### 응답 Headers

    | Key | 예시 값 | 설명 |
    | --- | --- | --- |
    | Set-Cookie | `refresh_token=<JWT>; HttpOnly; SameSite=lax; Max-Age=604800` | 유효기간 7일의 JWT 리프레시 토큰 (HttpOnly 쿠키) |

---

### 실패

- 401 Unauthorized

    ```json
    {
      "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | detail | string | 이메일 또는 비밀번호가 올바르지 않은 경우의 오류 메시지 |

- 403 Forbidden

    ```json
    {
      "detail": "비활성화된 계정입니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | detail | string | 사용자 계정이 비활성화되어 로그인할 수 없다는 오류 메시지 |

- 422 Unprocessable Entity (필수 값 누락 또는 입력 형식 오류)

    ```json
    {
      "detail": [
        {
          "loc": ["body", "email"],
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

---

## 4. 비고

- 액세스 토큰의 유효기간은 30분이다.
- 리프레시 토큰의 유효기간은 7일이며, HttpOnly 쿠키(`refresh_token`)로 전달된다.
- JWT payload에는 최소 식별 정보인 `user_id`와 토큰 종류(`type`)만 저장한다.
- 액세스 토큰 만료 시 리프레시 토큰을 이용해 `POST /api/v1/auth/refresh`로 액세스 토큰을 재발급한다.
- 리프레시 토큰까지 만료된 경우 다시 로그인을 진행해야 한다.
- 비밀번호 검증은 bcrypt를 사용하며, DB에는 해시된 비밀번호만 저장된다.

---

# REQ-USER-003

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 로그아웃 API |
| 설명 | 로그인 유저는 로그아웃 버튼을 통해 로그아웃을 진행할 수 있으며, 로그아웃 시 리프레시 토큰 쿠키가 삭제된다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/logout` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Cookie | `refresh_token=<JWT>` | 로그인 시 발급된 리프레시 토큰 쿠키 (있을 경우 삭제됨) |

### 본문 예시

```
(요청 본문 없음)
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 로그아웃 API는 요청 본문을 사용하지 않음 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 로그아웃 API는 쿼리 파라미터를 사용하지 않음 |

---

## 3. 응답(Response)

### 성공

- 200 OK

    ```json
    {
      "message": "로그아웃 되었습니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | message | string | 로그아웃 성공 메시지 |

    ### 응답 Headers

    | Key | 예시 값 | 설명 |
    | --- | --- | --- |
    | Set-Cookie | `refresh_token=; HttpOnly; SameSite=lax; Max-Age=0` | 리프레시 토큰 쿠키 삭제 처리 |

---

### 실패

- 별도의 오류 응답 없음. 쿠키 존재 여부와 관계없이 항상 200 OK를 반환하며 쿠키를 삭제한다.

---

## 4. 비고

- 로그아웃은 서버 측에서 `refresh_token` HttpOnly 쿠키를 삭제하는 방식으로 처리된다.
- 별도의 인증(Authorization 헤더) 없이 호출 가능하다.
- 클라이언트는 로그아웃 후 보유 중인 액세스 토큰을 로컬에서 직접 제거해야 한다.
- 로그아웃 후 클라이언트는 로그인 페이지로 전환되어야 한다.
