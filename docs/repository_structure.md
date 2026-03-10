# Repository Structure

Monorepo layout and conventions.

```
/ (root)
├── services/
│   ├── auth_service/
│   ├── property_service/
│   ├── ml_service/
│   └── report_service/
├── frontend/         # Next.js app
├── ml/               # training scripts, notebooks
├── infrastructure/   # Docker configs, k8s manifests (if any)
├── common/           # shared Python packages (logging, db, models)
├── docs/             # documentation (this directory)
├── tests/            # integration and e2e tests
├── Makefile          # convenience commands
├── docker-compose*.yml
├── .github/workflows/*
└── README.md
```

### Makefile Commands

- `make up` – start development environment
- `make down` – stop containers
- `make logs` – tail container logs
- `make migrate` – run database migrations (Alembic)
- `make test` – run the full test suite
- `make deploy` – trigger CI/CD deploy workflow

### Naming & Style

- Services use `snake_case` for Python packages and `kebab-case` for Docker
  container names.
- Python code adheres to PEP 8; use Black for formatting and Flake8 for linting.
- JavaScript/TypeScript uses ESLint + Prettier.
- Environment variables are uppercase with underscores (e.g.,
  `POSTGRES_PASSWORD`).
- Log messages use structured JSON and include `request_id` and `user_id`
  when available.
