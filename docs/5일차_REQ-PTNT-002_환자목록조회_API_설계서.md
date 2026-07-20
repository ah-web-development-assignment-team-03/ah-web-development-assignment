# 환자 목록 조회 API 설계서

## 1. 문서 개요

### 1.1 목적

본 문서는 `REQ-PTNT-002` 환자 목록 조회 API의 요청·응답 규격과 검색·필터·페이지네이션 처리 규칙을 정의한다. 또한 `NFR-PTNT-001`을 만족하기 위한 검증 기준과 다른 환자 API 담당자와 사전에 공유해야 할 공통 계약을 정리한다.

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
- 승인 전 사용자(`Role.PENDING`)는 접근할 수 없다.
- 현재 프로젝트의 권한 모델을 기준으로 승인된 내부 사용자(`Role.STAFF`)와 관리자(`Role.ADMIN`)의 조회를 허용하는 안을 사용한다.
- `Department.DEV`, `Department.MEDICAL`, `Department.RESEARCH`는 모두 조회 대상 부서이다.
- 역할과 부서 중 어느 필드를 최종 권한 기준으로 사용할지는 환자 API 전체가 같은 Dependency를 사용하도록 구현 전에 공동 확정한다.

```http
Authorization: Bearer <access_token>
```

## 4. 요청(Request)

### 4.1 Query Parameters

모든 검색·필터 조건은 선택 사항이며, 함께 전달하면 `AND` 조건으로 결합한다.

| 파라미터 | 자료형 | 필수 | 기본값 | 제약 조건 | 설명 |
| --- | --- | :---: | --- | --- | --- |
| `name` | string | N | `null` | 공백 제거 후 1~30자 | 환자 이름 부분 일치 검색 |
| `gender` | string | N | `null` | `M`, `F` | 환자 성별 필터 |
| `min_age` | integer | N | `null` | 0~150 | 조회할 최소 나이, 경계값 포함 |
| `max_age` | integer | N | `null` | 0~150 | 조회할 최대 나이, 경계값 포함 |
| `page` | integer | N | `1` | 1 이상 | 조회할 페이지 번호 |
| `size` | integer | N | `20` | 1~100 | 페이지당 환자 수 |

### 4.2 검색·필터 처리 규칙

1. `name`은 앞뒤 공백을 제거한 후 부분 일치로 검색한다.
2. 공백 제거 결과가 빈 문자열이면 잘못된 검색 조건으로 보고 `422 Unprocessable Entity`를 반환한다.
3. `gender`는 현재 Database enum과 같은 `M`, `F`만 허용한다.
4. `min_age`는 `Patient.age >= min_age`, `max_age`는 `Patient.age <= max_age`로 처리한다.
5. `min_age`가 `max_age`보다 크면 `422 Unprocessable Entity`를 반환한다.
6. 조건을 전달하지 않으면 전체 환자를 페이지 단위로 조회한다.
7. 페이지 간 중복·누락을 방지하기 위해 `Patient.id ASC`로 정렬한 뒤 offset 기반 페이지네이션을 적용한다.
8. 요청한 페이지가 전체 범위를 벗어나거나 조건에 맞는 환자가 없으면 오류가 아닌 빈 `items`와 `total: 0` 또는 해당 조건의 전체 건수를 `200 OK`로 반환한다.

## 5. 응답(Response)

### 5.1 성공 응답

```json
{
  "items": [
    {
      "id": 1,
      "name": "홍길동",
      "age": 32,
      "gender": "M",
      "phone_number": "01012345678",
      "created_at": "2026-07-20T10:30:00",
      "updated_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

| 필드 | 자료형 | Nullable | 설명 |
| --- | --- | :---: | --- |
| `items` | array | X | 현재 페이지의 환자 목록 |
| `items[].id` | integer | X | 환자 고유 ID |
| `items[].name` | string | X | 환자 이름 |
| `items[].age` | integer | X | 환자 나이 |
| `items[].gender` | string | O | 성별(`M`, `F`), 현 DB 모델상 null 가능 |
| `items[].phone_number` | string | X | 환자 연락처. DB의 `phone`을 API에서 `phone_number`로 노출하는 안 |
| `items[].created_at` | string(datetime) | X | 생성일시, ISO 8601 형식 |
| `items[].updated_at` | string(datetime) | O | 수정일시, 수정 이력이 없으면 `null` |
| `total` | integer | X | 검색·필터 조건에 맞는 전체 환자 수 |
| `page` | integer | X | 현재 페이지 번호 |
| `size` | integer | X | 페이지당 요청 건수 |


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

```text
app/apis/patients.py
app/schemas/patient.py
app/services/patient_service.py
app/repositories/patient_repository.py
```

팀원별 별도 schema 또는 service 파일을 만들지 않고 위 공통 파일에 기능을 추가한다.

### 7.2 Schema

```python
class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: Gender | None
    phone_number: str
    created_at: datetime
    updated_at: datetime | None


class PatientListResponse(BaseModel):
    items: list[PatientResponse]
    total: int
    page: int
    size: int
```

`PatientResponse`는 등록, 목록, 상세, 수정 응답에서 함께 재사용한다. `phone_number`를 유지한다면 Pydantic alias 또는 명시적 변환으로 `Patient.phone` 값을 매핑한다.

### 7.3 Router → Service

```python
async def list_patients(
    session: AsyncSession,
    *,
    name: str | None,
    gender: Gender | None,
    min_age: int | None,
    max_age: int | None,
    page: int,
    size: int,
) -> PatientListResponse:
    ...
