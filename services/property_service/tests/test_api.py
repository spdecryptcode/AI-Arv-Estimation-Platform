import os
import sys
import pytest
from httpx import AsyncClient
import json

# ensure the service package is on the path
# service code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# make common package importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "common")))
from app.main import app


@pytest.mark.asyncio
async def test_property_crud_and_search(monkeypatch):
    # Use real Meili instance – wipe any existing documents so tests start clean
    from common.meili import meili_client
    try:
        meili_client.index("properties").delete_all_documents()
    except Exception:
        # if the index doesn't exist yet, create it explicitly
        meili_client.create_index("properties", {"primaryKey": "id"})

    from httpx import ASGITransport
    # create a dummy token using shared secret
    from common.security import create_access_token
    # mark as superuser so we can perform write operations
    token = create_access_token({"user_id": "test-user", "is_superuser": True})
    auth_headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # metrics endpoint should exist and be accessible without auth
        mresp = await ac.get("/metrics")
        assert mresp.status_code == 200
        assert "python_gc_objects_collected_total" in mresp.text

        # requests without token should be rejected on protected routes
        resp = await ac.post("/properties", json={"address": "No Auth"})
        assert resp.status_code == 401
        # also update/delete should fail before we create a record
        resp = await ac.put("/properties/doesnotexist", json={"address":"x"})
        assert resp.status_code == 401
        resp = await ac.delete("/properties/doesnotexist")
        assert resp.status_code == 401
        # and ARV proxy without auth should fail as well
        resp = await ac.get("/properties/doesnotexist/arv")
        assert resp.status_code == 401

        # using a non-superuser token should produce 403 on writes
        token2 = create_access_token({"user_id": "normal", "is_superuser": False})
        headers2 = {"Authorization": f"Bearer {token2}"}
        resp = await ac.post("/properties", json={"address":"Forbidden"}, headers=headers2)
        assert resp.status_code == 403

        # verify import endpoint queues a task
        called = {}
        def fake_delay(path):
            called['path'] = path
            class Dummy:
                id = 'fakeid'
            return Dummy()
        import common.tasks
        monkeypatch.setattr(common.tasks.ingest_properties_csv, 'delay', fake_delay)
        resp = await ac.post("/properties/import", json={}, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body['status'] == 'queued'
        assert body['task_id'] == 'fakeid'
        assert called['path'] == "/app/data/sample_properties.csv"

        # create
        resp = await ac.post("/properties", json={"address": "Test 123"}, headers=auth_headers)
        assert resp.status_code == 200
        prop = resp.json()
        prop_id = prop["id"]
        assert prop["address"] == "Test 123"

        # verify that the index helper actually wrote the document; wait briefly
        import asyncio
        found = False
        for _ in range(10):
            docs = meili_client.index("properties").get_documents().results
            if any(d.id == prop_id for d in docs):
                found = True
                break
            await asyncio.sleep(0.1)
        assert found, "document was not added to Meili"

        # create two additional properties to exercise comps endpoint
        resp2 = await ac.post("/properties", json={"address": "Test 456"}, headers=auth_headers)
        assert resp2.status_code == 200
        other1 = resp2.json()["id"]
        resp3 = await ac.post("/properties", json={"address": "Test 789"}, headers=auth_headers)
        assert resp3.status_code == 200
        other2 = resp3.json()["id"]

        # wait for the last document to propagate to Meili
        import asyncio
        for _ in range(20):
            docs = meili_client.index("properties").get_documents().results
            if any(d.id == other2 for d in docs):
                break
            await asyncio.sleep(0.1)

        # search for it through the API
        resp = await ac.get("/properties/search", params={"q": "Test"})
        assert resp.status_code == 200
        data = resp.json()
        # basic metadata according to our schema
        assert data["query"] == "Test"
        assert isinstance(data["limit"], int)
        assert "processingTimeMs" in data
        assert any(d["id"] == prop_id for d in data.get("hits", []))

        # comps should include the two other properties but not the subject
        resp = await ac.get(f"/properties/{prop_id}/comps")
        assert resp.status_code == 200
        comps = resp.json()
        ids = {c["id"] for c in comps}
        assert other1 in ids and other2 in ids

        # ARV proxy should return ML service result
        # clear any existing cache first
        from common.cache import client as redis_client
        await redis_client.delete(f"arv:{prop_id}")

        resp = await ac.get(f"/properties/{prop_id}/arv", headers=auth_headers)
        assert resp.status_code == 200
        arv = resp.json()
        assert arv["property_id"] == prop_id
        assert "min" in arv and "max" in arv
        # cache key should now exist and match the response
        cached = await redis_client.get(f"arv:{prop_id}")
        assert cached is not None
        assert arv == json.loads(cached)

        # models listing should be available through the property service
        resp = await ac.get("/ml/models", headers=auth_headers)
        assert resp.status_code == 200
        assert "placeholder.txt" in resp.json().get("models", [])

        # retrain proxy should forward to ML service
        resp = await ac.post("/ml/retrain", headers=auth_headers)
        assert resp.status_code == 200
        assert "task_id" in resp.json()

        # report proxy should forward to report service
        resp = await ac.post(f"/properties/{prop_id}/report", json={}, headers=auth_headers)
        assert resp.status_code == 200
        assert "task_id" in resp.json()
        report_tid = resp.json()["task_id"]
        resp = await ac.get(f"/properties/{prop_id}/report_status/{report_tid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["task_id"] == report_tid

        # batch ARV via property service
        resp = await ac.post("/properties/arv_batch", json={"property_ids": [prop_id]}, headers=auth_headers)
        assert resp.status_code == 200
        batch = resp.json()
        assert isinstance(batch, list) and batch[0]["property_id"] == prop_id

        # asynchronous ARV submissions and status checks
        resp = await ac.post(f"/properties/{prop_id}/arv_async", json={}, headers=auth_headers)
        assert resp.status_code == 200
        async_data = resp.json()
        assert "task_id" in async_data
        task_id = async_data["task_id"]

        # status should be available through property service proxy
        resp = await ac.get(f"/properties/{prop_id}/arv_status/{task_id}", headers=auth_headers)
        assert resp.status_code == 200
        status_data = resp.json()
        assert status_data["task_id"] == task_id
        assert isinstance(status_data.get("state"), str)

        # ensure unauthorized attempts are blocked
        resp = await ac.post(f"/properties/{prop_id}/arv_async", json={})
        assert resp.status_code == 401
        resp = await ac.get(f"/properties/{prop_id}/arv_status/{task_id}")
        assert resp.status_code == 401

        # update
        resp = await ac.put(f"/properties/{prop_id}", json={"address": "Test 456"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["address"] == "Test 456"
        # wait for the update to be indexed
        import asyncio
        found = False
        for _ in range(10):
            resp = await ac.get("/properties/search", params={"q": "456"})
            if any(d["id"] == prop_id for d in resp.json().get("hits", [])):
                found = True
                break
            await asyncio.sleep(0.1)
        assert found

        # delete
        resp = await ac.delete(f"/properties/{prop_id}", headers=auth_headers)
        assert resp.status_code == 200
        resp = await ac.get("/properties/search", params={"q": "456"})
        assert all(d["id"] != prop_id for d in resp.json().get("hits", [])), "deleted property still in search results"
