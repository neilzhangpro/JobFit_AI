# =============================================================================
# JobFit AI — Makefile
# =============================================================================
# Standard commands for development and deployment.

COMPOSE_DEV = docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_PROD = docker compose -f docker-compose.yml -f docker-compose.prod.yml

# --- Development ---
.PHONY: dev dev-build down logs

dev:
	$(COMPOSE_DEV) up

dev-build:
	$(COMPOSE_DEV) up --build

down:
	docker compose down

logs:
	docker compose logs -f

# --- Production ---
.PHONY: prod prod-build

prod:
	$(COMPOSE_PROD) up -d

prod-build:
	$(COMPOSE_PROD) up -d --build

# --- Testing ---
.PHONY: test test-backend test-frontend lint

test: test-backend test-frontend

test-backend:
	$(COMPOSE_DEV) exec backend pytest -v

test-frontend:
	$(COMPOSE_DEV) exec frontend npm test

lint:
	$(COMPOSE_DEV) exec backend ruff check .
	$(COMPOSE_DEV) exec backend mypy --strict .
	$(COMPOSE_DEV) exec frontend npx eslint src/
	$(COMPOSE_DEV) exec frontend npx tsc --noEmit

# --- Database ---
.PHONY: migrate migrate-create seed

migrate:
	$(COMPOSE_DEV) exec backend alembic upgrade head

migrate-create:
	$(COMPOSE_DEV) exec backend alembic revision --autogenerate -m "$(msg)"

seed:
	$(COMPOSE_DEV) exec backend python -m scripts.seed

# --- Cleanup ---
.PHONY: clean

clean:
	docker compose down -v --rmi local
