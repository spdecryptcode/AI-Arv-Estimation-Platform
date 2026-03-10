from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import models

async def get_property(db: AsyncSession, prop_id):
    result = await db.execute(select(models.Property).filter(models.Property.id == prop_id))
    return result.scalars().first()

async def list_properties(db: AsyncSession, limit: int = 50):
    result = await db.execute(select(models.Property).limit(limit))
    return result.scalars().all()

async def create_property(db: AsyncSession, address: str):
    prop = models.Property(address=address)
    db.add(prop)
    await db.commit()
    await db.refresh(prop)
    # asynchronously index in Meili (fire-and-forget)
    try:
        from common.meili import index_property
        index_property({
            "id": str(prop.id),
            "address": prop.address,
        })
    except Exception as e:
        # log so tests and devs can see if something goes wrong
        print("[crud] meili indexing failed", e)
    return prop


async def update_property(db: AsyncSession, prop_id: str, address: str):
    prop = await get_property(db, prop_id)
    if not prop:
        return None
    prop.address = address
    await db.commit()
    await db.refresh(prop)
    try:
        from common.meili import index_property
        index_property({
            "id": str(prop.id),
            "address": prop.address,
        })
    except Exception as e:
        print("[crud] meili update failed", e)
    return prop


async def delete_property(db: AsyncSession, prop_id: str):
    prop = await get_property(db, prop_id)
    if not prop:
        return False
    await db.delete(prop)
    await db.commit()
    try:
        from common.meili import delete_property
        delete_property(prop_id)
    except Exception as e:
        print("[crud] meili delete failed", e)
    return True
