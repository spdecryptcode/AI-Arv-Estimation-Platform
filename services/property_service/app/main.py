import sys
import os
from pathlib import Path

# make common importable
sys.path.append(str(Path(__file__).resolve().parents[2] / "common"))

from fastapi import FastAPI, Depends, HTTPException, status, Request
import json
from prometheus_fastapi_instrumentator import Instrumentator
import httpx
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from common.db import get_session
from common.security import decode_token
from common.cache import client as redis_client
from . import crud, schemas
from fastapi import BackgroundTasks

# authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # token endpoint just for documentation

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return payload


def get_current_superuser(user: dict = Depends(get_current_user)):
    if not user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
    return user

app = FastAPI(title="property_service")
# add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health():
    return {"status": "ok", "db": "ok", "redis": "ok"}


@app.post("/properties", response_model=schemas.PropertyOut)
async def create_property(prop: schemas.PropertyCreate, db: AsyncSession = Depends(get_session), user: dict = Depends(get_current_superuser)):
    # only superusers may create/update properties
    return await crud.create_property(db, prop.address)


@app.get("/properties", response_model=list[schemas.PropertyOut])
async def list_properties(limit: int = 50, db: AsyncSession = Depends(get_session)):
    return await crud.list_properties(db, limit)


# simple full-text search using MeiliSearch
@app.get("/properties/search", response_model=schemas.SearchResults)
async def properties_search(q: str, limit: int = 20):
    try:
        from common.meili import search_properties as meili_search
        result = meili_search(q, limit)
        # return the raw result, FastAPI will validate against SearchResults
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties/{id}", response_model=schemas.PropertyOut)
async def get_property(id: str, db: AsyncSession = Depends(get_session)):
    prop = await crud.get_property(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@app.get("/properties/{id}/comps", response_model=list[schemas.PropertyOut])
async def get_comps(id: str, limit: int = 5, db: AsyncSession = Depends(get_session)):
    """Return a set of comparable properties based on address similarity.

    This is a simple placeholder that searches Meili using the target
    property's address and then loads the matching record details from the
    database, excluding the subject itself.  A real implementation would
    incorporate geospatial distance, timeouts, and filtering logic.
    """
    prop = await crud.get_property(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    # perform free-text search on Meili
    from common.meili import search_properties as meili_search
    result = meili_search(prop.address, limit + 1)
    hits = [h for h in result.get("hits", []) if h.get("id") != id]
    comps = []
    for hit in hits[:limit]:
        p = await crud.get_property(db, hit.get("id"))
        if p:
            comps.append(p)
    return comps


@app.get("/properties/{id}/arv", response_model=schemas.ARVResult)
async def get_property_arv(id: str, request: Request, db: AsyncSession = Depends(get_session), user: dict = Depends(get_current_user)):
    """Proxy to ML service to compute ARV for a property."""
    prop = await crud.get_property(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # simple caching: if we already computed an ARV recently, return it
    cache_key = f"arv:{id}"
    cached = await redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            # fall back to normal path if cache entry is malformed
            pass

    # call ML service, forward the Authorization header from incoming request
    ml_url = os.getenv("ML_SERVICE_URL", "http://ml_service:8003")
    auth_header = request.headers.get("Authorization")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print(f"[proxy] calling ML {ml_url}/ml/arv auth={auth_header}")
            resp = await client.post(
                f"{ml_url}/ml/arv",
                json={"property_id": id},
                headers={"Authorization": auth_header} if auth_header else {},
            )
            print("[proxy] ml resp", resp.status_code, resp.text)
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="Timeout contacting ML service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"ML service error {resp.status_code}")
    result = resp.json()
    # store in cache (TTL configurable via environment variable)
    ttl = int(os.getenv("ARV_CACHE_TTL", "300"))
    await redis_client.set(cache_key, json.dumps(result), ex=ttl)
    return result


@app.get("/ml/models")
async def proxy_ml_models(request: Request, user: dict = Depends(get_current_user)):
    """Retrieve available ML models by forwarding to the ml_service."""
    ml_url = os.getenv("ML_SERVICE_URL", "http://ml_service:8003")
    auth_header = request.headers.get("Authorization")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ml_url}/ml/models",
            headers={"Authorization": auth_header} if auth_header else {},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"ML service error {resp.status_code}")
    return resp.json()


@app.post("/properties/arv_batch")
async def proxy_arv_batch(request: Request, payload: dict, user: dict = Depends(get_current_user)):
    """Forward batch ARV requests to ml_service."""
    ml_url = os.getenv("ML_SERVICE_URL", "http://ml_service:8003")
    auth_header = request.headers.get("Authorization")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ml_url}/ml/arv_batch",
            json=payload,
            headers={"Authorization": auth_header} if auth_header else {},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"ML service error {resp.status_code}")
    return resp.json()


