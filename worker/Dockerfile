FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

# ai 그룹 의존성만 설치 (FastAPI 제외). torch/torchvision은 CPU-only 인덱스에서 별도 설치.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv \
    && uv export --frozen --no-dev --no-hashes --no-emit-project --only-group ai \
        | grep -viE '^(torch|torchvision|triton|pytorch-triton)([=<>~!; ]|$)|^(nvidia|cuda)-' \
        > /tmp/ai_requirements.txt \
    && uv pip install --python /opt/venv redis -r /tmp/ai_requirements.txt \
    && uv pip install --python /opt/venv \
        --index-url https://download.pytorch.org/whl/cpu \
        torch torchvision

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY worker/ ./worker/

CMD ["python", "-m", "worker.main"]
