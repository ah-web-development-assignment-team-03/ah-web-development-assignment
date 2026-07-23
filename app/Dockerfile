# 1단계: Python 라이브러리 설치
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

# 잠금 파일에서 CUDA/GPU 패키지를 제외한 나머지 의존성을 설치한다.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv \
    && uv export --frozen --no-dev --no-hashes --no-emit-project \
    | grep -viE '^(torch|torchvision|triton|pytorch-triton)([=<>~!; ]|$)|^(nvidia|cuda)-' \
    > /tmp/requirements.txt \
    && uv pip install --python /opt/venv -r /tmp/requirements.txt

# 모델 코드는 CPU(fp32) 추론만 사용하므로 CPU 전용 PyTorch를 설치한다.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /opt/venv \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.13.0+cpu torchvision==0.28.0+cpu


# 2단계: FastAPI 실행 이미지
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