@app.post("/ml/retrain")
async def proxy_retrain(request: Request, user: dict = Depends(get_current_user)):
    """Proxy the retrain trigger to the ml_service."""
    ml_url = os.getenv("ML_SERVICE_URL", "http://ml_service:8003")
    auth_header = request.headers.get("Authorization")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ml_url}/ml/retrain",
            headers={"Authorization": auth_header} if auth_header else {},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"ML service error {resp.status_code}")
    return resp.json()


@app.post("/properties/{id}/report")
async def proxy_report(id: str, request: Request, db: AsyncSession = Depends(get_session), user: dict = Depends(get_current_user)):
    """Forward report generation request to report_service."""
    prop = await crud.get_property(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    rs_url = os.getenv("REPORT_SERVICE_URL", "http://report_service:8004")
    auth_header = request.headers.get("Authorization")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{rs_url}/reports",
            json={"property_id": id},
            headers={"Authorization": auth_header} if auth_header else {},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Report service error {resp.status_code}")
    return resp.json()


@app.get("/properties/{id}/report_status/{task_id}")
async def proxy_report_status(id: str, task_id: str, request: Request, db: AsyncSession = Depends(get_session), user: dict = Depends(get_current_user)):
    prop = await crud.get_property(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    rs_url = os.getenv("REPORT_SERVICE_URL", "http://report_service:8004")
    auth_header = request.headers.get("Authorization")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{rs_url}/reports/{task_id}",
            headers={"Authorization": auth_header} if auth_header else {},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Report service error {resp.status_code}")
    return resp.json()


@app.post("/properties/{id}/arv_async")
async def request_property_arv_async(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """Request an asynchronous ARV computation and return a Celery task ID.

    This mirrors `/ml/jobs` but is convenient for clients that only talk to the
    property service.
    """
    prop = await crud.get_property(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    ml_url = os.getenv("ML_SERVICE_URL", "http://ml_service:8003")
    auth_header = request.headers.get("Authorization")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ml_url}/ml/jobs",
            json={"property_id": id},
            headers={"Authorization": auth_header} if auth_header else {},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"ML service error {resp.status_code}")
    return resp.json()


@app.get("/properties/{id}/arv_status/{task_id}")
async def get_property_arv_status(
    id: str,
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """Proxy job status query to the ML service.

    Verifies the property exists before forwarding the request.
    """
    prop = await crud.get_property(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    ml_url = os.getenv("ML_SERVICE_URL", "http://ml_service:8003")
    auth_header = request.headers.get("Authorization")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ml_url}/ml/jobs/{task_id}",
            headers={"Authorization": auth_header} if auth_header else {},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"ML service error {resp.status_code}")
    return resp.json()


@app.put("/properties/{id}", response_model=schemas.PropertyOut)
async def update_property(id: str, prop: schemas.PropertyUpdate, db: AsyncSession = Depends(get_session), user: dict = Depends(get_current_superuser)):
    updated = await crud.update_property(db, id, prop.address)
    if not updated:
        raise HTTPException(status_code=404, detail="Property not found")
    return updated


# this will allow import tasks to be kicked off asynchronously
@app.post("/properties/import")
async def import_properties(payload: schemas.ImportRequest, user: dict = Depends(get_current_superuser)):
    """Trigger a CSV ingestion via Celery and return an acknowledgement.

    If no filepath is provided the endpoint uses the default `/app/data/sample_properties.csv`.
    """
    from common.tasks import ingest_properties_csv
    path = payload.filepath or "/app/data/sample_properties.csv"
    # launch the task in the background
    task = ingest_properties_csv.delay(path)
    return {"status": "queued", "task_id": task.id, "filepath": path}


@app.delete("/properties/{id}")
async def delete_property(id: str, db: AsyncSession = Depends(get_session), user: dict = Depends(get_current_superuser)):
    success = await crud.delete_property(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"status": "deleted"}
