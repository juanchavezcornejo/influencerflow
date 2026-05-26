FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      curl \
      ca-certificates \
      git \
    && rm -rf /var/lib/apt/lists/*

# uv is the package manager.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install deps first for better layer caching.
COPY pyproject.toml ./
COPY uv.lock* ./
RUN uv sync --frozen 2>/dev/null || uv sync

# Download face_recognition models
RUN uv run pip install git+https://github.com/ageitgey/face_recognition_models

COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
