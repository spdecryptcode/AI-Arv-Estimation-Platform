FROM python:3.11-slim-bookworm AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bookworm
WORKDIR /app
# copy both libraries and executables from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# also install requirements again to make sure nothing is missing
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# ensure test requirements are installed (sometimes the multi-stage copy skips them)
RUN pip install --no-cache-dir pytest httpx pytest-asyncio
# explicitly ensure psycopg2 and alembic CLI are present (caching sometimes skips)
RUN pip install --no-cache-dir psycopg2-binary alembic

COPY . .
USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
