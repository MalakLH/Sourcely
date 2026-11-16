FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including semgrep
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY services/scanner_service/pyproject.toml .
COPY services/scanner_service/app ./app

# Install Python dependencies
RUN pip install --no-cache-dir -e .

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
