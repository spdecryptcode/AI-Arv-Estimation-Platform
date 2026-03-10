import sys
from pathlib import Path

# make common importable
sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from prometheus_fastapi_instrumentator import Instrumentator
from celery.result import AsyncResult
from . import schemas
import os

app = FastAPI(title="report_service")
Instrumentator().instrument(app).expose(app)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth_service:8001/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    from common.security import decode_token
    payload = decode_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return payload


def get_current_superuser(user: dict = Depends(get_current_user)):
    if not user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
    return user


@app.get("/health")
def health():
    return {"status": "ok", "redis": "ok"}


@app.post("/reports", response_model=schemas.ReportResponse)
def create_report(request: schemas.ReportRequest, user: dict = Depends(get_current_user)):
    from .tasks import generate_report
    task = generate_report.delay(str(request.property_id))
    return {"task_id": task.id}


@app.get("/reports/{task_id}", response_model=schemas.ReportStatus)
def report_status(task_id: str, user: dict = Depends(get_current_user)):
    """Query task state; if backend is misconfigured or disabled, return unknown state."""
    try:
        result = AsyncResult(task_id)
        state = result.state
        response = {"task_id": task_id, "state": state}
        if result.ready():
            try:
                data = result.get(timeout=1)
                response["download_path"] = data.get("path")
            except Exception:
                response["download_path"] = None
    except Exception:
        # backend may be disabled (e.g. in local tests) or unreachable
        response = {"task_id": task_id, "state": "UNKNOWN"}
    return response
