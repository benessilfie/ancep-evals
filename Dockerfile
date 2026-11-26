FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

COPY docs ./docs

ENV PATH="/app/.venv/bin:$PATH"
CMD ["sh", "-c", "uvicorn submission_evals.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
