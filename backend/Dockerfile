# syntax=docker/dockerfile:1

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final runtime container
FROM python:3.11-slim AS runner

WORKDIR /app

# Create data directory for SQLite volume
RUN mkdir -p /data /data/cache && chmod -R 777 /data

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source
COPY app ./app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////data/app.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
