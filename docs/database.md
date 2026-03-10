# Database Design

Details of the PostgreSQL/PostGIS setup, table schemas, indexes, and connection
pooling strategy.

## 4.1 PostgreSQL + PostGIS Configuration

- **Image:** `postgis/postgis:15-3.3`
- **Memory tuning** (for a 16 GB server):
  - `shared_buffers = 4GB`
  - `effective_cache_size = 12GB`
  - `work_mem = 64MB`
  - `maintenance_work_mem = 1GB`
  - `max_connections = 200` (actual limited by PgBouncer)
  - `wal_level = replica` (for future streaming replication)
  - `checkpoint_completion_target = 0.9`
  - `default_statistics_target = 500`
  - `random_page_cost = 1.1` (SSD assumption)

Overrides are passed via Docker environment variables or a mounted
`postgresql.conf`.

## 4.2 Core Table Schemas

### 4.2.1 `properties` (Primary Property Table)

Columns include:
- `id` UUID primary key
- `apn` text unique
- `address` text
- `location` geography(Point,4326)
- `sqft_living`, `sqft_lot`, `bedrooms`, `bathrooms`, `year_built`, etc.
- zoning, flood_zone, seismic_zone, neighborhood text fields
- amenity and transit scores
- `updated_at` timestamp with time zone

Geometry indexes and GIST indexes are added on `location`.

### 4.2.2 `property_sales` (Transaction History)

Columns include:
- `id` UUID primary key
- `property_id` UUID references `properties(id)`
- `sale_date` date
- `price` numeric
- `is_arms_length` boolean
- adjustments, `adjusted_price_per_sqft` computed field

### 4.2.3 `property_permits` (Permit History)

Captures all permits with `apn`, permit type, description, value, issue and
final dates.  Text is later embedded by the renovation model pipeline.

### 4.2.4 `arv_estimates` (Model Outputs)

Stores output from the ARV range generator:
- `property_id` UUID
- `computed_at` timestamp
- percentile values (p10, p50, p90)
- confidence_score, thin_market_flag
- `model_version` identifier

### 4.2.5 Key Indexes

```sql
CREATE INDEX idx_properties_location ON properties USING GIST(location);
CREATE INDEX idx_properties_neighborhood ON properties(neighborhood);
CREATE INDEX idx_properties_type_sqft ON properties(property_type, sqft_living);
CREATE INDEX idx_properties_sale_date ON property_sales(sale_date DESC);
CREATE INDEX idx_properties_apn ON properties(apn);
CREATE INDEX idx_arv_property ON arv_estimates(property_id, computed_at DESC);
```

## 4.3 PgBouncer Connection Pooling

A separate `pgbouncer` container runs in transaction pooling mode.  It limits
actual PostgreSQL connections to 50 while allowing up to 1000 FastAPI
connections.  All application services connect to PgBouncer on port 6432; the
pooler routes traffic to Postgres.

Configuration is stored in `pgbouncer.ini` mounted as a volume.  Healthchecks
are defined to ensure PgBouncer is ready before application services start.
