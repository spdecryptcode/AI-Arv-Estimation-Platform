import os
import sys
# ensure celery doesn't try to connect to a Docker redis host during local tests
os.environ.setdefault("REDIS_URL", "memory://")
import pytest
from httpx import AsyncClient

# service imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# add workspace root (three levels up) and the common subdirectory
ws_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(ws_root)
sys.path.append(os.path.join(ws_root, "common"))
# container path when running inside Docker
sys.path.append("/app/common")
from app.main import app
from common.security import create_access_token


@pytest.mark.asyncio
async def test_report_endpoints(tmp_path):
    token = create_access_token({"user_id": "user1"})
    headers = {"Authorization": f"Bearer {token}"}

    from httpx import ASGITransport
    # prevent Celery from trying to contact Redis by replacing delay method
    from app import tasks as tasks_mod
    tasks_mod.generate_report.delay = lambda *args, **kwargs: type("T", (), {"id": "dummy"})()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # health
        resp = await ac.get("/health")
        assert resp.status_code == 200
        # metrics may not include report counter until a report is generated
        m = await ac.get("/metrics")
        assert m.status_code == 200
        # create report
        prop_id = "00000000-0000-0000-0000-000000000000"
        resp = await ac.post("/reports", json={"property_id": prop_id}, headers=headers)
        assert resp.status_code == 200
        tid = resp.json()["task_id"]
        # status initially pending or queued
        resp = await ac.get(f"/reports/{tid}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == tid
        # simulate completion by calling task manually
        from app.tasks import generate_report, OUTPUT_DIR
        # tests shouldn't write into the mounted volume (permissions issues)
        # patch output directory to tmp_path
        import app.tasks as tasks_mod
        tasks_mod.OUTPUT_DIR = str(tmp_path)
        result = generate_report(prop_id)
        assert "path" in result
        assert str(tmp_path) in result["path"]
        # output should be a PDF if reportlab is available
        path = result["path"]
        assert path.endswith(".pdf") or path.endswith(".txt")
        # make sure file actually exists
        assert os.path.exists(path)
        # after manual run the originally queued task still shows pending
        resp = await ac.get(f"/reports/{tid}", headers=headers)
        assert resp.status_code == 200
        assert resp.json().get("download_path") is None
        # metric should now register at least one report (from manual run)
        m2 = await ac.get("/metrics")
        assert "reports_generated_total" in m2.text
        for line in m2.text.splitlines():
            if line.startswith("reports_generated_total"):
                assert float(line.split()[-1]) >= 1.0
                break
