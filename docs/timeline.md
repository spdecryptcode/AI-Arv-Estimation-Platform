# Development Timeline & Team Composition

Provides a recommended schedule and staffing model for building the platform.

## Recommended Team Composition

- **Full-stack engineer with ML experience** – backend, data pipeline, model
  development (can cover two roles).
- **Frontend developer** – Next.js, UI components, mapping integration.
- **DevOps/Infrastructure engineer** – Docker orchestration, monitoring,
  CI/CD, backups.

A two-person team (full-stack/ML + frontend/devops) can deliver version 1.0 in
~3 months. A single engineer may require 5–6 months.

## Phase-by-Phase Timeline (example)

| Week | Focus                                    |
|------|------------------------------------------|
| 1–3  | Repo setup, Docker, CI, auth & data MVP  |
| 4–8  | ETL pipeline, database schema, search API |
| 9–16 | Full backend services + ML model dev     |
| 13–18| Frontend MVP → complete UI               |
| 17–21| Observability, security hardening        |
| 19–22| Deployment automation, backups           |
| 21–26| Testing, documentation, polish          |

Overlap is intentional: backend and ML tasks run in parallel when possible.

Adjust schedule based on team size, unforeseen data quality issues, and
stakeholder feedback.  Feature flags should be used to keep scope flexible.
