import os
import sys
import pytest
from httpx import AsyncClient

# ensure package import path includes service and common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "common")))
from app.main import app


@pytest.mark.asyncio
async def test_register_login():
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # register a user with a random email to avoid collisions across runs
        import uuid
        random_email = f"user-{uuid.uuid4().hex}@example.com"
        payload = {"email": random_email, "password": "secret"}
        resp = await ac.post("/auth/register", json=payload)
        assert resp.status_code == 200, f"registration failed: {resp.text}"
        data = resp.json()
        assert data["email"] == random_email
        assert "id" in data

        # login should succeed
        resp = await ac.post("/auth/login", json=payload)
        assert resp.status_code == 200
        tok = resp.json()
        assert "access_token" in tok
        assert tok["token_type"] == "bearer"

        # bad login fails
        resp = await ac.post("/auth/login", json={"email": "user1@example.com", "password": "wrong"})
        assert resp.status_code == 401
