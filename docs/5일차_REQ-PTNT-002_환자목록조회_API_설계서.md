# 환자 목록 조회 API 설계서

## 1. 문서 개요

### 1.1 목적

본 문서는 `REQ-PTNT-002` 환자 목록 조회 API의 요청·응답 규격과 검색·필터·페이지네이션 처리 규칙을 정의한다. 또한 `NFR-PTNT-001`의 성능 기준과 다른 환자 API 구현에 직접 영향을 주는 항목을 정리한다.

### 1.2 적용 요구사항

| 요구사항 ID | 내용 |
| --- | --- |
| `REQ-PTNT-002` | 로그인한 사내 개발진, 의료 실무진, 연구진이 환자 목록을 조회하고 이름 검색, 성별 및 나이 범위 필터를 사용할 수 있어야 한다. |
| `NFR-PTNT-001` | 환자 API는 최대 3초 이내에 처리하고 응답해야 한다. |

## 2. API 기본 정보

| 항목 | 내용 |
| --- | --- |
| API명 | 환자 목록 조회 |
| Method | `GET` |
| URL | `/api/v1/patients` |
| 인증 | Bearer Access Token 필수 |
| 요청 Body | 없음 |
| 응답 Content-Type | `application/json` |
| 성공 상태 코드 | `200 OK` |

## 3. 인증 및 접근 권한

- 공통 `get_current_user` Dependency를 통해 Access Token, 사용자 존재 여부 및 활성 상태를 확인한다.
- 기존 `patients.py`에 정의된 `_require_staff_or_admin` Dependency를 재사용한다.
- `Role.STAFF`, `Role.ADMIN` 사용자에게 조회를 허용한다.
- `Role.PENDING` 사용자는 `403 Forbidden`으로 거부한다.

## 4. 요청

### 4.1 Query Parameters

| 파라미터 | 자료형 | 필수 | 기본값 | 제약 조건 | 설명 |
| --- | --- | :---: | --- | --- | --- |
| `name` | string | N | `null` | 공백 제거 후 1~30자 | 환자 이름 부분 일치 검색 |
| `gender` | string | N | `null` | `M`, `F` | 환자 성별 필터 |
| `min_age` | integer | N | `null` | 0~150 | 최소 나이, 경계값 포함 |
| `max_age` | integer | N | `null` | 0~150 | 최대 나이, 경계값 포함 |
| `page` | integer | N | `1` | 1 이상 | 조회할 페이지 번호 |
| `size` | integer | N | `20` | 1~100 | 페이지당 환자 수 |

### 4.2 검색·필터 처리 규칙

1. 검색·필터 조건을 함께 전달하면 `AND` 조건으로 결합한다.
2. `name`은 앞뒤 공백을 제거한 후 부분 일치로 검색한다.
3. 공백 제거 결과가 빈 문자열이면 `422 Unprocessable Entity`를 반환한다.
4. `gender`는 공통 `Gender` enum의 `M`, `F`만 허용한다.
5. `min_age`와 `max_age`는 경계값을 포함한다.
6. `min_age`가 `max_age`보다 크면 `422 Unprocessable Entity`를 반환한다.
7. 조건이 없으면 전체 환자를 페이지 단위로 조회한다.
8. 기본 정렬은 `Patient.id ASC`로 한다.
9. 조회 결과가 없거나 요청 페이지가 범위를 벗어나면 `200 OK`와 빈 `items`를 반환한다.

## 5. 응답

### 5.1 응답 구조

| 필드 | 자료형 | Nullable | 설명 |
| --- | --- | :---: | --- |
| `items` | array | X | 현재 페이지의 환자 목록 |
| `items[].id` | integer | X | 환자 고유 ID |
| `items[].name` | string | X | 환자 이름 |
| `items[].age` | integer | X | 환자 나이 |
| `items[].gender` | string | O | 성별(`M`, `F`), 등록되지 않은 경우 `null` |
| `items[].phone` | string | X | 환자 연락처 |
| `items[].created_at` | string(datetime) | X | 생성일시 |
| `items[].updated_at` | string(datetime) | O | 수정일시, 수정 이력이 없으면 `null` |
| `total` | integer | X | 검색·필터 조건에 맞는 전체 환자 수 |
| `page` | integer | X | 현재 페이지 번호 |
| `size` | integer | X | 페이지당 요청 건수 |

- 목록의 각 환자 항목은 기존 `PatientDetailResponse`를 재사용한다.
- 조회 결과가 없으면 `items`는 빈 배열로 반환한다.
- 요청 페이지가 전체 범위를 벗어나도 `total`은 검색·필터 조건에 맞는 전체 건수를 유지한다.

## 6. 오류 응답

