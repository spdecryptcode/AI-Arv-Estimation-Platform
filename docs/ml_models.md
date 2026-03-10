# ML & ARV Estimation

This document describes the machine learning components: comp selection engine,
ARV models, and confidence range generation.

## 6.1 Comp Selection Engine

Three-phase process:

1. **Candidate Retrieval (PostGIS query)**
   ```sql
   SELECT *
   FROM property_sales ps
   JOIN properties p ON ps.property_id = p.id
   WHERE ST_DWithin(p.location::geography, subject_location::geography, radius_meters)
     AND ps.sale_date >= NOW() - INTERVAL 'N days'
     AND p.property_type = subject_type
     AND p.sqft_living BETWEEN subject_sqft * (1 - tolerance)
                         AND subject_sqft * (1 + tolerance)
     AND ps.is_arms_length = true
   ORDER BY ps.sale_date DESC
   LIMIT 50;
   ```
   Reduces to ~50 candidates for further scoring.

2. **Similarity Scoring**
   - Compute weighted cosine similarity over features: `sqft_living`, bedrooms,
     bathrooms, age, condition, amenity scores, etc.
   - Properties with score < 0.65 are discarded.
   - Ensure minimum of 3 comps; if not enough, increment radius by 0.25 mi up to
     2.0 mi.

3. **Adjustment Calculation**
   - Apply Fannie Mae UAD-style adjustments for attribute differences (sqft,
     garage, bedrooms, etc.).
   - Adjustment rates calibrated per neighborhood via linear regression on
     matched pairs from `property_sales`.

## 6.2 ARV Estimation Models

### 6.2.1 Model 1 — Hedonic Pricing (XGBoost Regressor)

- **Target:** `adjusted_price_per_sqft` (sale price/time-trend adjusted ÷ GLA)
- **Features:**
  - Property attributes (sqft, bedrooms, bathrooms, year built, stories,
    garage presence/spaces, ADU, condition grade)
  - Encoded neighborhood, flood zone, seismic zone
  - Walkability/transit/amenity scores (400 m & 800 m)
  - Sale month/year, days since sale
- **Library:** `xgboost` 2.x with early stopping on 20% validation split.
- **Hyperparameter tuning:** Optuna, 200 trials initially then quarterly.
- **Performance metric:** MAPE < 8% on held‑out test set.
- **Retraining cadence:** monthly; track feature importance in
  `model_metrics` table for drift detection.

### 6.2.2 Model 2 — Renovation Uplift (LightGBM Regressor)

- Predicts percentage uplift from renovations between two sales of same APN.
- Training data: records with two sales ≤3 yrs apart and intermediate permits.
- Permit descriptions embedded with `sentence-transformers` (all-MiniLM-L6-v2)
  and classified into categories: kitchen, bathroom, structural, ADU, full
  remodel.

### 6.2.3 Model 3 — Market Trend Adjustment (Prophet)

- Train a time series per neighborhood on monthly median price index from
  `property_sales`.
- Forecast 90 days ahead; produce a multiplier (e.g. 1.034).  Applies to
  adjust ARV for market movement.

### 6.2.4 ARV Range Generation — Monte Carlo Simulation

Run 10,000 iterations sampling from:

1. Prediction uncertainty interval of XGBoost (quantile regression).
2. Uplift model confidence intervals.
3. Adjustment uncertainty (±15% per adjustment item).

Output percentiles P10/P50/P90 as low/mid/high range.  If <5 comps available,
reduce `confidence_score` and widen range; UI shows "Thin Market" warning.

## 6.3 Model Hosting & Retraining

Models are stored in the `model_store` volume (mounted at `/app/models`) with date-stamped names.  A
retrain task (via Celery) rebuilds models and writes a new artifact; it is
scheduled to run automatically by the `celery_beat` scheduler according to the
`RETRAIN_CRON` environment variable (default `0 0 * * *` for midnight UTC daily).
The schedule can be tightened (e.g. `*/5 * * * *`) for tests or relaxed to
monthly for production.  The job can also be triggered manually via `POST /ml/retrain`.
Clients can query available artifacts via the `GET /ml/models` endpoint; the
`property_service` proxies this metadata when needed.  Old versions are retained 6 months.

The `ml_service` loads the latest artifacts at startup and exposes single- and
a batch-prediction endpoints.  Async jobs are queued when latency risk exists via
`POST /ml/jobs` and can be polled with `GET /ml/jobs/{id}`. Clients that only
reach the property service may use `/properties/{id}/arv_async` and
`/properties/{id}/arv_status/{task_id}` instead – the property service simply
forwards the request to the ML service.

Custom metrics (prediction latency, MAPE, model_version) are emitted via
Prometheus.
