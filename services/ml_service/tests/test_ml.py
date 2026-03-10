import os
# avoid needing a real redis server when running tests locally
os.environ.setdefault("REDIS_URL", "memory://")
import sys
import pytest
from httpx import AsyncClient

# ensure imports work by adding service root and workspace root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(workspace_root)
sys.path.append(os.path.join(workspace_root, "common"))

import tempfile, os, pathlib

# the actual app import will be done within the test after path setup


@pytest.mark.asyncio
async def test_ml_endpoints(monkeypatch):
    # import local modules now that sys.path is configured
    from app.main import app
    from common.security import create_access_token
    from app import schemas, model

    # set up a temporary model store and ensure our helper sees it
    tmp = tempfile.TemporaryDirectory()
    monkeypatch.setattr(model, 'MODEL_STORE_PATH', pathlib.Path(tmp.name))
    # clear cached model list so endpoint picks up new path
    try:
        model.available_models.cache_clear()
    except AttributeError:
        pass
    # create a dummy model file
    open(os.path.join(tmp.name, 'dummy_model.bin'), 'w').close()

    token = create_access_token({"user_id": "user1"})
    headers = {"Authorization": f"Bearer {token}"}

    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # health
        resp = await ac.get("/health")
        assert resp.status_code == 200
        # models listing should show our dummy file
        resp = await ac.get("/ml/models", headers=headers)
        assert resp.status_code == 200
        assert "dummy_model.bin" in resp.json().get("models", [])

        # metric should reflect at least one model
        metr = await ac.get("/metrics")
        text = metr.text
        assert "ml_models_loaded" in text
        # value should be >=1
        for line in text.splitlines():
            if line.startswith("ml_models_loaded"):
                parts = line.split()
                assert float(parts[-1]) >= 1.0
                break

        # arv
        resp = await ac.post("/ml/arv", json={"property_id": "00000000-0000-0000-0000-000000000000"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "min" in data and "max" in data
        # verify compute_arv helper directly
        raw = model.compute_arv("00000000-0000-0000-0000-000000000000")
        assert raw == data

        # batch inference
        resp = await ac.post("/ml/arv_batch", json={"property_ids": [
            "00000000-0000-0000-0000-000000000000",
            "11111111-1111-1111-1111-111111111111"
        ]}, headers=headers)
        assert resp.status_code == 200
        batch = resp.json()
        assert isinstance(batch, list) and len(batch) == 2
        assert batch[0] == model.compute_arv("00000000-0000-0000-0000-000000000000")

        # retrain endpoint - patch celery to avoid backend errors in tests
        from importlib import reload
        import common.celery_app as ca
        # default schedule key is 'retrain-models'
        reload(ca)
        assert "retrain-models" in ca.celery.conf.beat_schedule
        # test that env var changes schedule parsing
        os.environ["RETRAIN_CRON"] = "*/5 * * * *"
        reload(ca)
        sched = ca.celery.conf.beat_schedule.get("retrain-models")
        assert sched is not None
        # check the crontab instance has correct minute field
        assert sched["schedule"]._orig_minute == "*/5"
        tmp = tempfile.TemporaryDirectory()
        monkeypatch.setattr(model, 'MODEL_STORE_PATH', pathlib.Path(tmp.name))

        # monkeypatch celery send_task so we don't hit a missing backend
        from app import main as appmod
        appmod.celery.send_task = lambda *args, **kwargs: type("T", (), {"id": "dummy"})()

        resp = await ac.post("/ml/retrain", headers=headers)
        assert resp.status_code == 200
        rein_resp = schemas.RetrainResponse(**resp.json())
        # directly call retrain task to simulate completion
        from app.tasks import retrain_models
        result = retrain_models()
        assert 'path' in result
        assert pathlib.Path(result['path']).exists()

        # narrative (uses Ollama helper; may return placeholder text)
        resp = await ac.post("/ml/narrative", json={"property_id": "00000000-0000-0000-0000-000000000000"}, headers=headers)
        assert resp.status_code == 200
        narr = resp.json().get("narrative", "")
        assert isinstance(narr, str)
        assert "narrative" in narr or narr.startswith("[narrative")
        # unauthorized
        resp = await ac.post("/ml/arv", json={"property_id": "00000000-0000-0000-0000-000000000000"})
        assert resp.status_code == 401

        # test job submission (does not validate execution)
        resp = await ac.post("/ml/jobs", json={"property_id": "00000000-0000-0000-0000-000000000000"}, headers=headers)
        assert resp.status_code == 200
        job_resp = schemas.JobResponse(**resp.json())
        task_id = job_resp.task_id

        # check job status endpoint
        resp = await ac.get(f"/ml/jobs/{task_id}", headers=headers)
        assert resp.status_code == 200
        status_data = schemas.JobStatus(**resp.json())
        assert status_data.task_id == task_id
        assert isinstance(status_data.state, str)
