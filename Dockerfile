# ---------- build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---------- runtime stage ----------
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/    ./app/
COPY static/ ./static/

# These directories are expected to exist; real data comes via volumes
RUN mkdir -p photos .thumbnails

EXPOSE 8000

# Use 2 workers for a typical home server; bump if your machine has more cores
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
