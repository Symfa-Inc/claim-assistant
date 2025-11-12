FROM python:3.13-slim

# Prevent Python from writing pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_PORT=8501

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
RUN pip install --upgrade pip setuptools wheel \
    && pip install "uv>=0.4.20" \
    && uv pip install --system .

# Copy application code
COPY src ./src
COPY data ./data
COPY metrics ./metrics

# Default Streamlit command
EXPOSE 8501
CMD ["streamlit", "run", "src/claim_assistant/app.py"]

