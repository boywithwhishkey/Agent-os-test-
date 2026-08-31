FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

# The "persistence" extra (asyncpg + redis) is REQUIRED, not optional, for any
# deployment that sets AGENT_OS_*_BACKEND=postgres or AGENT_OS_QUEUE_BACKEND=redis.
# Installing the bare package left the image without asyncpg, so a durable-backend
# deployment would start and then fail at first query with
# "asyncpg is required for PostgreSQL persistence".
RUN pip install --no-cache-dir ".[persistence]"

# Migrations are applied manually (nothing in app startup runs them), so the
# runner and the .sql files have to exist inside the image to be runnable
# against the attached database.
COPY migrations ./migrations
COPY scripts ./scripts

EXPOSE 8000

# Render (and most PaaS hosts) inject $PORT; fall back to 8000 elsewhere.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
