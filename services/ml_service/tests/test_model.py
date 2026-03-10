import os
import tempfile
import pathlib
import pytest

from app import model


def test_model_available_and_compute(tmp_path, monkeypatch):
    # create a temporary model store with one file
    store = tmp_path / "models"
    store.mkdir()
    (store / "mymodel.bin").write_text("dummy")
    monkeypatch.setattr(model, "MODEL_STORE_PATH", store)

    assert model.available_models() == ["mymodel.bin"]
    # deterministic output
    res1 = model.compute_arv("abc")
    res2 = model.compute_arv("abc")
    assert res1 == res2
    assert res1["property_id"] == "abc"
    assert res1["min"] < res1["max"]


def test_compute_arv_task_returns_model_value(monkeypatch):
    # ensure the Celery task uses the compute_arv logic
    property_id = "xyz"
    # create fake model list
    monkeypatch.setattr(model, "available_models", lambda: ["foo"])
    from app.tasks import compute_arv_task
    task_result = compute_arv_task(property_id)
    assert task_result == model.compute_arv(property_id)