오류 응답은 프로젝트의 공통 FastAPI 형식인 `detail` 필드를 사용한다.

| 상태 코드 | 의미 | 발생 조건 |
| ---: | --- | --- |
| `200` | OK | 조회 성공, 조회 결과가 없는 경우 포함 |
| `401` | Unauthorized | Access Token 누락, 형식 오류, 만료, 위조 또는 잘못된 Token 종류 |
| `403` | Forbidden | 비활성 사용자 또는 허용되지 않은 역할 |
| `404` | Not Found | Token의 사용자 ID에 해당하는 사용자가 없음 |
| `422` | Unprocessable Entity | 성별, 나이 범위 또는 페이지 값 검증 실패 |
| `500` | Internal Server Error | 예상하지 못한 Database 또는 서버 오류 |

## 7. 계층별 구현 계약

### 7.1 공통 파일

| 계층 | 파일 | 목록 조회 추가 내용 |
| --- | --- | --- |
| Router | `app/apis/patients.py` | `GET /api/v1/patients` Handler |
| Schema | `app/schemas/patient.py` | `PatientListResponse` |
| Service | `app/services/patient_service.py` | `list_patients` |
| Repository | `app/repositories/patient_repository.py` | 목록 조회 및 전체 건수 조회 함수 |

새 파일을 만들지 않고 기존 파일에 기능을 추가한다.

### 7.2 Router

- 기존 `router`와 `_require_staff_or_admin`을 재사용한다.
- Query Parameter 검증과 Dependency 주입을 담당한다.
- Service의 `list_patients`를 호출한다.

### 7.3 Service

- 함수명은 `list_patients`로 한다.
- Database session, 검색·필터 조건, `page`, `size`를 전달받는다.
- 나이 범위 검증, offset 계산 및 응답 조립을 담당한다.
- 목록 조회는 읽기 전용이므로 commit하지 않는다.

### 7.4 Repository

- 검색·필터 조건과 `offset`, `limit`을 적용해 환자 목록을 조회한다.
- 동일한 검색·필터 조건으로 전체 건수를 조회한다.
- 기본 정렬은 `Patient.id ASC`로 한다.
- 조회 query만 수행하며 commit하지 않는다.

### 7.5 Schema

- `PatientListResponse`는 `items`, `total`, `page`, `size`를 포함한다.
- `items`의 자료형은 기존 `PatientDetailResponse` 목록으로 한다.
- 환자 ID는 `int`, 연락처 필드명은 `phone`, 성별은 공통 `Gender | None`을 사용한다.

## 8. NFR-PTNT-001 성능 기준

- 지정된 테스트 환경에서 요청 수신부터 응답 완료까지 3초 미만이어야 한다.
- 애플리케이션 시작과 최초 의존성 설치 시간은 측정에서 제외한다.
- Database query에 검색·필터와 `LIMIT/OFFSET`을 적용한다.
- 목록 응답에 필요하지 않은 연관 데이터는 함께 조회하지 않는다.
- 정상 목록, 복합 필터 및 빈 결과 조건을 각각 측정한다.

## 9. 다른 담당자 구현과 겹치는 부분 및 사전 공유 사항

| 우선순위 | 겹치는 대상 | 연동 항목 | 확인 내용 |
| :---: | --- | --- | --- |
| 중간 | 수정·삭제 담당(병학) | `PatientDetailResponse` | 수정 응답에서 같은 Schema를 재사용할 경우 필드 구조 변경이 목록 응답에도 영향을 줌 |

## 10. 테스트 시나리오

| 구분 | 시나리오 | 기대 결과 |
| --- | --- | --- |
| 정상 | 조건 없이 첫 페이지 조회 | `200`, 최대 20건, 정확한 `total` |
| 정상 | 이름 일부로 검색 | 해당 이름을 포함하는 환자만 반환 |
| 정상 | 성별 필터 | 지정한 성별의 환자만 반환 |
| 정상 | 최소·최대 나이 필터 | 경계값을 포함한 범위의 환자만 반환 |
| 정상 | 복합 검색·필터 | 모든 조건을 만족하는 환자만 반환 |
| 정상 | 조회 결과 없음 | `200`, 빈 `items`, `total=0` |
| 정상 | 전체 범위를 벗어난 페이지 | `200`, 빈 `items`, 전체 건수 유지 |
| 검증 | `page=0` 또는 `size=101` | `422` |
| 검증 | 지원하지 않는 `gender` | `422` |
| 검증 | `min_age > max_age` | `422` |
| 인증 | Token 없음, 만료 또는 위조 | `401` |
| 권한 | 비활성 사용자 또는 `Role.PENDING` | `403` |
| 성능 | 정상·복합 필터·빈 결과 조회 | 각 요청 3초 미만 |
