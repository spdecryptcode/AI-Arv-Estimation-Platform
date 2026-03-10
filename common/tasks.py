from .celery_app import celery
import csv
import os
import asyncio
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from common.db import DATABASE_URL

@celery.task
def debug_task(message):
    print(f"Debug: {message}")
    return message

@celery.task
def ingest_properties_csv(filepath: str):
    """Read a CSV of property records and insert into the properties table."""
    # use async engine identical to application
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)

    async def _do_work():
        async with AsyncSession(engine) as session:
            with open(filepath, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # use raw SQL insert to avoid importing app models
                    from sqlalchemy import text
                    await session.execute(
                        text("INSERT INTO properties (id, address) VALUES (:id, :address) "
                             "ON CONFLICT (id) DO UPDATE SET address = EXCLUDED.address"),
                        {"id": row.get('id'), "address": row.get('address')}
                    )
                    # index each record immediately (fire-and-forget)
                    try:
                        from common.meili import index_property
                        index_property({
                            "id": row.get('id'),
                            "address": row.get('address'),
                        })
                    except Exception:
                        pass
            await session.commit()

    asyncio.run(_do_work())
    return f"ingested {filepath}"
