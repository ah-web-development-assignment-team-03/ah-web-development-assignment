# syntax=docker/dockerfile:1

# =============================================================================
# builder — 의존성을 /opt/venv 에 설치. torch/torchvision 은 CPU 전용 휠로.
# =============================================================================
FROM python:3.13-slim AS builder

# uv 바이너리 (astral 공식 이미지에서 복사)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# C 확장 컴파일용 빌드 도구 (asyncmy 등은 aarch64 휠이 없어 소스 빌드됨).
# builder 스테이지에만 두므로 runtime 이미지는 슬림하게 유지된다.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /build
COPY pyproject.toml uv.lock ./

# 의존성 전용 venv 를 /app 밖(/opt/venv)에 만든다.
# → compose 가 프로젝트 루트를 /app 에 bind mount 해도 패키지가 사라지지 않는다.
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# 1) torch/torchvision(및 CUDA 계열)을 '제외'한 잠금 의존성을 설치.
#    uv.lock 의 torch 는 linux 에서 CUDA(cuda-toolkit, nvidia-*-cu13, triton)를 끌어와
#    이미지가 5GB+ 로 커지므로 여기서 빼고, 아래 2)에서 CPU 휠로 따로 설치한다.
#    (pyproject.toml / uv.lock 은 수정하지 않는다 — 커밋 범위 밖)
RUN uv export --frozen --no-dev --no-hashes --no-emit-project \
      | grep -viE '^(torch|torchvision|triton|pytorch-triton)([=<>~!; ]|$)|^(nvidia|cuda)-' \
      > /tmp/requirements.txt \
    && uv pip install --python /opt/venv -r /tmp/requirements.txt

# 2) torch/torchvision 은 PyTorch CPU 인덱스에서 설치 (CUDA 미포함 → 이미지 대폭 축소).
RUN uv pip install --python /opt/venv \
      --index-url https://download.pytorch.org/whl/cpu \
      torch torchvision

# =============================================================================
# runtime — 슬림 런타임 + venv + 앱 코드(+ 모델 가중치)
# =============================================================================
FROM python:3.13-slim AS runtime

# 런타임 필수 패키지:
#  - curl: compose healthcheck 가 /healthcheck 를 호출
#  - libglib2.0-0: opencv-python-headless(cv2) 런타임 의존
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 빌더에서 만든 의존성 venv 를 그대로 복사 (/app 밖이라 bind mount 에 안 덮인다)
COPY --from=builder /opt/venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 앱 실행에 필요한 것만 COPY.
# ⚠️ worker/ 에는 models/*.pth(5개, 136MB)가 포함되어야 한다
#    — app/main.py 의 `from worker.model import load_models` 가 이를 로드한다.
COPY app/ ./app/
COPY worker/ ./worker/
COPY alembic/ ./alembic/
COPY static/ ./static/
COPY alembic.ini pyproject.toml uv.lock ./

EXPOSE 8000

# compose 는 entrypoint 로 이 CMD 를 덮어쓴다. 이미지 단독 실행 시의 기본값.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
