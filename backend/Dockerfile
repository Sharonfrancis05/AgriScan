# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

# libgl1/libglib2.0-0 are required by opencv-python-headless at import time
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
# CPU-only torch wheels by default (much smaller image); see docs/setup_dev.md for the GPU variant.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1 \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/models_store /app/storage/uploads /app/storage/reports

EXPOSE 8000

FROM base AS dev
RUN pip install --no-cache-dir -r requirements-dev.txt
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

FROM base AS prod
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
