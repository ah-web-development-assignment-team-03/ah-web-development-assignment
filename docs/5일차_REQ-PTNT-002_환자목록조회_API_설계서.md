# 환자 목록 조회 API 설계서

## 1. 문서 개요

### 1.1 목적

본 문서는 가빈 담당 범위인 `REQ-PTNT-002` 환자 목록 조회 API의 요청·응답 규격과 검색·필터·페이지네이션 처리 규칙을 정의한다. 또한 `NFR-PTNT-001`을 만족하기 위한 검증 기준과 다른 환자 API 담당자와 사전에 공유해야 할 공통 계약을 정리한다.

### 1.2 적용 요구사항

| 요구사항 ID | 내용 | 본 문서 적용 범위 |
| --- | --- | --- |
| `REQ-PTNT-002` | 로그인한 사내 개발진, 의료 실무진, 연구진이 환자 목록을 조회하고 이름 검색, 성별 및 나이 범위 필터를 사용할 수 있어야 한다. | 전체 |
| `NFR-PTNT-001` | 모든 환자 API는 최대 3초 이내에 처리하고 응답해야 한다. | 목록 조회 API의 성능 기준 |

## 2. API 기본 정보

| 항목 | 내용 |
| --- | --- |
| API명 | 환자 목록 조회 |
| Method | `GET` |
| URL | `/api/v1/patients` |
| 인증 | Bearer Access Token 필수 |
| 요청 Content-Type | 요청 Body 없음 |
| 응답 Content-Type | `application/json` |
| 성공 상태 코드 | `200 OK` |

## 3. 인증 및 접근 권한

- `Authorization` Header에 Bearer Access Token을 전달한다.
- 공통 `get_current_user` Dependency를 통해 토큰, 사용자 존재 여부 및 활성 상태를 확인한다.
- 요구사항에 명시된 사내 개발진, 의료 실무진, 연구진에게 조회를 허용한다.
- 현재 프로젝트에는 사용자 승인 상태를 나타내는 `Role`과 직군을 나타내는 `Department`가 따로 있으므로, 두 필드를 조합한 최종 권한 조건은 환자 API 전체가 같은 Dependency를 사용하도록 구현 전에 공동 확정한다.
- 현재 코드 구조상 `Role.PENDING` 사용자의 허용 여부와 `Role.ADMIN` 사용자의 포함 여부가 요구사항에 명시되어 있지 않으므로 임의로 확정하지 않는다.

## 4. 요청(Request)

### 4.1 Query Parameters

모든 검색·필터 조건은 선택 사항이며, 함께 전달하면 `AND` 조건으로 결합한다.

| 파라미터 | 자료형 | 필수 | 기본값 | 제약 조건 | 설명 |
| --- | --- | :---: | --- | --- | --- |
| `name` | string | N | `null` | 공백 제거 후 빈 문자열 불가 | 환자 이름 부분 일치 검색 |
| `gender` | string | N | `null` | `M`, `F` | 환자 성별 필터 |
| `min_age` | integer | N | `null` | 0 이상 | 조회할 최소 나이, 경계값 포함 |
| `max_age` | integer | N | `null` | 0 이상 | 조회할 최대 나이, 경계값 포함 |
| `page` | integer | N | `1` | 1 이상 | 조회할 페이지 번호 |
| `size` | integer | N | `20` | 1~100 | 페이지당 환자 수 |

### 4.2 검색·필터 처리 규칙

1. `name`은 앞뒤 공백을 제거한 후 부분 일치로 검색한다.
2. 공백 제거 결과가 빈 문자열이면 잘못된 검색 조건으로 보고 `422 Unprocessable Entity`를 반환한다.
3. `gender`는 현재 Database enum과 같은 `M`, `F`만 허용한다.
4. `min_age`는 `Patient.age >= min_age`, `max_age`는 `Patient.age <= max_age`로 처리한다.
5. `min_age`가 `max_age`보다 크면 `422 Unprocessable Entity`를 반환한다.
6. 조건을 전달하지 않으면 전체 환자를 페이지 단위로 조회한다.
7. 페이지 간 중복·누락을 줄이기 위해 고유한 값인 `Patient.id ASC`를 기본 정렬 기준으로 사용한다. 정렬 기능을 별도로 제공하는 것은 현재 범위에 포함하지 않는다.
8. 요청한 페이지가 전체 범위를 벗어나거나 조건에 맞는 환자가 없으면 오류가 아닌 빈 `items`와 `total: 0` 또는 해당 조건의 전체 건수를 `200 OK`로 반환한다.

## 5. 응답(Response)

### 5.1 응답 필드

