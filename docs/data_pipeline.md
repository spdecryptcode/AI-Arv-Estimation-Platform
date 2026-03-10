# Data Sources & Ingestion Pipeline

This document outlines the free data sources the platform ingests and the ETL
architecture implemented via Celery tasks.  The pipeline is idempotent: rerunning
a task for the same date upserts existing rows rather than duplicating.

## 3.1 Free Data Sources

- SF Open Data (Socrata API): assessor, sales, permits, etc.
- Redfin research CSV downloads
- Zillow Research CSV datasets
- OpenStreetMap amenities and zoning via Overpass API
- US Census boundaries and demographic layers
- Supplemental web scraping via Playwright when APIs are unavailable

## 3.2 ETL Pipeline Architecture

The ingestion module consists of three logical layers:

1. **Extraction layer** – fetch raw data from external sources and store it in a
   staging table (`raw_ingestion`).  Each extractor returns structured data or
   writes raw JSON with a checksum, source, and timestamp.
2. **Transformation layer** – normalize and enrich records using internal tools.
3. **Loading layer** – upsert cleaned records into the primary tables and
   update secondary systems (Meilisearch, Redis cache).

### 3.2.1 Extraction Layer

- `SocrataExtractor`: uses `sodapy` to paginate Socrata datasets, handles rate
  limiting with exponential backoff, and writes the response JSON to
  `raw_ingestion`.
- `CSVExtractor`: downloads large CSVs with streaming via `requests`, validates
  against a known schema, and writes to staging. Checksums prevent reprocessing.
- `GeoJSONExtractor`: fetches zoning, flood, seismic layers, reprojects to
  EPSG:4326 with `pyproj`, and writes to PostGIS geometry columns.
- `OverpassExtractor`: queries OSM Overpass API at 1 request/sec, caches
  results in Redis for 7 days, and writes amenity records.
- `PlaywrightScraper`: headless Chrome with rotating user agents in a
  dedicated container; used only for sources lacking APIs.

### 3.2.2 Transformation Layer

- `AddressNormalizer`: standardizes addresses with `usaddress-scourgify`.
  Output: canonical components (number, street, unit, city, state, ZIP).
- `Geocoder`: batch geocoding against a self-hosted Nominatim container,
  falling back to the public API; results cached in PostGIS with confidence
  score.
- `PropertyNormalizer`: maps heterogeneous source fields to the unified
  `PropertyRecord` schema, handles type coercion, nulls, and flags outliers
  (>3σ from neighborhood median).
- `GeoEnricher`: attaches neighborhood, flood zone, seismic zone, zoning
designation via PostGIS `ST_Within`/`ST_DWithin` spatial joins.
- `AmenityScorer`: computes walkability and transit scores with PostGIS
  distance queries at 400m, 800m, and 1600m.
- `QualityScorer`: assigns a 0–1 completeness score; records below 0.6 are
  quarantined in `data_quality_issues` for manual review.

### 3.2.3 Loading Layer

- Use `ON CONFLICT` upsert logic on natural key `apn`; update `updated_at`.
- After DB upsert, send the document to Meilisearch property index with
  searchable and filterable attributes.
- Publish property IDs to Redis Pub/Sub; `property_service` listeners flush
  cache keys.
- Record each ingestion run in `ingestion_runs` with metadata (record count,
  errors, duration, quality metrics).

## 3.3 Ingestion Schedule (Celery Beat)
> **Note:**  for developers the repository also contains a small
> `services/data_pipeline` package with minimal extractor and transformer
> implementations (e.g. `CSVExtractor`, `AddressNormalizer`).  These helpers
> are intentionally lightweight and avoid external dependencies so they can be
> used in unit tests or quick experiments.  Run `make pipeline-test` from the
> project root to execute the accompanying pytest suite.

### Manual Trigger via API

For development and debugging the property CSV loader the `property_service`
exposes a light‑weight HTTP endpoint:

```
POST /properties/import
{
  "filepath": "/path/to/file.csv"    # optional, defaults to /app/data/sample_properties.csv
}
```

This routes the request to the `common.tasks.ingest_properties_csv` Celery
job and returns a JSON acknowledgement including the generated task ID.
The endpoint is also exercised by the service’s integration test.


Celery Beat schedules the extraction tasks daily:

- `fetch_assessor_data` – 01:00 PST every day
- `fetch_sales_data` – 02:00 PST every day
- `fetch_permits_data` – 03:00 PST every day
- `update_osm_amenities` – 04:00 PST every Sunday
- `retrain_models` – 00:00 UTC every day (for demonstration; adjust to monthly in production)

All tasks are idempotent and log metrics via Prometheus counters.  Failures
automatically retry with exponential backoff (max 5 attempts).
