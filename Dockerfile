FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /bin/

WORKDIR /app
# Copy dependency files FIRST (for Docker layer caching)
COPY pyproject.toml uv.lock ./

RUN uv sync --locked

COPY . .

EXPOSE 8000

CMD [ "uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000" ]