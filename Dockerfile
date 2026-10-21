FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_SYSTEM_PYTHON=1
RUN pip install --no-cache-dir uv==0.9.18

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --no-cache ".[ui,gemini]"

COPY app ./app
COPY evals ./evals
COPY docs ./docs
COPY artifacts/models ./artifacts/models

RUN useradd --create-home liverbuddy && mkdir -p /app/data /app/artifacts/index && chown -R liverbuddy /app
USER liverbuddy

EXPOSE 8000 8501
CMD ["liverbuddy", "serve", "--host", "0.0.0.0", "--port", "8000"]
