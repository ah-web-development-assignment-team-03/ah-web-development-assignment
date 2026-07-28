# 6일차 - 폐렴 예측 API 설계

> 본 문서는 「6일차 - AI 폐렴 예측 사용자 요구사항 정의서」의 API 규격을 정의한다.
> 현재 작성 범위는 **REQ-PRED-002(폐렴 예측 결과 조회)** 이며, REQ-PRED-001 파트와 공통 규약은 팀 합의 후 하나의 문서로 통합한다.

---

# REQ-PRED-002 폐렴 예측 결과 조회 API

## 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 진료기록별 폐렴 예측 결과 목록 조회 API |
| 설명 | 승인된 사내 사용자가 진료기록 상세 페이지에서 해당 진료기록의 X-ray로 수행한 AI 폐렴 예측 결과를 목록으로 조회한다. |
| 엔드포인트 | `/api/v1/medical-records/{record_id}/predictions` |
| 메서드 | `GET` |
| 인증 필요 여부 | Y |
| 요구사항 | REQ-PRED-002, NFR-PRED-002 |

### 조회 단위

- 예측 결과는 환자 전체가 아니라 **진료기록(`record_id`) 단위**로 조회한다.
- 하나의 진료기록에 서로 다른 모델의 결과가 저장될 수 있으므로 목록으로 반환한다.
- 동일한 진료기록과 동일한 모델의 결과 재사용 여부는 REQ-PRED-001의 캐시 정책에서 처리한다.

---

## 2. 인증 및 권한

- `Authorization: Bearer <access_token>` 헤더가 필요하다.
- 공통 `get_current_user` Dependency로 토큰, 사용자 존재 여부, 활성 상태를 확인한다.
- `role`이 `STAFF` 또는 `ADMIN`인 사용자만 접근할 수 있다.
- `MEDICAL`, `DEV`, `RESEARCH` 부서의 승인된 사용자는 모두 조회할 수 있다.
- `PENDING` 사용자는 접근할 수 없다.

> 현재 프로젝트는 부서(`Department`)와 역할(`Role`)을 별도로 관리한다. `MEDICAL`, `DEV`, `RESEARCH`는 소속 부서이고, `PENDING`, `STAFF`, `ADMIN`은 승인·관리 권한이다. 기존 진료기록 API와 동일하게 승인된 일반 사용자(`STAFF`)와 관리자(`ADMIN`)를 허용한다.

---

## 3. 요청(Request)

### Headers

| Key | Value | 필수 | 설명 |
|---|---|---|---|
| `Authorization` | `Bearer <access_token>` | Y | 로그인 후 발급된 Access Token |

### Path Parameter

| 파라미터명 | 타입 | 필수 | 제약 | 설명 |
|---|---|---|---|---|
| `record_id` | integer | Y | 1 이상 | 조회할 진료기록의 고유 ID |

### Query Parameter

| 파라미터명 | 타입 | 필수 | 기본값 | 제약 | 설명 |
|---|---|---|---|---|---|
| `page` | integer | N | `1` | 1 이상 | 조회할 페이지 번호 |
| `size` | integer | N | `20` | 1~100 | 페이지당 예측 결과 수 |

### Request Body

없음 (`GET` 요청이므로 요청 본문을 사용하지 않는다.)

### 요청 예시

```http
GET /api/v1/medical-records/101/predictions?page=1&size=20
Authorization: Bearer <access_token>
```

---

## 4. 처리 규칙

1. Access Token과 현재 사용자의 활성 상태를 검증한다.
2. 현재 사용자의 역할이 `STAFF` 또는 `ADMIN`인지 확인한다.
3. `record_id`에 해당하는 진료기록의 존재 여부를 확인한다.
4. `ai_analysis_results.record_id`가 요청한 `record_id`와 일치하는 결과를 조회한다.
5. 결과는 `created_at DESC`, 동일 시각이면 `id DESC` 순으로 정렬한다.
6. `page`와 `size`에 따라 목록을 페이지네이션한다.
7. 저장된 결과가 없으면 `404`가 아닌 `200 OK`와 빈 `items`를 반환한다.
8. 조회 API에서는 AI 모델 추론을 실행하거나 새로운 결과를 저장하지 않는다.

---

## 5. 응답(Response)

### 성공: `200 OK`

