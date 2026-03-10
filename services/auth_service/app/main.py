import sys
from pathlib import Path

# ensure common package can be imported
sys.path.append(str(Path(__file__).resolve().parents[2] / "common"))

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.db import get_session
from . import crud, schemas
from .core import security

app = FastAPI(title="auth_service")
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health():
    return {"status": "ok", "db": "ok", "redis": "ok"}


@app.post("/auth/register", response_model=schemas.UserOut)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_session)):
    existing = await crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_user = await crud.create_user(db, user)
    return db_user


@app.post("/auth/login", response_model=schemas.Token)
async def login(form_data: schemas.UserCreate, db: AsyncSession = Depends(get_session)):
    user = await crud.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={
        "user_id": str(user.id),
        "is_superuser": user.is_superuser,
    })
    return {"access_token": access_token, "token_type": "bearer"}
