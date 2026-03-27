FROM python:3.13-slim

# Prevent Python from writing pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libfreetype6 \
        libjpeg62-turbo \
        libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN pip install --upgrade pip setuptools wheel \
    && pip install "uv>=0.4.20" \
    && uv pip install --system .
COPY data ./data
COPY metrics ./metrics

ENV PYTHONPATH=/app/src

EXPOSE 8000
CMD ["uvicorn", "claim_assistant.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
