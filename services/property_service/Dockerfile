FROM python:3.11-slim-bookworm AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bookworm
WORKDIR /app
# copy libs and bin
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# reinstall requirements to guarantee availability
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# make sure psycopg2 and alembic are installed for migrations later
RUN pip install --no-cache-dir psycopg2-binary alembic

# install test dependencies explicitly so pytest is available in the container
RUN pip install --no-cache-dir pytest httpx pytest-asyncio

COPY . .
USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
