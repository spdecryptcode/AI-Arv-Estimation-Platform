# Security

Details on authentication, network security, secrets handling, and input
validation.

## 9.1 Authentication & Authorization

- RS256 JWT tokens signed with private key (Docker secret).
- Access token TTL: 60 minutes; refresh token TTL: 30 days.
- Refresh tokens stored in Redis keyed by user; logout deletes the key.
- RBAC enforced via FastAPI dependencies (`viewer`, `analyst`, `admin`).
- Passwords hashed with bcrypt cost 12; minimum length 12 characters.
- Rate limit login endpoints (10/min per IP) via `slowapi` + Redis.
- Token revocation: deleting the Redis entry revokes all associated access
tokens.

## 9.2 Network Security

- Only Nginx exposed on host ports 80/443.
- Internal Docker network isolates services; no external outbound access.
- TLS 1.2+ enforced by Nginx. Self-signed cert in dev; Let's Encrypt via
  Certbot in prod.
- CORS strict origin whitelist; no wildcards.
- Nginx security headers: X-Frame-Options DENY, X-Content-Type-Options
  nosniff, Referrer-Policy strict-origin, CSP, HSTS 1y.
- Service-to-service calls use internal DNS names.

## 9.3 Secrets Management

- Secrets passed via Docker secrets (production) or `.env` files (development,
  gitignored).
- Separates `env.dev` and `env.prod` files.
- Secrets include JWT private key, PostgreSQL/Redis passwords, Meilisearch
  master key, SMTP credentials.

## 9.4 Input Validation & Injection Prevention

- All request bodies validated with Pydantic v2 strict models (coercion
  disabled).
- SQL queries parameterized via SQLAlchemy; no raw string interpolation.
- PostGIS geometry inputs sanitized prior to use.
- File uploads (if any) have MIME checks, virus scan hook, size limits at
  Nginx level.
- Meilisearch queries escape special characters.
