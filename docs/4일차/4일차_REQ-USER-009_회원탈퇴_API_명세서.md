# 회원 탈퇴 API 명세서

## 1. 문서 개요

### 1.1 목적

본 문서는 `REQ-USER-009` 회원 탈퇴 기능의 HTTP 요청·응답 규격과 처리 정책을 정의한다.

### 1.2 요구사항

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | `REQ-USER-009` |
| 기능명 | 회원 탈퇴 |
| 기능 설명 | 로그인 사용자가 현재 비밀번호를 확인한 후 자신의 계정과 관련 데이터를 즉시 삭제한다. |
| 인증 | Access Token 필수 |
| 성능 기준 | 지정된 테스트 환경에서 요청별 3.0초 미만 |

## 2. 공통 정책

### 2.1 인증 정책

- Access Token은 `Authorization` Header에 Bearer 형식으로 전달한다.
- 토큰이 없거나 Bearer 형식이 아니면 `401 Unauthorized`를 반환한다.
- 토큰이 만료·위조·손상되었거나 Access Token이 아니면 `401 Unauthorized`를 반환한다.
- 토큰 Payload의 `user_id`로 현재 사용자를 조회한다.
- 현재 사용자가 존재하지 않으면 `404 Not Found`를 반환한다.
- 비활성화된 사용자는 회원 탈퇴 API에 접근할 수 없으며 `403 Forbidden`을 반환한다.

```http
Authorization: Bearer <access_token>
```

### 2.2 응답 형식

- 회원 탈퇴 성공 시 응답 Body 없이 `204 No Content`를 반환한다.
- 회원 탈퇴 성공 시 로그아웃과 동일한 옵션으로 `refresh_token` 쿠키를 삭제한다.
- 오류 응답은 FastAPI의 공통 오류 형식인 `detail` 필드를 사용한다.
- 서버 내부 예외 내용, 비밀번호 및 토큰 정보는 오류 응답에 노출하지 않는다.

```json
{
  "detail": "오류 메시지"
}
```

### 2.3 성능 정책

- 회원 탈퇴 API는 지정된 로컬 테스트 환경에서 3.0초 미만에 응답해야 한다.
- 애플리케이션 시작 시간과 최초 의존성 설치 시간은 측정에서 제외한다.

## 3. 회원 탈퇴 API

### 3.1 기본 정보

| 항목 | 내용 |
| --- | --- |
| API명 | 회원 탈퇴 |
| Method | `DELETE` |
| URL | `/api/v1/users/me` |
| Content-Type | `application/json` |
| 인증 | Bearer Access Token |
| 성공 상태 코드 | `204 No Content` |

### 3.2 기능 설명

현재 로그인한 사용자의 비밀번호를 다시 확인한 후 사용자 계정을 Database에서 하드 삭제한다. 사용자 삭제 시 해당 사용자가 업로드한 `xray_images` 행은 외래키의 `ON DELETE CASCADE` 정책에 따라 함께 삭제한다.

환자, 진료 기록 및 AI 분석 결과는 사용자 삭제의 직접 대상에 포함하지 않는다. 외부 파일 저장소에 저장된 실제 X-ray 파일 삭제도 본 API의 범위에 포함하지 않는다.

### 3.3 Request Header

| Header | 자료형 | 필수 | 설명 | 예시 |
| --- | --- | :---: | --- | --- |
| `Authorization` | String | O | Bearer 형식의 Access Token | `Bearer eyJhbGciOi...` |
| `Content-Type` | String | O | 요청 Body의 미디어 타입 | `application/json` |

### 3.4 Request Body

| 필드 | 자료형 | 필수 | 제약 조건 | 설명 |
| --- | --- | :---: | --- | --- |
| `current_password` | String | O | 빈 문자열 허용 안 함 | 회원 본인 확인을 위한 현재 비밀번호 |

#### 요청 예시

```http
DELETE /api/v1/users/me HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "current_password": "CurrentPassword123!"
}
```

### 3.5 Success Response

#### 회원 탈퇴 성공

```http
HTTP/1.1 204 No Content
Set-Cookie: refresh_token=""; expires=<즉시 만료 시각>; HttpOnly; Max-Age=0; Path=/; SameSite=lax
```

응답 Body는 반환하지 않으며, `Set-Cookie` Header를 통해 브라우저의 Refresh Token 쿠키를 만료시킨다.

### 3.6 Error Response

#### 400 Bad Request — 현재 비밀번호 불일치

```json
{
  "detail": "현재 비밀번호가 일치하지 않습니다."
}
```

#### 401 Unauthorized — Access Token 누락 또는 유효하지 않음

```json
{
  "detail": "유효하지 않거나 만료된 Access Token입니다."
}
```

토큰이 전달되지 않은 경우에도 보안상 동일한 인증 오류 형식을 사용할 수 있다. 최종 메시지는 공통 인증 Dependency의 오류 형식을 따른다.

#### 403 Forbidden — 비활성화된 계정

```json
{
  "detail": "비활성화된 계정입니다."
}
```

#### 404 Not Found — 사용자 없음

```json
{
  "detail": "사용자를 찾을 수 없습니다."
}
```

