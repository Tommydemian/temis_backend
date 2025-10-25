FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /bin/
ADD . /app
WORKDIR /app
# Copy dependency files FIRST (for Docker layer caching)
COPY pyproject.toml uv.lock ./

# Copy application code (changes frequently, won't bust cache)
COPY . .
RUN uv sync --locked
EXPOSE 8080
CMD [ "uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000" ]