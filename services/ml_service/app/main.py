import sys
from pathlib import Path

# make common package importable. We try a few candidate roots so that
# imports work both inside Docker (where the repo is mounted at /app) and
# during local testing (where path levels are different).
# __file__ might be /app/app/main.py in container or
# /Users/.../services/ml_service/app/main.py on host.
paths = []
p = Path(__file__).resolve()
# service package itself
paths.append(str(p.parents[1]))
# one level up (likely workspace root outside container)
if len(p.parents) > 2:
    paths.append(str(p.parents[2]))
# also include potential common subdirectories
for candidate in list(paths):
    paths.append(str(Path(candidate) / "common"))
# add each unique path to sys.path
for candidate in dict.fromkeys(paths):
    sys.path.append(candidate)

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge
from pydantic import BaseModel
from common.celery_app import celery
from common.security import decode_token
from fastapi.security import OAuth2PasswordBearer
from . import schemas
from celery.result import AsyncResult
from . import model
import os

app = FastAPI(title="ml_service")
Instrumentator().instrument(app).expose(app)

# custom metric tracking number of models available
models_gauge = Gauge('ml_models_loaded', 'Number of ML model artifacts')

def update_models_gauge():
    models_gauge.set(len(model.available_models()))

# set at startup
update_models_gauge()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth_service:8001/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return payload


def get_current_superuser(user: dict = Depends(get_current_user)):
    if not user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    return user


@app.get("/health")
def health():
    return {"status": "ok", "ml": "ok", "redis": "ok"}


@app.get("/ml/models")
def list_models_endpoint(user: dict = Depends(get_current_user)):
    """Return a list of available model artifacts."""
    models = model.available_models()
    # update our custom metric
    models_gauge.set(len(models))
    return {"models": models}


@app.post("/ml/arv", response_model=schemas.ARVResult)
def compute_arv_endpoint(request: schemas.PropertyIdRequest, user: dict = Depends(get_current_user)):
    # synchronous inference using our model helpers
    return model.compute_arv(str(request.property_id))


@app.post("/ml/arv_batch", response_model=list[schemas.ARVResult])
def compute_arv_batch(request: schemas.BatchRequest, user: dict = Depends(get_current_user)):
    """Compute ARV for a list of property IDs in one call."""
    results = []
    for pid in request.property_ids:
        results.append(model.compute_arv(str(pid)))
    return results


@app.post("/ml/narrative", response_model=schemas.NarrativeResult)
def generate_narrative(request: schemas.PropertyIdRequest, user: dict = Depends(get_current_user)):
    # build a simple prompt based on property id (real implementation would
    # include property details, comps, etc.)
    prompt = f"Write a short narrative description for property {request.property_id}."
    from .ollama import generate as run_ollama
    narrative = run_ollama(prompt)
    return {"property_id": request.property_id, "narrative": narrative}


@app.post("/ml/jobs", response_model=schemas.JobResponse)
def submit_job(request: schemas.PropertyIdRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    task = celery.send_task("services.ml_service.app.tasks.compute_arv_task", args=[request.property_id])
    return {"task_id": task.id}


@app.post("/ml/retrain", response_model=schemas.RetrainResponse)
def retrain_endpoint(user: dict = Depends(get_current_user)):
    """Trigger a retraining job via Celery."""
    task = celery.send_task("services.ml_service.app.tasks.retrain_models")
    return {"task_id": task.id}


@app.get("/ml/jobs/{task_id}", response_model=schemas.JobStatus)
def check_job(task_id: str, user: dict = Depends(get_current_user)):
    """Query the status/result of a previously submitted ML job.

    When the Celery backend is disabled (e.g. during local unit testing) this
    endpoint will return state "UNKNOWN" instead of raising.
    """
    try:
        result = AsyncResult(task_id, app=celery)
        state = result.state
        response = {"task_id": task_id, "state": state}
        if result.ready():
            try:
                response["result"] = result.get(timeout=1)
            except Exception as e:
                response["result_error"] = str(e)
    except Exception:
        response = {"task_id": task_id, "state": "UNKNOWN"}
    return response