#### 422 Unprocessable Entity — 요청값 검증 실패

`current_password`가 누락되거나 요청 Body의 형식이 올바르지 않을 때 FastAPI의 요청값 검증 오류를 반환한다.

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "current_password"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

#### 500 Internal Server Error — 회원 탈퇴 처리 실패

```json
{
  "detail": "회원 탈퇴 처리 중 오류가 발생했습니다."
}
```

Database 오류가 발생하면 사용자 및 관련 X-ray 데이터의 삭제 작업을 모두 롤백한다.

### 3.7 상태 코드 요약

| 상태 코드 | 의미 | 발생 조건 |
| ---: | --- | --- |
| `204` | No Content | 회원과 해당 회원이 업로드한 X-ray 데이터 삭제 성공 |
| `400` | Bad Request | 현재 비밀번호 불일치 |
| `401` | Unauthorized | Access Token 누락·형식 오류·만료·위조·손상 또는 잘못된 Token 종류 |
| `403` | Forbidden | 비활성화된 계정 |
| `404` | Not Found | 토큰의 `user_id`와 일치하는 사용자가 존재하지 않음 |
| `422` | Unprocessable Entity | 필수 요청값 누락 또는 자료형·Body 형식 오류 |
| `500` | Internal Server Error | Database 처리 실패 또는 예상하지 못한 서버 오류 |

## 4. 처리 규칙

### 4.1 정상 처리 순서

1. `Authorization` Header에서 Bearer Access Token을 추출한다.
2. 공통 인증 Dependency가 `decode_token()`을 이용해 토큰을 검증한다.
3. 토큰 Payload에서 `user_id`를 가져와 현재 사용자를 조회한다.
4. 사용자의 존재 여부와 활성화 상태를 확인한다.
5. 요청의 `current_password`와 저장된 `hashed_password`를 비교한다.
6. 비밀번호가 일치하면 현재 사용자 행을 삭제한다.
7. `ON DELETE CASCADE`에 따라 해당 사용자가 업로드한 `xray_images` 행을 자동 삭제한다.
8. 하나의 트랜잭션으로 변경 내용을 커밋한다.
9. 로그아웃과 동일한 쿠키 옵션으로 `refresh_token` 쿠키를 삭제한다.
10. `204 No Content`를 반환한다.

### 4.2 데이터 삭제 정책

| 데이터 | 삭제 여부 | 처리 방식 |
| --- | :---: | --- |
| 현재 사용자 | O | `users` 행 하드 삭제 |
| 사용자가 업로드한 X-ray 정보 | O | `xray_images.uploader_id` 외래키의 `ON DELETE CASCADE` |
| 다른 사용자가 업로드한 X-ray 정보 | X | 유지 |
| 환자 정보 | X | 유지 |
| 진료 기록 | X | 유지 |
| AI 분석 결과 | X | 유지 |
| 외부 저장소의 실제 이미지 파일 | X | 현재 요구사항 범위에서 제외 |

### 4.3 트랜잭션 정책

- 사용자 삭제와 관련 X-ray 정보 삭제는 하나의 Database 트랜잭션으로 처리한다.
- 처리 중 오류가 발생하면 전체 작업을 롤백한다.
- 부분 삭제 상태를 허용하지 않는다.

### 4.4 보안 정책

- 현재 비밀번호는 평문으로 저장하거나 로그에 기록하지 않는다.
- 저장된 해시 비밀번호와 안전한 비밀번호 검증 함수를 이용해 비교한다.
- Access Token과 `current_password`는 오류 메시지에 포함하지 않는다.
- 탈퇴 완료 후 삭제된 사용자의 기존 Access Token으로 인증할 수 없어야 한다.
- 탈퇴 완료 후 클라이언트에 `refresh_token` 쿠키가 남아 있지 않아야 한다.

## 5. 테스트 기준

| 테스트 항목 | 예상 결과 |
| --- | --- |
| 정상 토큰과 올바른 현재 비밀번호 | `204`, 사용자 및 해당 사용자의 X-ray 정보 삭제, `refresh_token` 쿠키 만료 |
| 현재 비밀번호 불일치 | `400`, 모든 데이터 유지 |
| Access Token 누락 | `401` |
| 만료·위조·손상된 Access Token | `401` |
| Refresh Token으로 요청 | `401` |
| 비활성화된 사용자 | `403` |
| 토큰의 사용자가 DB에 없음 | `404` |
| `current_password` 누락 | `422` |
| Database 삭제 실패 | `500`, 전체 삭제 롤백 |
| 다른 사용자의 X-ray 정보 존재 | 탈퇴 후에도 해당 데이터 유지 |
| 응답시간 측정 | 지정된 테스트 환경에서 3.0초 미만 |

## 6. 구현 전 연동 확인 사항

- Person 2의 `decode_token()` 반환값과 예외 형식
- 공통 인증 Dependency의 최종 오류 메시지
- 비밀번호 검증 공통 함수의 인터페이스
- 사용자 API Router의 최종 Prefix
- `xray_images.uploader_id`의 `ON DELETE CASCADE` 마이그레이션 적용 여부
- 팀 공통 오류 응답 Body 또는 별도 비즈니스 오류 코드 사용 여부
