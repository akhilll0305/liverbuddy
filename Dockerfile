# --- build the React UI ---
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# --- Python API serving /api and the built UI at / ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_SYSTEM_PYTHON=1 LB_ROOT=/app
RUN pip install --no-cache-dir uv==0.9.18

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --no-cache ".[gemini]"

COPY evals ./evals
COPY docs ./docs
COPY artifacts/models ./artifacts/models
COPY --from=web /web/dist ./web/dist

RUN useradd --create-home liverbuddy && mkdir -p /app/data /app/artifacts/index && chown -R liverbuddy /app
USER liverbuddy

EXPOSE 8000
CMD ["liverbuddy", "serve", "--host", "0.0.0.0", "--port", "8000"]
