# =============================================================================
# ByggSjekk – Makefile
# Kjør `make help` for oversikt over alle kommandoer.
# =============================================================================

COMPOSE_BASE := docker compose -f infra/docker-compose.yml
COMPOSE_DEV  := $(COMPOSE_BASE) -f infra/docker-compose.dev.yml
COMPOSE_PROD := $(COMPOSE_BASE) -f infra/docker-compose.prod.yml

.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Utvikling
# -----------------------------------------------------------------------------

.PHONY: dev
dev: ## Start alle tjenester i utviklingsmodus (med hot-reload)
	$(COMPOSE_DEV) up --build

.PHONY: dev-detached
dev-detached: ## Start alle tjenester i bakgrunnen
	$(COMPOSE_DEV) up --build -d

.PHONY: down
down: ## Stopp alle tjenester (bevar volumes)
	$(COMPOSE_DEV) down

.PHONY: restart
restart: ## Restart alle tjenester
	$(COMPOSE_DEV) restart

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

.PHONY: logs
logs: ## Følg logger fra alle tjenester
	$(COMPOSE_DEV) logs -f

.PHONY: logs-api
logs-api: ## Følg logger fra API-tjenesten
	$(COMPOSE_DEV) logs -f api

.PHONY: logs-web
logs-web: ## Følg logger fra web-tjenesten
	$(COMPOSE_DEV) logs -f web

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

.PHONY: test-api
test-api: ## Kjør API-tester (pytest)
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml \
		exec api pytest tests/ -v

.PHONY: test-api-local
test-api-local: ## Kjør API-tester lokalt (uten Docker)
	cd apps/api && pytest tests/ -v

.PHONY: test-api-cov
test-api-cov: ## Kjør API-tester med dekningsrapport
	$(COMPOSE_DEV) exec api pytest apps/api/tests/ -v --cov=. --cov-report=term-missing

.PHONY: test-web
test-web: ## Kjør frontend-tester (Jest / Vitest)
	$(COMPOSE_DEV) exec web npm run test

.PHONY: test-all
test-all: test-api test-web ## Kjør alle tester

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

.PHONY: migrate
migrate: ## Kjør Alembic-migrasjoner (upgrade head)
	$(COMPOSE_DEV) exec api alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Rull tilbake siste migrasjon
	$(COMPOSE_DEV) exec api alembic downgrade -1

.PHONY: migrate-generate
migrate-generate: ## Generer ny migrasjon (bruk: make migrate-generate MSG="beskrivelse")
	$(COMPOSE_DEV) exec api alembic revision --autogenerate -m "$(MSG)"

.PHONY: migrate-history
migrate-history: ## Vis migrasjonshistorikk
	$(COMPOSE_DEV) exec api alembic history --verbose

.PHONY: migrate-status
migrate-status: ## Vis gjeldende migrasjonsstatus (produksjon)
	$(COMPOSE_PROD) exec api alembic current

.PHONY: rollback
rollback: ## Rull tilbake siste migrasjon (produksjon)
	$(COMPOSE_PROD) exec api alembic downgrade -1

# -----------------------------------------------------------------------------
# Testdata / seed
# -----------------------------------------------------------------------------

.PHONY: seed
seed: ## Seed regelbase og mock-sak
	$(COMPOSE_DEV) exec api python scripts/seed_rules.py
	$(COMPOSE_DEV) exec api python scripts/seed_mock_case.py

.PHONY: seed-rules
seed-rules: ## Seed kun regelbasen
	$(COMPOSE_DEV) exec api python scripts/seed_rules.py

.PHONY: seed-mock
seed-mock: ## Seed kun mock-sak
	$(COMPOSE_DEV) exec api python scripts/seed_mock_case.py

# -----------------------------------------------------------------------------
# Evalueringer
# -----------------------------------------------------------------------------

.PHONY: eval
eval: ## Kjør avviksmotorevalueringer mot mock-datasett
	$(COMPOSE_DEV) exec api python scripts/run_evals.py

.PHONY: evals
evals: ## Kjør evalueringer via Docker
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml \
		exec api python /workspace/scripts/run_evals.py

.PHONY: evals-local
evals-local: ## Kjør evalueringer lokalt (uten Docker)
	cd byggsjekk && python3 scripts/run_evals.py 2>/dev/null || python scripts/run_evals.py

# -----------------------------------------------------------------------------
# Interaktive skall
# -----------------------------------------------------------------------------

.PHONY: shell-api
shell-api: ## Åpne bash-skall i API-containeren
	$(COMPOSE_DEV) exec api bash