| 필드 | 자료형 | Nullable | 설명 |
| --- | --- | :---: | --- |
| `items` | array | X | 현재 페이지의 환자 목록 |
| `items[].id` | integer | X | 환자 고유 ID |
| `items[].name` | string | X | 환자 이름 |
| `items[].age` | integer | X | 환자 나이 |
| `items[].gender` | string | 협의 필요 | 성별(`M`, `F`). 요구사항상 등록 필수이나 현 DB 모델은 null 허용 |
| `items[].phone_number` | string | X | 환자 연락처. 외부 필드명은 환자 API 전체에서 통일 필요 |
| `items[].created_at` | string(datetime) | X | 생성일시, ISO 8601 형식 |
| `items[].updated_at` | string(datetime) | O | 수정일시, 수정 이력이 없으면 `null` |
| `total` | integer | X | 검색·필터 조건에 맞는 전체 환자 수 |
| `page` | integer | X | 현재 페이지 번호 |
| `size` | integer | X | 페이지당 요청 건수 |

조회 결과가 없으면 `items`는 빈 배열로 반환하며, `total`에는 검색·필터 조건에 맞는 전체 건수를 반환한다.

## 6. 오류 응답

오류 응답은 프로젝트의 공통 FastAPI 형식인 `detail` 필드를 사용한다.

### 6.1 상태 코드 요약

| 상태 코드 | 의미 | 발생 조건 |
| ---: | --- | --- |
| `200` | OK | 조회 성공, 결과가 없는 경우 포함 |
| `401` | Unauthorized | Access Token 누락, 형식 오류, 만료, 위조 또는 잘못된 토큰 종류 |
| `403` | Forbidden | 비활성 계정 또는 허용되지 않은 역할 |
| `404` | Not Found | 토큰의 사용자 ID에 해당하는 사용자가 없음 |
| `422` | Unprocessable Entity | enum, 나이 범위, 페이지 값 등 Query Parameter 검증 실패 |
| `500` | Internal Server Error | 예상하지 못한 Database 또는 서버 오류 |

## 7. 계층별 구현 계약(초안)

본 절은 목록 담당자가 제안하는 인터페이스이며, 같은 파일을 사용하는 환자 등록·상세·수정·삭제 담당자와 합의 후 확정한다.

### 7.1 파일 위치

| 구분 | 파일 |
| --- | --- |
| Router | `app/apis/patients.py` |
| Schema | `app/schemas/patient.py` |
| Service | `app/services/patient_service.py` |
| Repository | `app/repositories/patient_repository.py` |

팀원별 별도 schema 또는 service 파일을 만들지 않고 위 공통 파일에 기능을 추가한다.

### 7.2 Schema

- 목록 응답은 환자 항목 목록과 `total`, `page`, `size`를 포함한다.
- 환자 항목의 필드는 5장의 응답 필드 정의를 따른다.
- 등록·상세·수정 응답과 공통 `PatientResponse`를 재사용할지는 환자 API 담당자끼리 합의한다.
- 성별 enum과 연락처 필드의 내부 mapping 방식은 공통 필드 계약을 확정한 뒤 결정한다.

### 7.3 Router → Service

- Service 함수명은 `list_patients`로 통일한다.
- 전달 항목은 Database session, `name`, `gender`, `min_age`, `max_age`, `page`, `size`로 한다.
- Router는 HTTP 입력 검증과 Dependency 주입을 담당한다.
- Service는 나이 범위 검증과 응답 조립을 담당한다.

### 7.4 Service → Repository

- Repository 함수는 목록 조회와 전체 건수 조회를 담당한다.
- 전달 항목은 Database session, 검색·필터 조건, `offset`, `limit`로 한다.
- Repository는 조회 query만 수행하고 commit하지 않는다.
- 목록 조회는 읽기 전용이므로 Service에서도 commit 또는 rollback을 수행하지 않는다.
- `offset`은 `(page - 1) * size`, `limit`은 `size`로 계산한다.
- 목록 query와 count query에는 반드시 동일한 검색·필터 조건을 적용한다.

## 8. NFR-PTNT-001 성능 설계 및 검증

### 8.1 성능 기준

- 지정된 테스트 환경에서 API 요청 수신부터 JSON 응답 완료까지 3.0초 미만이어야 한다.
- 애플리케이션 시작, 의존성 설치 및 최초 Database 생성 시간은 측정에서 제외한다.
- 정상 목록, 복합 필터 및 결과가 없는 조건을 각각 측정한다.

### 8.2 구현 시 고려사항

- 전체 행을 애플리케이션으로 가져온 뒤 필터링하지 않고 Database query에 조건과 `LIMIT/OFFSET`을 적용한다.
- 진료기록 등 목록 응답에 필요하지 않은 연관 데이터를 함께 조회하지 않는다.
- index 추가나 DB별 검색 최적화는 실제 데이터 규모와 성능 측정 결과를 확인한 뒤 구현 단계에서 결정한다.
- 기능 테스트에 더해 여러 페이지와 복합 필터를 포함한 성능 테스트를 작성한다.

## 9. 다른 담당자와 겹치는 부분 및 사전 공유 사항

아래 항목은 이번 문서에서 일방적으로 확정하지 않고, 실제 설계서를 작성하며 발견한 통합 지점으로 팀에 공유한다.

