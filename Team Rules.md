# Team Rules

## **1. 코어 타임**

- 평일 오후 3시 20분부터 오후 4시까지를 기본 코어 타임으로 운영
- 코어 타임에는 팀 프로젝트 관련 작업, 진행 상황 공유, 이슈 논의 진행
- 추가 회의가 필요한 경우 팀원들과 사전에 일정 조율
- 코어 타임 동안에는 가능한 한 팀 연락 채널과 회의에 참여
- 개인 작업이 필요한 경우에도 현재 작업 상태와 완료 목표 공유

## **2. 회의 방식**

- 회의 전 논의할 안건을 팀 채널 또는 Notion에 미리 작성
- 회의 시작 시 각자 진행 상황, 문제점, 다음 작업을 간단히 공유
- 한 명이 회의 내용을 기록하고, 회의 종료 후 결정 사항 정리
- 의견이 다를 경우 개인적인 선호보다 프로젝트 요구사항과 구현 가능성을 기준으로 논의
- 확정된 내용은 구두로만 남기지 않고 Notion 또는 GitHub Issue에 기록
- 회의 종료 전 담당자와 마감일을 명확히 지정

## **3. 불참 및 지각 공유**

- 코어 타임 또는 회의에 참석하기 어려운 경우 가능한 한 사전에 팀 채널에 공유
- 불참 사유와 함께 현재 작업 상태, 전달 사항, 예상 복귀 시점 작성
- 갑작스러운 상황으로 사전 공유가 어려운 경우 확인 가능한 시점에 바로 안내
- 불참으로 인해 작업 일정에 영향이 발생하는 경우 담당 업무 재조정 요청
- 장기간 작업이 어려운 경우 팀장과 팀원들에게 미리 공유

## **4. Git Branch 규칙**

- `main` 브랜치는 항상 실행 가능한 안정적인 상태로 유지
- 모든 작업은 별도의 브랜치를 생성한 뒤 진행
- 하나의 브랜치에서는 하나의 기능 또는 하나의 작업만 수행
- 브랜치 이름은 작업 목적이 드러나도록 작성

브랜치 이름 형식:

```
feat/기능명
fix/수정내용
docs/문서내용
refactor/리팩토링내용
test/테스트내용
chore/환경설정내용
```

예시:

```
feat/patient-api
feat/model-serving
fix/image-upload-error
docs/team-rules
chore/docker-setup
```

## **5. Commit Message 규칙**

