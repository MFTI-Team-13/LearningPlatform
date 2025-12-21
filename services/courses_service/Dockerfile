FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/courses_service/pyproject.toml /app/pyproject.toml
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -e .

COPY shared                        /app/shared
COPY services/courses_service/app     /app/app
COPY services/courses_service/migrations /app/migrations
COPY services/courses_service/alembic.ini /app/alembic.ini

RUN pip install --no-cache-dir \
      alembic asyncpg "psycopg[binary]" uvicorn debugpy watchfiles \
      pytest pytest-asyncio httpx

ENV PYTHONPATH="/app:/app/shared"

EXPOSE 8001
CMD ["uvicorn", "app.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8001"]
