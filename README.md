# ARV Estimation & Property Comparison Platform

This repository contains the code and documentation for an AI-powered property
comparison and after-repair value (ARV) estimation tool targeting the San
Francisco real estate market. The system is fully containerized with Docker,
uses a 100% open-source stack, and is designed for production workloads with
high availability, observability and automated data pipelines.  In addition to
FastAPI services there are dedicated Celery workers (including an `ml_worker`
that processes ARV inference jobs) and optional background services for
periodic model retraining.

## 📁 Documentation
All detailed documentation lives under the `docs/` directory.  Use the links
below to navigate the system design and operational guides.

1. [Architecture](docs/architecture.md)
2. [Data Pipeline](docs/data_pipeline.md) *(includes a simple `services/data_pipeline` helper package with unit tests)*
3. [Database](docs/database.md)
4. [Microservices](docs/microservices.md) – includes auth, property, ML, report services and their APIs
5. [ML Models](docs/ml_models.md)
6. [AI Narrative Generation](docs/ai_narratives.md)
7. [Frontend](docs/frontend.md)
8. [Observability](docs/observability.md)
9. [Security](docs/security.md)
10. [Deployment & CI/CD](docs/deployment.md)
11. [Repository Structure](docs/repository_structure.md)
12. [Timeline & Team](docs/timeline.md)
13. [Quick Start](docs/quick_start.md)
14. [Contributing](docs/contributing.md)
15. [Operating Guide](docs/operating.md)

## 🚧 Frontend (optional)

A minimal Next.js app lives in the `frontend/` directory.  It is not required
for backend development but can be started with:

```bash
cd frontend
npm install
npm run dev
```

The client reads `NEXT_PUBLIC_API_BASE` from `.env.local` (defaults to
`http://localhost:8002`) and calls the property service directly.  Only basic
search, login and property detail pages have been scaffolded; additional UI
work is left as future enhancement.  You can authenticate via the `/login`
page and the token will be stored in `localStorage` for protected actions
(e.g. report generation).

---

Refer to these documents when developing, operating, or reviewing the platform.