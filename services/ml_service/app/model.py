import os
import random
from pathlib import Path

# path where trained model artifacts are stored; mounted volume in compose
MODEL_STORE_PATH = Path(os.getenv("MODEL_STORE_PATH", "/app/models"))


from functools import lru_cache


@lru_cache(maxsize=1)
def available_models() -> list[str]:
    """Return a list of model filenames present in the store.

    Results are cached for a short duration to reduce repeated disk access in
    high‑traffic scenarios.  Clearing the cache can be done with
    ``available_models.cache_clear()`` (used by retraining tasks).
    """
    if not MODEL_STORE_PATH.exists():
        return []
    return [p.name for p in MODEL_STORE_PATH.iterdir() if p.is_file()]


def compute_arv(property_id: str) -> dict:
    """Dummy ARV computation using model artifacts (if any).

    The result is deterministic given the property ID and first model name
    (if present). This stands in for a real ML inference pipeline.
    """
    models = available_models()
    # seed with property_id and first model name so values change when models
    # are updated
    seed = hash(property_id)
    if models:
        seed ^= hash(models[0])
    random.seed(seed)
    base = random.randint(80_000, 200_000)
    return {"property_id": property_id, "min": base, "max": base + 50_000}