.PHONY: shell-web
shell-web: ## Åpne sh-skall i web-containeren
	$(COMPOSE_DEV) exec web sh

.PHONY: shell-db
shell-db: ## Åpne psql-skall mot databasen
	$(COMPOSE_DEV) exec db psql -U byggsjekk -d byggsjekk

.PHONY: shell-redis
shell-redis: ## Åpne redis-cli
	$(COMPOSE_DEV) exec redis redis-cli

# -----------------------------------------------------------------------------
# Kodeanalyse og formatering
# -----------------------------------------------------------------------------

.PHONY: lint-api
lint-api: ## Kjør ruff linter på API-koden
	$(COMPOSE_DEV) exec api ruff check .

.PHONY: lint-api-fix
lint-api-fix: ## Kjør ruff linter og fiks automatisk
	$(COMPOSE_DEV) exec api ruff check . --fix

.PHONY: format-api
format-api: ## Formater API-koden med ruff format
	$(COMPOSE_DEV) exec api ruff format .

.PHONY: typecheck-api
typecheck-api: ## Kjør mypy typekontroll
	$(COMPOSE_DEV) exec api mypy . --ignore-missing-imports

.PHONY: lint-web
lint-web: ## Kjør ESLint på frontend-koden
	$(COMPOSE_DEV) exec web npm run lint

.PHONY: check
check: lint-api test-api ## Kjør lint og tester (CI-sjekk)
	@echo "All checks passed."

# -----------------------------------------------------------------------------
# Opprydding
# -----------------------------------------------------------------------------

.PHONY: clean
clean: ## Stopp tjenester og fjern alle volumes (destruktiv!)
	@echo "ADVARSEL: Dette vil slette alle data i databasen og MinIO."
	@read -p "Er du sikker? (ja/nei): " ans && [ "$$ans" = "ja" ] || exit 1
	$(COMPOSE_DEV) down -v

.PHONY: clean-force
clean-force: ## Stopp tjenester og fjern volumes uten bekreftelse
	$(COMPOSE_DEV) down -v

.PHONY: prune
prune: ## Fjern ubrukte Docker-ressurser
	docker system prune -f

# -----------------------------------------------------------------------------
# Produksjon (bruk med forsiktighet)
# -----------------------------------------------------------------------------

.PHONY: prod
prod: ## Start produksjon (docker-compose.prod.yml overlay)
	$(COMPOSE_PROD) up -d --build

.PHONY: prod-build
prod-build: ## Bygg produksjonsbilder uten cache
	$(COMPOSE_PROD) build --no-cache

.PHONY: deploy
deploy: prod-build prod migrate ## Fullt deployment: build → start → migrer
	@echo "Deployment fullfort"

.PHONY: prod-up
prod-up: ## Start produksjonskonfigurasjon (uten dev-overrides)
	$(COMPOSE_BASE) up -d

.PHONY: prod-down
prod-down: ## Stopp produksjonskonfigurasjon
	$(COMPOSE_BASE) down

.PHONY: ps
ps: ## Vis kjørende tjenester
	$(COMPOSE_PROD) ps

.PHONY: health
health: ## Sjekk API- og web-helse
	@curl -sf http://localhost:8000/health && echo "API OK" || echo "API nede"
	@curl -sf http://localhost:3000 && echo "Web OK" || echo "Web nede"

# -----------------------------------------------------------------------------
# Backup
# -----------------------------------------------------------------------------

.PHONY: backup
backup: ## Ta backup av databasen (lagres i backups/)
	@mkdir -p backups
	$(COMPOSE_PROD) exec db pg_dump -U byggsjekk byggsjekk | gzip > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup lagret i backups/"

# -----------------------------------------------------------------------------
# SSL (Let's Encrypt)
# -----------------------------------------------------------------------------

.PHONY: ssl-init
ssl-init: ## Initialiser Let's Encrypt-sertifikat for nops.no
	certbot certonly --standalone -d nops.no -d www.nops.no --email jakob@konsepthus.no --agree-tos --no-eff-email

.PHONY: ssl-renew
ssl-renew: ## Forny sertifikat og last inn nginx på nytt
	certbot renew --quiet && $(COMPOSE_PROD) exec nginx nginx -s reload

# -----------------------------------------------------------------------------
# Hjelp
# -----------------------------------------------------------------------------

.PHONY: help
help: ## Vis denne hjelpen
	@echo ""
	@echo "ByggSjekk – tilgjengelige make-kommandoer:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
