# ByggSjekk – Avvikstjeneste for arkitekter

ByggSjekk er en norsk SaaS-plattform som hjelper arkitekter med å oppdage potensielle avvik mellom godkjente byggetegninger og dagens tilstand. Systemet er et **beslutningsstøtteverktøy** – arkitekten er alltid siste kontrollinstans.

---

## Hurtigstart / Quick Start

### Forutsetninger

- [Docker](https://docs.docker.com/get-docker/) og Docker Compose (v2)
- [Make](https://www.gnu.org/software/make/) (inkludert i de fleste Unix-systemer; Windows: via WSL2 eller Git Bash)
- Git

### Start utvikling

```bash
git clone <repo-url> byggsjekk
cd byggsjekk

# Sett opp miljøvariabler
cp .env.example .env
# Rediger .env og fyll inn nøkler for OpenAI / Anthropic

# Start alle tjenester med hot-reload
make dev
```

Første oppstart laster ned Docker-images og bygger containere. Dette tar noen minutter.

---

## Tjenester

| Tjeneste | URL | Beskrivelse |
|----------|-----|-------------|
| Frontend (Next.js) | http://localhost:3000 | Brukergrensesnitt for arkitekter |
| Backend API (FastAPI) | http://localhost:8000 | REST API med forretningslogikk |
| API-dokumentasjon (Swagger) | http://localhost:8000/docs | Interaktiv API-utforsker |
| API-dokumentasjon (ReDoc) | http://localhost:8000/redoc | Alternativ API-dokumentasjon |
| MinIO Console | http://localhost:9001 | Objektlager-administrasjon |
| pgAdmin | http://localhost:5050 | Database-administrasjon (kun dev) |

**pgAdmin-innlogging:** admin@byggsjekk.no / admin
**MinIO-innlogging:** byggsjekk / byggsjekk123

---

## Makefile-kommandoer

| Kommando | Beskrivelse |
|----------|-------------|
| `make dev` | Start alle tjenester med hot-reload |
| `make dev-detached` | Start alle tjenester i bakgrunnen |
| `make down` | Stopp alle tjenester |
| `make logs` | Følg logger fra alle tjenester |
| `make logs-api` | Følg logger fra API |
| `make logs-web` | Følg logger fra frontend |
| `make test-api` | Kjør API-tester (pytest) |
| `make test-api-cov` | Kjør API-tester med dekningsrapport |
| `make test-web` | Kjør frontend-tester |
| `make test-all` | Kjør alle tester |
| `make migrate` | Kjør Alembic-migrasjoner |
| `make migrate-generate MSG="..."` | Generer ny migrasjon |
| `make seed` | Seed regelbase og mock-sak |
| `make seed-rules` | Seed kun regelbasen |
| `make seed-mock` | Seed kun mock-sak |
| `make eval` | Kjør avviksmotorevalueringer |
| `make shell-api` | Åpne bash-skall i API-container |
| `make shell-db` | Åpne psql mot databasen |
| `make lint-api` | Kjør ruff linter |
| `make format-api` | Formater API-koden |
| `make clean` | Fjern alle volumes (destruktiv!) |
| `make help` | Vis alle kommandoer |

---

## Arkitektur

```
byggsjekk/
├── apps/
│   ├── api/          # FastAPI-backend (Python 3.12)
│   └── web/          # Next.js 14-frontend (TypeScript)
├── services/         # Domenespesifikke tjenester
│   ├── document_ingestion/
│   ├── plan_parser/
│   ├── deviation_engine/
│   ├── rule_engine/
│   ├── municipality_connectors/
│   ├── review_workflow/
│   ├── reporting/
│   └── dispensation_intelligence/
├── packages/
│   └── shared_types/ # Delte Pydantic-modeller
├── infra/            # Docker-konfigurasjon
├── scripts/          # Hjelpeskript (seed, eval)
└── docs/             # Produktdokumentasjon
```

### Teknologistabel

| Lag | Teknologi |
|-----|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12, SQLAlchemy (async) |
| Database | PostgreSQL 16 (JSONB for semi-strukturerte data) |
| Jobbkø | ARQ + Redis 7 |
| Objektlager | MinIO (S3-kompatibel) |
| Autentisering | JWT (HS256), bcrypt |
| AI-integrasjon | OpenAI GPT-4o / Anthropic Claude (abstrakt adapter) |
| Migrasjoner | Alembic |
| Linting | ruff, mypy (Python); ESLint (TypeScript) |

### Dataflyt

```
Bruker (nettleser)
      │
      ▼
 Next.js Web (3000)
      │  REST/JSON
      ▼
 FastAPI API (8000)
      │
      ├──► PostgreSQL (data, metadata)
      ├──► MinIO (dokumentfiler, tegninger)
      ├──► Redis (jobbkø, cache)
      └──► AI-adapter (OpenAI / Anthropic)
               │
               ▼
         Analyse-resultater
         (confidence-score, avvik)
```

---

## Faglige prinsipper

ByggSjekk er designet etter følgende faglige og etiske prinsipper:

1. **Arkitekten er alltid siste kontrollinstans.** Systemet gir aldri endelige juridiske konklusjoner – kun beslutningsstøtte.

2. **Alle AI-vurderinger har confidence-score.** Brukeren ser alltid usikkerheten knyttet til en analyse.

3. **Forsiktig språkbruk.** Systemet bruker ikke ordene «ulovlig», «godkjent» eller «krever søknad» som endelig konklusjon. Vi bruker formuleringar som «potensielt avvik», «indikerer endring» og «bør vurderes av ansvarlig arkitekt».

4. **ApprovalStatus-modellen** bruker fire tilstander i stedet for binær godkjent/ikke-godkjent:
   - `RECEIVED` – dokumentet er mottatt og registrert
   - `ASSUMED_APPROVED` – sannsynlig godkjent basert på alder/kontekst, ikke verifisert
   - `VERIFIED_APPROVED` – verifisert godkjent via kommunekobling
   - `UNKNOWN` – kan ikke fastslås

5. **Sporbarhet.** Alle AI-vurderinger lagres med modellversjon, prompt-hash og rå LLM-svar for etterprøvbarhet.

---

## Utvikling

### Første gangs oppsett

```bash
cp .env.example .env
make dev
make migrate      # Kjør databasemigrasjoner
make seed         # Legg inn regelbase og testdata
```

### Kjøre tester

```bash
make test-api          # pytest med verbose output
make test-api-cov      # pytest med dekningsrapport
make test-web          # Jest / Vitest
```

### Database-migrasjoner

```bash
# Kjør alle migrasjoner
make migrate

# Generer ny migrasjon etter modellendring
make migrate-generate MSG="legg til felt X i tabell Y"

# Rull tilbake siste migrasjon
make migrate-down
```

### Seed testdata

```bash
make seed         # Kjør begge seed-skript
make seed-rules   # Kun regelbase (TEK17, PBL, SAK10)
make seed-mock    # Kun mock-sak (Storgata 1, Oslo)
```

### Kjøre evalueringer

```bash
make eval         # Kjør avviksmotorevalueringer mot kjente testtilfeller
```

---

## Bidra

Se `docs/architecture/` for systemdetaljer og `docs/adr/` for arkitekturelle beslutninger.
Legg til nye regler ved å følge guiden i `docs/rules/how-to-add-rules.md`.

---

*ByggSjekk er utviklet av Konsepthus AS. Alle AI-vurderinger er beslutningsstøtte – ikke juridisk rådgivning.*
