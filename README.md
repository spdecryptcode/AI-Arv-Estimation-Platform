# ARV Estimation & Property Comparison Platform

> An AI-powered, fully open-source platform for After-Repair Value (ARV) estimation and property comparison, targeting the San Francisco real estate market.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

---

## Overview

This platform provides real estate investors and analysts with automated ARV estimates backed by comparable sales data, ML regression models, and AI-generated property narratives. The entire stack is containerized, production-ready, and built exclusively on open-source tools.

**Key capabilities:**
- Automated comparable property search and ranking
- ML-based ARV estimation with async Celery job queue
- AI narrative generation via a local Ollama LLM
- PDF report generation per property
- JWT-secured API with role-based access
- Full-text property search powered by MeiliSearch
- Prometheus + Grafana observability out of the box

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Next.js UI │────▶│  Property Service │────▶│   ML Service    │
│  (port 3000)│     │   (port 8002)     │     │  (port 8003)    │
└─────────────┘     └──────────────────┘     └─────────────────┘
                            │                        │
                     ┌──────▼──────┐         ┌──────▼──────┐
                     │ Auth Service│         │Celery Worker│
                     │ (port 8001) │         │  + Redis    │
                     └─────────────┘         └─────────────┘
                            │
              ┌─────────────┼─────────────┐
         ┌────▼────┐  ┌─────▼─────┐  ┌───▼──────────┐
         │Postgres │  │MeiliSearch│  │Report Service│
         └─────────┘  └───────────┘  │  (port 8004) │
                                     └──────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend APIs | FastAPI (Python 3.11) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Full-text Search | MeiliSearch |
| ML / ARV Model | scikit-learn (XGBoost / Ridge regression) |
| AI Narratives | Ollama (local LLM, no external API calls) |
| Frontend | Next.js 14 + Tailwind CSS |
| Containerization | Docker + Docker Compose |
| Observability | Prometheus + Grafana |
| Auth | JWT (python-jose) |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 20.10+ and Docker Compose
- [Node.js](https://nodejs.org/) 20+ (frontend only)
- [Make](https://www.gnu.org/software/make/)

### Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/spdecryptcode/AI-Arv-Estimation-Platform.git
cd AI-Arv-Estimation-Platform

# 2. Set up environment
cp .env.example .env        # fill in JWT secret and DB passwords

# 3. Build and start all services
make up

# 4. Run database migrations
make migrate

# 5. (Optional) Load sample property data
docker compose exec property_service python scripts/load_sample_data.py
```

Services will be available at:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Property API | http://localhost:8002/docs |
| Auth API | http://localhost:8001/docs |
| ML API | http://localhost:8003/docs |
| Report API | http://localhost:8004/docs |
| Grafana | http://localhost:3001 |

### Get an API token

```bash
curl -s -X POST http://localhost:8001/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"email":"user@example.com","password":"pass"}' | jq .access_token
```

Use the returned token as `Authorization: Bearer <token>` on all protected endpoints.

---

## Project Structure

```
.
├── services/
│   ├── auth_service/       # JWT authentication & user management
│   ├── property_service/   # Property CRUD, comps search, ARV caching
│   ├── ml_service/         # ARV ML model + async inference jobs
│   └── report_service/     # PDF report generation
├── frontend/               # Next.js UI (search, login, property detail)
├── common/                 # Shared utilities (DB, cache, Celery, security)
├── data/                   # Sample property CSV
├── docs/                   # Full documentation
├── docker-compose.yml
└── Makefile
```

---

## Common Commands

```bash
make up           # Start all services
make down         # Stop all services
make logs         # Tail all logs
make migrate      # Run Alembic migrations
make test         # Run all tests
make ml-worker    # Start the ML Celery worker
make beat         # Start the Celery beat scheduler (model retraining)
```

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design and service interactions |
| [Microservices](docs/microservices.md) | API reference for all services |
| [ML Models](docs/ml_models.md) | ARV model details and retraining |
| [AI Narratives](docs/ai_narratives.md) | Ollama LLM integration |
| [Data Pipeline](docs/data_pipeline.md) | ETL and data ingestion |
| [Database](docs/database.md) | Schema and migrations |
| [Frontend](docs/frontend.md) | Next.js app guide |
| [Observability](docs/observability.md) | Metrics, logs, and dashboards |
| [Security](docs/security.md) | Auth, secrets, and threat model |
| [Deployment](docs/deployment.md) | CI/CD and production deployment |
| [Quick Start](docs/quick_start.md) | Detailed setup guide |
| [Contributing](docs/contributing.md) | How to contribute |
| [Operating Guide](docs/operating.md) | Day-to-day operations |

---