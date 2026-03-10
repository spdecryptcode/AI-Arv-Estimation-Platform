# Convenience commands for development

.PHONY: up down logs migrate test build

up:
	# start all containers in development mode
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build

down:
	docker compose -f docker-compose.yml -f docker-compose.override.yml down

logs:
	docker compose -f docker-compose.yml -f docker-compose.override.yml logs -f

migrate:
	@echo "Running migrations for auth_service"
	docker compose exec auth_service alembic upgrade head
	@echo "Property service uses the same database; its schema is managed manually or via a combined migration tool."
	@echo "A starter revision exists at services/property_service/alembic/versions/0001_create_properties_table.py"
	# Running alembic inside property_service will fail because the database already
	# records the auth_service revision. You can apply that script manually if needed.

build:
	docker compose -f docker-compose.yml -f docker-compose.override.yml build

ml-worker:
	@echo "Starting ML queue worker"
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d celery_ml_worker

beat:
	@echo "Starting Celery beat scheduler"
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d celery_beat

test:
	@echo "Running full suite of integration tests and pipeline unit tests"
	$(MAKE) property-test
	$(MAKE) auth-test
	$(MAKE) ml-test
	$(MAKE) report-test
	$(MAKE) pipeline-test

report-test:
	@echo "Running report_service integration tests"
	docker compose exec report_service pytest tests/test_report.py -q

property-test:
	@echo "Running property_service integration tests"
	docker compose exec property_service pytest tests/test_api.py -q

auth-test:
	@echo "Running auth_service integration tests"
	docker compose exec auth_service pytest tests/test_auth.py -q

ml-test:
	@echo "Running ml_service integration tests"
	docker compose exec ml_service python -m pytest tests/test_ml.py tests/test_model.py -q
pipeline-test:
	@echo "Running data_pipeline unit tests"
	@cd services/data_pipeline && pytest -q
