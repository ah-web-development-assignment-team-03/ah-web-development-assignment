# REQ-PRED-001 폐렴 예측 실행 API

> 본 문서는 「6일차 - AI 폐렴 예측 사용자 요구사항 정의서」의 **REQ-PRED-001(AI 모델 활용 폐렴 예측)** 규격을 정의한다.
> 응답 필드명·타입·오류 형식은 REQ-PRED-002 명세와 동일한 규약을 사용한다.

---

## 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 진료기록 폐렴 예측 실행 API |
| 설명 | 승인된 사내 사용자가 진료기록 상세 페이지의 「AI 예측 결과보기」를 통해, 해당 진료기록에 저장된 X-ray로 폐렴 예측을 수행한다. |
| 엔드포인트 | `/api/v1/medical-records/{record_id}/predictions` |
| 메서드 | `POST` |
| 인증 필요 여부 | Y |
| 요구사항 | REQ-PRED-001, NFR-PRED-002 |
| 예측 함수 | `worker/model.py` 의 `predict(image_path) -> {is_pneumonia, confidence, ai_model}` (PR #45) |

### 캐시 정책 (요구사항 핵심)

- 예측 결과는 **`record_id` + `ai_model` 조합**으로 식별한다.
- 동일 조합의 결과가 이미 저장되어 있으면 **AI 추론을 수행하지 않고 저장된 결과를 반환**한다.
- 모델이 교체되면 `ai_model` 값이 달라지므로 새로 추론하며, 결과는 모델별로 누적 저장된다. (REQ-PRED-002 목록 조회에서 모델별 결과 확인)

---

## 2. 인증 및 권한

- `Authorization: Bearer <access_token>` 헤더가 필요하다.
- 공통 `get_current_user` Dependency로 토큰, 사용자 존재 여부, 활성 상태를 확인한다.
- `role`이 `STAFF` 또는 `ADMIN`인 사용자만 접근할 수 있다. (`PENDING` 불가)
- `MEDICAL`, `DEV`, `RESEARCH` 부서의 승인된 사용자는 모두 실행할 수 있다.

> REQ-PRED-002와 동일한 권한 판정 기준을 사용한다.

---

## 3. 요청(Request)

### Headers

| Key | Value | 필수 | 설명 |
|---|---|---|---|
| `Authorization` | `Bearer <access_token>` | Y | 로그인 후 발급된 Access Token |

### Path Parameter

| 파라미터명 | 타입 | 필수 | 제약 | 설명 |
|---|---|---|---|---|
| `record_id` | integer | Y | 1 이상 | 예측을 수행할 진료기록의 고유 ID |

### Request Body

없음. 예측에 사용할 X-ray는 진료기록 저장 시 업로드된 이미지(`xray_images.image_url`)를 사용한다.

### 요청 예시

```http
POST /api/v1/medical-records/101/predictions
Authorization: Bearer <access_token>
```

---

## 4. 처리 규칙

1. Access Token과 현재 사용자의 활성 상태를 검증한다.
2. 현재 사용자의 역할이 `STAFF` 또는 `ADMIN`인지 확인한다.
3. `record_id`에 해당하는 진료기록의 존재 여부를 확인한다. (없으면 404)
4. 해당 진료기록에 연결된 X-ray 이미지의 존재 여부를 확인한다. (없으면 404)
5. `ai_analysis_results`에서 `record_id` + 현재 모델의 `ai_model` 조합을 조회한다.
   - **캐시 히트**: 저장된 결과를 그대로 반환한다. **추론을 수행하지 않는다.** → `200 OK`
   - **캐시 미스**: 6번으로 진행한다.
6. `predict(image_path)`를 호출하여 예측을 수행한다.
7. 반환값을 `ai_analysis_results`에 저장하고 commit한다. → `201 Created`
8. 추론 또는 저장 실패 시 rollback한다. (500)

---

## 5. 응답(Response)

### 성공: `200 OK` (캐시 히트) / `201 Created` (신규 추론)

```json
{
  "id": 37,
  "is_pneumonia": true,
  "confidence": 96.42,
  "heatmap_url": null,
  "predicted_at": "2026-07-21T15:30:45Z",
  "ai_model": "v7_densenet121_5fold",
  "cached": false
}
```

### 응답 필드

| 필드명 | 타입 | Null 허용 | 설명 |
|---|---|---|---|
| `id` | integer | N | 예측 결과 고유 ID |
| `is_pneumonia` | boolean | N | 폐렴 예측 여부 (폐렴 확률 0.5 이상) |
| `confidence` | number | N | **폐렴일 확률**. `0.00~100.00`, 소수점 둘째 자리까지 반환 |
| `heatmap_url` | string | Y | Grad-CAM heatmap 이미지 URL. 생성하지 않은 경우 `null` |
| `predicted_at` | string(datetime) | N | 예측 수행 및 결과 저장 일시. ISO 8601 형식 |
| `ai_model` | string | N | 예측에 사용한 모델 식별자 |
| `cached` | boolean | N | **001 전용 메타 필드.** 저장된 결과 반환 여부(재추론 생략 확인용) |

> `id` ~ `ai_model` 6개 필드는 REQ-PRED-002의 `items[]` 항목과 **동일한 필드명·타입**이다.
> `cached`는 캐시 정책 검증을 위한 001 전용 필드이며 002 목록에는 포함하지 않는다.

### 필드 매핑

| 응답 필드 | 저장 필드/출처 |
|---|---|
| `id` | `ai_analysis_results.id` |
| `is_pneumonia` | `ai_analysis_results.is_pneumonia` ← `predict()["is_pneumonia"]` |
| `confidence` | `ai_analysis_results.confidence` ← `predict()["confidence"]` |
| `heatmap_url` | `ai_analysis_results.heatmap_url` |
| `predicted_at` | `ai_analysis_results.created_at` |
| `ai_model` | `ai_analysis_results.ai_model` ← `predict()["ai_model"]` (`MODEL_TAG`) |
| `cached` | 캐시 조회 결과에 따라 서비스 계층에서 판단 |

> PR #45의 `predict()`는 `confidence`를 **예측한 클래스의 확신도**가 아닌 **폐렴일 확률(0~100)** 로 반환한다.
> 따라서 `is_pneumonia: false`, `confidence: 3.20` 과 같은 응답이 정상이며, 화면 문구에 이 의미를 명시해야 한다.

---

## 6. 오류 응답

오류 응답은 프로젝트 공통 FastAPI 형식인 `detail` 필드를 사용한다.

| 상태 코드 | 상황 | 응답 `detail` |
|---|---|---|
| `401 Unauthorized` | 토큰 누락, 형식 오류, 만료 또는 위조 | `유효하지 않거나 만료된 Access Token입니다.` |
| `403 Forbidden` | `PENDING` 등 허용되지 않은 역할 | `접근 권한이 없습니다.` |
| `403 Forbidden` | 비활성화된 사용자 | `비활성화된 계정입니다.` |
| `404 Not Found` | 진료기록이 존재하지 않음 | `진료기록을 찾을 수 없습니다.` |
| `404 Not Found` | 진료기록에 X-ray 이미지가 없음 | `예측에 사용할 X-ray 이미지가 없습니다.` |
| `422 Unprocessable Entity` | `record_id` 검증 실패 | FastAPI 입력 검증 오류 배열 |
| `500 Internal Server Error` | AI 추론 실패 (모델 로드 실패, 이미지 손상 등) | `폐렴 예측 처리 중 오류가 발생했습니다.` |
| `504 Gateway Timeout` | 처리시간이 3초를 초과함 | `폐렴 예측 처리시간이 3초를 초과했습니다.` |

---

## 7. 성능 및 데이터 규칙 (NFR-PRED-002)

- API는 **3초 이내**에 응답해야 한다.
- 캐시 히트 시에는 추론을 생략하므로 조회 수준의 응답 시간을 유지한다.
- `predict()`는 CPU 기준 **1.7~2.0초**(3-scale × 5-fold = 15회 추론)가 소요된다. 캐시 미스 시 3초 초과 위험이 있어 아래 대응을 적용한다.
  - **스레드 위임**: `predict()`는 동기 CPU 작업이므로 async 핸들러에서 직접 호출하면 이벤트 루프가 차단되어 다른 요청까지 지연된다. `anyio.to_thread.run_sync`로 위임한다.
  - **워밍업**: 모델 로드가 lazy(최초 호출 시 fold 5개 로드)이므로, 앱 시작 시점(FastAPI lifespan)에 `load_models()`를 미리 호출한다. 첫 요청 지연과 동시 요청 시 중복 로드를 방지한다.
  - **타임아웃**: 3초 초과 시 `504`로 응답한다. (002와 동일 정책)
- `confidence`는 DB `Numeric(5, 2)`와 맞춰 `0.00~100.00` 범위로 저장·반환한다.
- `ai_model`은 PR #45의 `MODEL_TAG`(`v7_densenet121_5fold`) 값을 그대로 저장한다.
- 현재 모델은 heatmap을 생성하지 않으므로 `heatmap_url`은 `null`을 허용해야 한다.

---

## 8. 구현 예상 구조

REQ-PRED-002와 **동일한 파일을 공유**하므로, 구현 시 담당 구간을 분리하거나 병합 순서를 조율한다.

| 계층 | 예상 파일 | 001 책임 |
|---|---|---|
| API | `app/apis/predictions.py` | `POST` 핸들러, 인증·인가, 201/200 구분 |
| Schema | `app/schemas/prediction.py` | 단건 응답 스키마 (002의 item 스키마 재사용) |
| Service | `app/services/prediction_service.py` | 진료기록·이미지 확인, 캐시 판단, `predict()` 호출, 트랜잭션 |
| Repository | `app/repositories/prediction_repository.py` | 캐시 조회(`record_id` + `ai_model`), 결과 저장 |
| Model | `app/models/ai_analysis_result.py` | 저장 필드와 제약조건 |

### 응답 스키마 예시

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionResultItem(BaseModel):
    """002의 items[] 항목과 동일한 구조 — 공용으로 사용한다."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None
    predicted_at: datetime
    ai_model: str


class PredictionRunResponse(PredictionResultItem):
    """001 전용 — 캐시 히트 여부를 함께 반환한다."""

    cached: bool
```

구현 시 ORM의 `created_at`을 응답의 `predicted_at`으로 변환하는 명시적 매핑이 필요하다.

---

## 9. 테스트 시나리오

| 구분 | 시나리오 | 기대 결과 |
|---|---|---|
| 정상 | 저장된 결과가 없는 진료기록에 예측 실행 | `201`, `cached: false`, 결과가 DB에 저장됨 |
| 정상 | 동일 진료기록·동일 모델로 재요청 | `200`, `cached: true`, **추론이 재실행되지 않음** |
| 정상 | heatmap 미생성 결과 | `heatmap_url: null` |
| 정상 | 응답 `confidence` 범위 | `0.00 ~ 100.00` |
| 인증 | Access Token 누락 또는 만료 | `401` |
| 권한 | `PENDING` 사용자 접근 | `403` |
| 예외 | 존재하지 않는 `record_id` | `404` |
| 예외 | X-ray 이미지가 없는 진료기록 | `404` |
| 검증 | `record_id=0` | `422` |
| 성능 | 캐시 히트 요청 | 3초 이내 응답 |

> 캐시 동작 검증은 **DB 저장 건수가 늘지 않는지**로 확인한다. 응답만 비교하면 재추론 여부를 알 수 없다.

---

## 10. 002 및 DB 담당자와 합의할 항목

1. `(record_id, ai_model)` 조합에 **UNIQUE 제약**을 적용한다. 캐시 정책의 정합성 근거이며, 동시 요청 시 중복 저장을 방지한다.
2. `AIAnalysisResult.heatmap_url`을 `nullable=True`로 변경한다. (현재 `nullable=False`이나 `predict()`가 heatmap을 반환하지 않아 저장 불가)
3. 저장 시각 필드명은 DB `created_at`, API `predicted_at`으로 통일한다. (002 규약 채택)
4. 001 단건 응답과 002 `items[]`는 동일한 결과 필드명·타입을 사용한다. `cached`는 001 전용 메타 필드로 둔다.
5. 공통 오류 메시지와 `504 Gateway Timeout` 처리 방식을 001·002에서 동일하게 적용한다.
6. `confidence`의 의미를 **'폐렴일 확률'** 로 확정한다. (`predict()` 주석의 `max(p, 1-p)` 대안을 채택할 경우 001·002 동시 변경 필요)
7. 001·002가 같은 파일 4개를 사용하므로 **구현 담당 구간 분리 또는 병합 순서**를 사전 조율한다.
8. `is_pneumonia` 판정 임계값 `0.5`가 NFR-PRED-001의 Recall ≥ 0.90 측정 기준과 동일한지 확인한다.
