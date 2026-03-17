# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is this?

nops.no / ByggSjekk – Norwegian SaaS platform for property intelligence, building permits and architectural services. Monorepo with FastAPI backend, Next.js 14 frontend, PostgreSQL, Redis, MinIO, Docker.

## Commands

```bash
# Development (Docker)
make dev              # Start all services with hot-reload
make dev-detached     # Start in background
make down             # Stop all services
make logs-api         # Follow API logs
make logs-web         # Follow web logs

# Testing
make test-api         # Run pytest in Docker
make test-api-local   # Run pytest locally: cd apps/api && pytest tests/ -v

# Database
make migrate          # Run Alembic migrations
make migrate-generate MSG="description"  # Generate new migration
make shell-db         # psql shell

# Production
make prod             # Build and start production
./deploy.sh <server-ip>  # Full deploy to VPS

# Docker compose directly
docker compose -f infra/docker-compose.yml up -d --build api web
docker compose -f infra/docker-compose.yml restart api
```

## Architecture

### Monorepo structure
- `apps/api/` – FastAPI backend (Python 3.12, async SQLAlchemy, Alembic)
- `apps/web/` – Next.js 14 frontend (TypeScript, Tailwind, shadcn/ui)
- `services/` – Shared Python services used by API (municipality connectors, AI, regulations)
- `infra/` – Docker Compose, nginx, postgres init

### API routing
All endpoints registered in `apps/api/app/api/v1/router.py` via try/except ImportError pattern. New endpoint files auto-discovered if added there. 28 endpoint files in `apps/api/app/api/v1/endpoints/`.

### Key service modules (`services/`)
- `municipality_connectors/kartverket.py` – Kartverket Matrikkel (eiendom, bygninger, byggesaker). **Note:** Kartverket eiendomsregister blocks cloud server IPs (403). Geonorge adresser API works fine.
- `municipality_connectors/arealplaner.py` – Arealplaner.no (planrapport, dispensasjoner). Returns mock-data unless `AREALPLANER_API_KEY` is set.
- `municipality_connectors/dok_wms.py` – DOK-analyse via open WMS (NGU radon, NVE flom, NGU kvikkleire). **No API key needed.**
- `municipality_connectors/planslurpen.py` – Planslurpen.no (plan bestemmelser). Open API.
- `municipality_connectors/eiendomsdata.py` – SSB statistics, value estimation, neighbour lookup.
- `property_intelligence/analyzer.py` – AI analysis using Anthropic Claude. Falls back to rule-based if AI fails.
- `regulations/regelverk.py` – 38 paragraphs (PBL, TEK17, SAK10, EMGL, Byggforsk) used by AI prompts.
- `regulations/gebyrberegning.py` – Municipal fee calculation (Nesodden hardcoded, generic for others).
- `reporting/pdf_rapport.py` – PDF generation with fpdf2.

### Frontend API calls
Next.js uses rewrites to proxy `/api/*` to `http://api:8000/api/*` (configured in `next.config.js`). Frontend code uses relative paths via `fetchJSON()` from `apps/web/src/lib/utils.ts`. **Never hardcode API URLs.**

### Authentication
- `apps/api/app/core/deps.py` defines: `get_current_user` (requires auth), `get_optional_user` (auth optional – used for public endpoints), `require_ai_access` / `require_pdf_access` (plan-gated).
- Most property endpoints use `get_optional_user` to allow unauthenticated access.
- Token stored in `localStorage` as `byggsjekk_token`.

### AI integration pattern
All AI endpoints follow the same pattern:
1. Fetch data from Kartverket/Planslurpen/etc in parallel with `asyncio.gather`
2. Build a Norwegian prompt with `Svar BARE med gyldig JSON: {...}`
3. Call `anthropic.AsyncAnthropic` with `model="claude-sonnet-4-6"`, `max_tokens=4096` minimum
4. Strip markdown code fences, parse JSON
5. Handle truncated JSON gracefully (close open brackets/strings)

### Email
`apps/api/app/services/email.py` uses Resend REST API (primary, works from cloud) with SMTP fallback. Resend key detected by `re_` prefix on `smtp_password`.

### sys.path for services
Endpoint files that import from `services/` must include:
```python
for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
```

## Important notes

- All text content is in Norwegian (bokmål)
- `.env` and `stripeandresend.txt` contain secrets – never commit
- Production server: DigitalOcean 188.166.8.36, deploy via tar+scp
- Norkart partnership: Slim-BIM (2D→3D) sold via e-Torg, 10% commission
- Kartverket eiendomsregister returns 403 from cloud IPs – DOK via WMS works as alternative
- `next.config.js` has `eslint.ignoreDuringBuilds: true` and `typescript.ignoreBuildErrors: true`
- Dataclass fields in `services/` must all have defaults (non-default after default causes Python error)