- 커밋 메시지는 변경 내용을 한눈에 알 수 있도록 작성
- 하나의 커밋에는 하나의 논리적인 변경만 포함
- 의미 없는 메시지 사용 금지
- 작성 하는 메세지 가장 앞에 이슈번호 [#숫자] 를 작성
- “” 닫기 전에 #이슈번호를 작성하면 해당 이슈 번호로 추적이 가능

사용하지 않는 예시:

```
수정
완료
작업함
update
test
```

권장 형식:

```
타입: 변경 내용
```

사용 가능한 타입:

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
refactor: 기능 변경 없는 코드 구조 개선
test: 테스트 코드 추가 또는 수정
chore: 설정, 패키지, Docker 등 개발 환경 변경
style: 코드 동작과 무관한 형식 수정
```

예시:

```
feat: add pneumonia prediction endpoint
fix: handle invalid image file upload
docs: add team collaboration rules
chore: add Dockerfile and environment settings
```

## **6. Pull Request 규칙**

- 작업 완료 후 자신의 브랜치를 원격 저장소에 push하고 Pull Request 생성
- Pull Request 제목은 commit message와 동일한 형식으로 작성
- Pull Request 본문에는 작업 내용, 테스트 방법, 관련 이슈 작성
- 큰 작업은 가능한 한 작은 단위로 나누어 Pull Request 생성
- 리뷰가 완료되기 전 임의로 merge하지 않음
- 최소 1명 이상의 팀원 리뷰 후 merge
- merge 전 최신 `main` 브랜치와 충돌 여부 확인
- merge 완료 후 사용한 브랜치는 삭제

Pull Request 본문 예시:

```markdown
## 작업 내용

- 폐렴 판독 이미지 업로드 API 구현
- 모델 추론 결과를 JSON 형태로 반환
- 잘못된 파일 형식에 대한 예외 처리 추가

## 테스트 방법

1. FastAPI 서버 실행
2. `/docs` 접속
3. `/predict`에 X-ray 이미지 업로드
4. prediction과 probability 응답 확인

## 관련 이슈

Closes #12
```

## **7. 코드 리뷰 규칙**

- 코드를 작성한 사람을 평가하지 않고 코드와 구현 방식만 검토
- 리뷰 의견은 문제점, 이유, 수정 방향 순서로 작성
- 단순히 “수정해주세요”라고 작성하지 않고 왜 수정이 필요한지 설명
- 중요한 오류와 선택적 개선 사항을 구분
- 리뷰를 받은 사람은 모든 의견을 확인하고 수정 여부를 답변
- 의견을 반영하지 않는 경우 그 이유를 설명
- 긴급하지 않은 개인 취향의 수정 요구는 지양
- 보안, 예외 처리, API 응답, 데이터 검증, 테스트 여부를 우선 확인

리뷰 표현 예시:

```
현재 이미지 확장자만 확인하고 실제 MIME type은 검증하지 않고 있습니다.
잘못된 파일이 업로드될 가능성이 있으므로 Content-Type 검증을 추가하는 것이 좋겠습니다.
```

리뷰 구분:

```
[필수] 오류, 보안, 실행 실패, 요구사항 미충족
[제안] 가독성, 구조 개선, 유지보수성 개선
[질문] 구현 의도 확인
```

## **8. main 브랜치 직접 Push 금지**

- `main` 브랜치에서는 직접 코드를 작성하거나 push하지 않음
- 모든 변경 사항은 작업 브랜치와 Pull Request를 통해 반영
- 긴급 수정도 `fix/작업명` 브랜치를 생성하여 진행
- 팀장도 동일한 규칙 적용
- 단, 프로젝트 최초 템플릿 업로드와 팀 전체 합의가 있는 긴급 상황은 예외 가능

금지 예시:

```bash
git switch main
git add .
git commit -m "feat: add api"
git push origin main
```

권장 방식:

```bash
git switch -c feat/patient-api
git add .
git commit -m "feat: add patient api"
git push -u origin feat/patient-api
```

## **9. Conflict 해결 방식**

- conflict가 발생하면 해당 코드를 작성한 팀원과 먼저 확인
- 임의로 다른 팀원의 코드를 삭제하지 않음
- conflict 해결 전 현재 변경 사항을 commit 또는 stash
- 최신 `main` 브랜치를 가져온 뒤 자신의 브랜치에서 해결
- conflict 해결 후 기능이 정상적으로 작동하는지 다시 테스트
- 해결 내용이 복잡한 경우 Pull Request에 해결 과정을 기록

권장 흐름:

```bash
git switch main
git pull origin main
git switch 작업브랜치
git merge main
```

충돌 파일 수정 후:

```bash
git add .
git commit -m "fix: resolve merge conflict with main"
git push
```

Conflict 해결 원칙:

```
1. 양쪽 코드의 의도 확인
2. 필요한 코드만 통합
3. 실행 및 테스트
4. 팀원에게 해결 결과 공유
```

## **10. 업무 기록 방식**

- 모든 업무는 Notion 또는 GitHub Issue에 기록
- 작업 시작 전 담당자, 작업 내용, 마감일을 작성
- 작업 중 발생한 문제와 결정 사항 기록
- 작업 완료 후 결과, 관련 PR, 테스트 여부 업데이트
- 구두 또는 메신저에서 결정된 내용도 문서에 반영
- 개인 로컬 환경에만 정보를 남기지 않음

권장 업무 기록 항목:

```
작업명
담당자
상태
시작일
마감일
관련 브랜치
관련 Issue
관련 Pull Request
진행 내용
문제점
다음 작업
```

작업 상태 예시:

```
To Do
In Progress
Review
Done
Blocked
```

일일 작업 기록 예시:

```markdown
### 2026-07-13

담당자: OOO
작업: FastAPI 프로젝트 구조 확인 및 서버 실행
상태: Done

완료 내용:
- 가상환경 생성
- 패키지 설치
- FastAPI 개발 서버 실행 확인

문제점:
- 초기 실행 시 FastAPI app 탐색 실패

해결:
- main.py에 app 객체 생성 후 실행 경로 지정

다음 작업:
- 환자 조회 API 구현
```

## **11. 공통 협업 원칙**

- 작업에 문제가 생기면 숨기지 않고 빠르게 공유
- 정해진 마감일을 지키기 어려운 경우 사전에 안내
- 다른 팀원의 코드를 수정할 때 변경 이유를 공유
- 기능 구현보다 팀 전체가 이해할 수 있는 코드와 문서를 우선
- 담당자가 자리를 비워도 다른 팀원이 이어서 작업할 수 있도록 기록 유지
- 개인 판단으로 프로젝트 구조나 주요 기술을 변경하지 않고 팀 논의 후 결정

# **Git & GitHub Workflow**

```
1. GitHub Issue 또는 Notion에서 작업 확인
2. main 브랜치 최신화
3. 작업 브랜치 생성
4. 기능 구현
5. 로컬 테스트
6. commit
7. 원격 브랜치 push
8. Pull Request 생성
9. 코드 리뷰
10. 수정 사항 반영
11. main 브랜치 merge
12. 작업 브랜치 삭제
13. 업무 기록 업데이트
```