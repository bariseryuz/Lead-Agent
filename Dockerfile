FROM node:20-slim

# Install Python + venv tooling (no secrets baked into image)
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-venv python3-pip build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend deps
COPY backend/requirements.txt ./backend/requirements.txt
# Debian 12 enforces PEP 668; install deps into a venv instead of system python.
RUN python3 -m venv /opt/venv \
  && /opt/venv/bin/pip install --upgrade pip \
  && /opt/venv/bin/pip install --no-cache-dir -r ./backend/requirements.txt

# Frontend deps (use lockfile if present)
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --include=dev

# Copy the rest of the repo and build frontend
COPY . .
RUN cd frontend && npm run build

ENV PYTHONPATH=/app/backend
ENV PATH="/opt/venv/bin:${PATH}"

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