```json
{
  "items": [
    {
      "id": 37,
      "is_pneumonia": true,
      "confidence": 96.42,
      "heatmap_url": null,
      "predicted_at": "2026-07-21T15:30:45Z",
      "ai_model": "v7_densenet121_5fold"
    },
    {
      "id": 12,
      "is_pneumonia": false,
      "confidence": 18.75,
      "heatmap_url": "/media/heatmaps/record-101-model-v6.png",
      "predicted_at": "2026-07-20T11:20:00Z",
      "ai_model": "v6_densenet121"
    }
  ],
  "page": 1,
  "size": 20,
  "total": 2
}
```

### 최상위 응답 필드

| 필드명 | 타입 | 설명 |
|---|---|---|
| `items` | array | 현재 페이지의 폐렴 예측 결과 목록 |
| `page` | integer | 현재 페이지 번호 |
| `size` | integer | 페이지당 요청 건수 |
| `total` | integer | 해당 진료기록에 저장된 전체 예측 결과 수 |

### `items` 필드

| 필드명 | 타입 | Null 허용 | 설명 |
|---|---|---|---|
| `id` | integer | N | 예측 결과 고유 ID |
| `is_pneumonia` | boolean | N | 폐렴 예측 여부 |
| `confidence` | number | N | 폐렴일 확률. `0.00~100.00`, 소수점 둘째 자리까지 반환 |
| `heatmap_url` | string | Y | Grad-CAM heatmap 이미지 URL. heatmap을 생성하지 않은 경우 `null` |
| `predicted_at` | string(datetime) | N | 예측 수행 및 결과 저장 일시. ISO 8601 형식 |
| `ai_model` | string | N | 예측에 사용한 모델 식별자 |

### 필드 매핑

| 응답 필드 | 저장 필드/출처 |
|---|---|
| `id` | `ai_analysis_results.id` |
| `is_pneumonia` | `ai_analysis_results.is_pneumonia` |
| `confidence` | `ai_analysis_results.confidence` |
| `heatmap_url` | `ai_analysis_results.heatmap_url` |
| `predicted_at` | `ai_analysis_results.created_at` |
| `ai_model` | `ai_analysis_results.ai_model` |

> PR #45의 `predict()`는 이진 softmax 결과 중 폐렴 클래스(class 1)의 확률을 `confidence`로 반환한다. 따라서 예측 결과에 따라 값의 의미가 달라지지 않으며, 조회 API에서도 항상 **폐렴일 확률(0~100)** 로 반환한다. 정상일 확률은 `100 - confidence`, 폐렴 여부는 `confidence >= 50`으로 해석한다.

### 빈 결과 예시

진료기록은 존재하지만 아직 예측을 실행하지 않은 경우:

```json
{
  "items": [],
  "page": 1,
  "size": 20,
  "total": 0
}
```

요청 페이지가 전체 범위를 벗어난 경우에도 `200 OK`와 빈 `items`를 반환하며, `total`은 전체 결과 수를 유지한다.

---

## 6. 오류 응답

오류 응답은 프로젝트 공통 FastAPI 형식인 `detail` 필드를 사용한다.

| 상태 코드 | 상황 | 응답 `detail` |
|---|---|---|
| `401 Unauthorized` | 토큰 누락, 형식 오류, 만료 또는 위조 | `유효하지 않거나 만료된 Access Token입니다.` |
| `403 Forbidden` | `PENDING` 등 허용되지 않은 역할 | `접근 권한이 없습니다.` |
| `403 Forbidden` | 비활성화된 사용자 | `비활성화된 계정입니다.` |
| `404 Not Found` | 진료기록이 존재하지 않음 | `진료기록을 찾을 수 없습니다.` |
| `422 Unprocessable Entity` | `record_id`, `page`, `size` 검증 실패 | FastAPI 입력 검증 오류 배열 |
| `504 Gateway Timeout` | 조회 처리시간이 3초를 초과함 | `폐렴 예측 결과 조회 처리시간이 3초를 초과했습니다.` |

### `404 Not Found` 예시

```json
{
  "detail": "진료기록을 찾을 수 없습니다."
}
```

