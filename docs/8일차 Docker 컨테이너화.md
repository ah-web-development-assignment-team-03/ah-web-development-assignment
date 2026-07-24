# 8일차 Docker 컨테이너화

## **Docker Compose 이미지 빌드 및 컨테이너 실행**

Docker Compose 명령어를 사용하여 FastAPI 애플리케이션 이미지를 빌드하고 FastAPI와 MySQL 컨테이너를 실행했습니다.

실행 결과 FastAPI 이미지는 정상적으로 빌드되었으며, FastAPI와 MySQL 컨테이너가 모두 `healthy` 상태인 것을 확인했습니다.

![스크린샷 2026-07-24 오후 3.33.37.png](8%EC%9D%BC%EC%B0%A8%20Docker%20%EC%BB%A8%ED%85%8C%EC%9D%B4%EB%84%88%ED%99%94/%E1%84%89%E1%85%B3%E1%84%8F%E1%85%B3%E1%84%85%E1%85%B5%E1%86%AB%E1%84%89%E1%85%A3%E1%86%BA_2026-07-24_%E1%84%8B%E1%85%A9%E1%84%92%E1%85%AE_3.33.37.png)

## **Docker Desktop 실행 결과**

Docker Desktop에서도 FastAPI와 MySQL 컨테이너가 모두 실행 중인 것을 확인했습니다.

- FastAPI: 호스트의 8000번 포트와 컨테이너의 8000번 포트 연결
- MySQL: 호스트의 3306번 포트와 컨테이너의 3306번 포트 연결

![스크린샷 2026-07-24 오후 3.34.01.png](8%EC%9D%BC%EC%B0%A8%20Docker%20%EC%BB%A8%ED%85%8C%EC%9D%B4%EB%84%88%ED%99%94/%E1%84%89%E1%85%B3%E1%84%8F%E1%85%B3%E1%84%85%E1%85%B5%E1%86%AB%E1%84%89%E1%85%A3%E1%86%BA_2026-07-24_%E1%84%8B%E1%85%A9%E1%84%92%E1%85%AE_3.34.01.png)

## **실행 명령어**

```bash
docker compose --env-file .env.example up --build -d
docker compose --env-file .env.example ps
```

## **실행 결과**

- FastAPI 이미지 빌드 성공
- FastAPI 컨테이너 실행 성공
- MySQL 컨테이너 실행 성공
- FastAPI healthcheck 통과
- MySQL healthcheck 통과
- FastAPI `-reload` 옵션 적용