| 우선순위 | 겹치는 대상 | 공유·합의할 내용 | 현재 코드/문서에서 확인한 이유 |
| :---: | --- | --- | --- |
| 높음 | 환자 등록·상세 담당(A 금준), 수정·삭제 담당(병학님) | 공용 `PatientResponse`의 필드명과 nullable 여부 | 목록·등록·상세·수정이 같은 환자 표현을 반환해야 중복 schema를 피할 수 있음 |
| 높음 | 환자 API 전원 | 환자 ID 자료형을 `int`로 유지할지 UUID로 바꿀지 | 주의사항 문서는 UUID를 사용하지만 현재 `Patient.id`와 migration은 `BigInteger`임 |
| 높음 | 환자 API 전원 | 연락처 API 필드를 `phone` 또는 `phone_number` 중 하나로 통일 | 현재 환자 모델은 `phone`, 주의사항의 공통 schema는 `phone_number`임 |
| 높음 | 환자 등록·수정 담당 | 성별 enum의 공통 위치와 API 표현 | 환자 모델은 별도 `GenderEnum(M/F)`, 사용자 모델은 `app.models.enums.Gender(M/F)`를 사용함 |
| 높음 | 환자 API 전원, 인증 담당 | 조회 권한을 `Role`과 `Department`로 어떻게 판정할지 | 요구사항은 직군을 명시하지만 현재 공통 Dependency는 `Role`만 검사함 |
| 높음 | 환자 등록·수정 담당 | `gender`와 `updated_at`의 null 허용 여부 | 요구사항상 성별은 등록 필수지만 현재 DB의 `gender`, `updated_at`은 nullable임 |
| 중간 | 환자 등록·수정 담당 | 나이의 최대 허용값 | 목록 filter의 검증 범위는 등록 값의 허용 범위와 같아야 함 |
| 중간 | 환자 API 전원 | 이름 검색 파라미터를 `name`으로 통일하고 부분 일치 규칙 확정 | 화면·Router·Service·Repository의 이름이 다르면 통합 시 호출부 수정이 발생함 |
| 중간 | 환자 API 전원 | 목록 정렬 기준(`id ASC` 또는 최신 등록순) | offset 페이지네이션에서 명시적이고 공통된 정렬이 없으면 중복·누락 가능 |

## 10. 구현 전 최소 합의 제안

지금 단계에서는 구현 충돌을 막는 데 필요한 아래 항목까지만 합의한다. UI 표현, 세부 최적화 및 내부 mapping 방식은 구현 또는 프론트엔드 설계 단계에서 결정한다.

1. 환자 endpoint prefix는 `/api/v1/patients`로 통일한다.
2. 현재 Database와 migration을 존중해 환자 ID는 `integer`로 사용한다.
3. 연락처의 API 필드명을 `phone`과 `phone_number` 중 하나로 환자 API 전체에서 통일한다.
4. 성별의 API 값은 현재 DB와 같은 `M`, `F`를 우선 사용하되, enum 정의 위치의 통합 여부는 환자 모델 담당자와 협의한다.
5. 공통 `PatientResponse`의 재사용 여부와 nullable 필드를 환자 API 담당자끼리 통일한다.
6. `Role`과 `Department`를 조합한 조회 권한 조건을 인증 담당자와 확정한다.
7. 목록 기본값은 `page=1`, `size=20`, 최대 `size=100`으로 통일한다.
8. 검색·필터 조건은 `AND`, 이름은 부분 일치, 나이 경계는 포함한다.
9. 조회 결과가 없거나 범위를 벗어난 페이지는 `404`가 아닌 `200`과 빈 배열을 반환한다.
10. 공용 schema/service/repository 파일과 router 등록 담당자를 정한 후 각 기능 구현을 시작한다.

## 11. 테스트 시나리오

| 구분 | 시나리오 | 기대 결과 |
| --- | --- | --- |
| 정상 | 조건 없이 첫 페이지 조회 | `200`, 최대 20건, 정확한 `total` |
| 정상 | 이름 일부로 검색 | 해당 이름을 포함하는 환자만 반환 |
| 정상 | 성별만 필터 | 지정 성별 환자만 반환 |
| 정상 | 최소·최대 나이 필터 | 경계값을 포함한 범위의 환자만 반환 |
| 정상 | 이름·성별·나이 복합 조건 | 모든 조건을 만족하는 환자만 반환 |
| 정상 | 조건에 맞는 환자 없음 | `200`, `items=[]`, `total=0` |
| 정상 | 전체 페이지 범위를 넘는 page | `200`, `items=[]`, 조건에 맞는 `total` 유지 |
| 검증 | `page=0` 또는 `size=101` | `422` |
| 검증 | 지원하지 않는 `gender` | `422` |
| 검증 | `min_age > max_age` | `422` |
| 인증 | Token 없음·만료·위조 | `401` |
| 권한 | 비활성 사용자 또는 승인 전 사용자 | `403` |
| 성능 | 정상·복합 필터·빈 결과 조회 | 각 요청 3.0초 미만 |
