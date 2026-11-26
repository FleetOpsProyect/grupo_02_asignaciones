# syntax=docker/dockerfile:1

# La imagen base se fija por digest (no solo por tag) para que nadie pueda
# sustituirla silenciosamente: "3.12-slim" puede apuntar a bytes distintos
# manana, el digest nunca (OWASP A08 - Software and Data Integrity Failures).
FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN uv sync --frozen --no-dev


FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b AS runtime

RUN groupadd --system app && useradd --system --gid app --no-create-home app

ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--threads", "4", "--no-control-socket", "assignments.main:create_app()"]