### `422 Unprocessable Entity` 예시

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "page"],
      "msg": "Input should be greater than or equal to 1",
      "input": "0",
      "ctx": {
        "ge": 1
      }
    }
  ]
}
```

---

## 7. 성능 및 데이터 규칙

- NFR-PRED-002에 따라 API는 **3초 이내**에 응답해야 한다.
- 조회 쿼리는 `record_id` 인덱스를 사용하고 DB에서 정렬 및 페이지네이션한다.
- 안정적인 최신순 정렬을 위해 `(record_id, created_at, id)` 복합 인덱스를 구현 시 검토한다.
- `confidence`는 DB `Numeric(5, 2)`와 맞춰 `0.00~100.00` 범위로 저장·반환한다.
- `ai_model`은 PR #45의 `MODEL_TAG` 값과 동일한 식별자를 사용한다.
- Stage 6 요구사항에서는 heatmap이 선택사항이고 현재 PR #45의 모델도 heatmap을 생성하지 않는다. 다만 Stage 3 ERD와 현재 모델은 `heatmap_url`을 `nullable=False`로 정의하므로, 저장 기본값 또는 nullable 변경 정책은 REQ-PRED-001·DB 담당자와 합의한다.
- 응답에는 원본 X-ray URL을 중복 포함하지 않는다. 원본 이미지는 진료기록 상세 API의 `xray_image_url`을 사용한다.

---

## 8. 구현 예상 구조

| 계층 | 예상 파일 | 책임 |
|---|---|---|
| API | `app/apis/predictions.py` | 요청 검증, 인증·인가, 상태 코드와 응답 반환 |
| Schema | `app/schemas/prediction.py` | 결과 항목 및 페이지 응답 스키마 |
| Service | `app/services/prediction_service.py` | 진료기록 존재 확인, 조회 규칙 및 타임아웃 처리 |
| Repository | `app/repositories/prediction_repository.py` | 전체 건수 조회, 최신순 정렬 및 페이지네이션 |
| Model | `app/models/ai_analysis_result.py` | 저장 필드와 제약조건 정의 |

### 응답 스키마 예시

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None
    predicted_at: datetime
    ai_model: str


class PredictionResultListResponse(BaseModel):
    items: list[PredictionResultItem]
    page: int
    size: int
    total: int
```

구현 시 ORM의 `created_at`을 응답의 `predicted_at`으로 변환하는 명시적 매핑이 필요하다.

---

## 9. 테스트 시나리오

| 구분 | 시나리오 | 기대 결과 |
|---|---|---|
| 정상 | 저장된 결과가 있는 진료기록의 첫 페이지 조회 | `200`, 최신순 `items`, 정확한 `total` |
| 정상 | 서로 다른 모델 결과가 여러 개 존재 | `created_at DESC`, `id DESC` 순으로 반환 |
| 정상 | 저장된 결과가 없음 | `200`, `items: []`, `total: 0` |
| 정상 | 전체 범위를 벗어난 페이지 | `200`, 빈 `items`, 전체 `total` 유지 |
| 정상 | heatmap이 생성되지 않은 결과 | `heatmap_url: null` |
| 인증 | Access Token 누락 또는 만료 | `401` |
| 권한 | `PENDING` 사용자 접근 | `403` |
| 예외 | 존재하지 않는 `record_id` | `404` |
| 검증 | `record_id=0`, `page=0`, `size=101` | `422` |
| 성능 | 정상 목록 조회 | 3초 이내 응답 |

---

## 10. REQ-PRED-001 및 DB 담당자와 합의할 항목

1. `(record_id, ai_model)` 조합에 UNIQUE 제약을 적용하여 동일 진료기록·동일 모델의 결과가 중복 저장되지 않도록 한다.
2. 기존 `AIAnalysisResult.heatmap_url`과 Stage 3 ERD는 `nullable=False`이지만, Stage 6 요구사항에서는 heatmap이 선택사항이고 PR #45의 `predict()`도 heatmap을 반환하지 않는다. `NOT NULL`을 유지하면서 빈 문자열 또는 기본 이미지 URL을 저장할지, Stage 6 마이그레이션에서 `nullable=True`로 변경할지 합의한다. 선택사항의 의미를 유지하려면 `nullable=True`가 더 자연스럽다.
3. 저장 시각 필드명은 DB의 `created_at`, API의 `predicted_at`으로 통일해 매핑한다.
4. REQ-PRED-001 단건 응답과 REQ-PRED-002의 `items[]`는 동일한 결과 필드명과 타입을 사용한다.
5. 공통 오류 메시지와 `504 Gateway Timeout` 처리 방식을 001·002에서 동일하게 적용한다.
