from datetime import datetime, timedelta
import os
from jose import JWTError, jwt

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# symmetric secret shared across services
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    # data is a dict of claims; services may include role flags such as
    # `is_superuser` here.
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
