from common.celery_app import celery
from . import model
import time

@celery.task
def compute_arv_task(property_id: str):
    # delegate to the shared inference logic
    print(f"[ml_task] computing ARV for {property_id} using models {model.available_models()}")
    return model.compute_arv(property_id)


@celery.task
def retrain_models():
    """Dummy retraining task that writes a new model file to the store."""
    store = model.MODEL_STORE_PATH
    store.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    fname = f"retrained_{ts}.bin"
    path = store / fname
    path.write_text("trained at %d" % ts)
    print(f"[ml_task] retrained, created {path}")
    # invalidate cached listing so subsequent inferences see the new model
    try:
        model.available_models.cache_clear()
    except Exception:
        pass
    return {"path": str(path)}