```

Router는 HTTP 입력 검증과 Dependency 주입을 담당하고, `min_age <= max_age`와 같은 도메인 규칙 및 응답 조립은 Service에서 처리한다.

### 7.4 Service → Repository

```python
async def get_list(
    session: AsyncSession,
    *,
    name: str | None,
    gender: Gender | None,
    min_age: int | None,
    max_age: int | None,
    offset: int,
    limit: int,
) -> Sequence[Patient]:
    ...


async def count(
    session: AsyncSession,
    *,
    name: str | None,
    gender: Gender | None,
    min_age: int | None,
    max_age: int | None,
) -> int:
    ...
```

- Repository는 조회와 count query만 수행하고 commit하지 않는다.
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
- 응답에 필요한 환자 컬럼만 조회하고 불필요한 연관 관계를 eager loading하지 않는다.
- 데이터 증가 후 실행 계획을 확인하고 필요하면 `gender`, `age` 및 정렬 기준에 index를 추가한다.
- `%검색어%` 형태의 이름 부분 검색은 일반 B-tree index를 충분히 활용하지 못할 수 있으므로 대량 데이터 성능 시험 결과에 따라 검색 방식 또는 DB별 index를 공동 결정한다.
- 기능 테스트에 더해 여러 페이지와 복합 필터를 포함한 성능 테스트를 작성한다.

## 9. 다른 담당자와 겹치는 부분 및 사전 공유 사항

아래 항목은 이번 문서에서 일방적으로 확정하지 않고, 실제 설계서를 작성하며 발견한 통합 지점으로 팀에 공유한다.

| 우선순위 | 겹치는 대상 | 공유·합의할 내용 | 현재 코드/문서에서 확인한 이유 |
| :---: | --- | --- | --- |
| 높음 | 환자 등록·상세 담당(금준), 수정·삭제 담당(병학) | 공용 `PatientResponse`의 필드명과 nullable 여부 | 목록·등록·상세·수정이 같은 환자 표현을 반환해야 중복 schema를 피할 수 있음 |
| 높음 | 환자 API 전원 | 환자 ID 자료형을 `int`로 유지할지 UUID로 바꿀지 | 주의사항 예시는 UUID지만 현재 `Patient.id`와 migration은 `BigInteger`임 |
| 높음 | 환자 API 전원 | 연락처 API 필드를 `phone` 또는 `phone_number` 중 하나로 통일 | 현재 환자 모델은 `phone`, 주의사항의 공통 schema는 `phone_number`임 |
| 높음 | 환자 등록·수정 담당 | 성별 enum의 공통 위치와 외부 표현 | 환자 모델은 별도 `GenderEnum(M/F)`, 사용자 모델은 `app.models.enums.Gender(M/F)`, 기존 화면은 `male/female` 값을 사용함 |
| 높음 | 환자 API 전원, 인증 담당 | 조회 권한을 `Role`과 `Department`로 어떻게 판정할지 | 요구사항은 직군을 명시하지만 현재 공통 Dependency는 `Role`만 검사함 |
| 높음 | 환자 등록·수정 담당 | `gender`와 `updated_at`의 null 허용 여부 | 요구사항상 성별은 등록 필수지만 현재 DB의 `gender`, `updated_at`은 nullable임 |
| 중간 | 환자 등록·수정 담당 | 나이 허용 범위 | 목록 filter의 0~150 검증은 등록 값의 허용 범위와 같아야 함 |
| 중간 | 환자 API 전원 | 이름 검색 파라미터를 `name`으로 통일하고 부분 일치 규칙 확정 | 화면·Router·Service·Repository의 이름이 다르면 통합 시 호출부 수정이 발생함 |
| 중간 | 환자 API 전원 | 목록 정렬 기준(`id ASC` 또는 최신 등록순) | offset 페이지네이션에서 명시적이고 공통된 정렬이 없으면 중복·누락 가능 |
| 중간 | 환자 상세 및 진료기록 조회 담당(은영) | 환자 상세 화면에서 진료기록을 별도 endpoint로 조회할지 응답에 포함할지 | 목록 응답에는 진료기록을 포함하지 않되 상세 페이지 호출 구조는 맞춰야 함 |
| 중간 | 환자 수정·삭제 담당(병학), 진료기록 담당 | 환자 삭제와 동시 조회 시의 정책 및 cascade 범위 | 삭제된 환자는 목록에서 즉시 제외되어야 하고 관련 진료기록·파일 삭제 정책과 일치해야 함 |

## 10. 구현 전 팀에 제안할 확정안

아래 안을 환자 도메인의 공통 계약으로 제안한다.

1. 환자 endpoint prefix는 `/api/v1/patients`로 통일한다.
2. 현재 Database와 migration을 존중해 환자 ID는 `integer`로 사용한다.
3. API 연락처 필드는 다른 API와 의미가 분명한 `phone_number`로 통일하고 모델의 `phone`은 mapping한다. 모델까지 바꿀지는 migration 담당자와 별도로 결정한다.
4. 성별 enum은 `app.models.enums.Gender` 하나로 통합하고 API 값은 `M`, `F`를 사용한다.
5. 등록·목록·상세·수정은 공용 `PatientResponse`를 재사용한다.
6. 조회 권한은 활성 상태인 `STAFF`, `ADMIN`에 허용하고 `PENDING`은 거부한다. 부서 세 종류는 모두 허용한다.
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
