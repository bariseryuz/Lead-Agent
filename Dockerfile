FROM node:20-slim

# Install Python + pip (no secrets baked into image)
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-pip \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend deps
COPY backend/requirements.txt ./backend/requirements.txt
RUN python3 -m venv /app/venv \
  && /app/venv/bin/pip install --upgrade pip \
  && /app/venv/bin/pip install -r ./backend/requirements.txt

# Frontend deps (use lockfile if present)
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --include=dev

# Copy the rest of the repo and build frontend
COPY . .
RUN cd frontend && npm run build

ENV PYTHONPATH=/app/backend

EXPOSE 8000
CMD ["sh", "-c", "/app/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

