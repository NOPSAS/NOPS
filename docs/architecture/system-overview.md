# Systemarkitektur – ByggSjekk

**Versjon:** 0.1
**Sist oppdatert:** 2024

---

## Oversikt

ByggSjekk er bygget som et **monorepo** med tydelig separasjon mellom brukergrensesnitt, API-lag, domenespesifikke tjenester og infrastruktur. Arkitekturen legger til rette for uavhengig skalering av komponenter og enkel utskifting av integrasjoner (f.eks. AI-leverandør, kommunekobling).

```
byggsjekk/
├── apps/
│   ├── api/                  # FastAPI REST API
│   └── web/                  # Next.js 14 frontend
├── services/                 # Domenespesifikke tjenester
│   ├── document_ingestion/   # Filmottak, OCR, MinIO
│   ├── plan_parser/          # AI-basert tegningsparser
│   ├── deviation_engine/     # Avviksdetektor
│   ├── rule_engine/          # Regelmatching (TEK17, PBL, SAK10)
│   ├── municipality_connectors/ # Kommuneintegrasjoner
│   ├── review_workflow/      # Arkitektgjennomgang
│   ├── reporting/            # Rapportgenerering
│   └── dispensation_intelligence/ # Dispensasjonsvurdering
├── packages/
│   └── shared_types/         # Delte Pydantic-modeller og enums
├── infra/                    # Docker-konfigurasjon
├── scripts/                  # Seed- og hjelpeskript
└── docs/                     # Produktdokumentasjon
```

---

## Komponenter

### Web – Next.js 14

Brukergrensesnitt for arkitekter. Bygget med:
- **Next.js 14** (App Router, React Server Components)
- **TypeScript** for typesikkerhet
- **Tailwind CSS** + **shadcn/ui** for konsistent design
- **React Query** for servertilstandshåndtering
- **Zustand** for lokal klienttilstand

Nøkkelsider:
- `/` – Dashboard med saksoversikt
- `/cases/[id]` – Saksdetaljer med avviksliste
- `/cases/[id]/review` – Arkitektgjennomgang (side-by-side tegningsvisning)
- `/cases/[id]/report` – Rapportvisning og eksport

### API – FastAPI

REST API som eksponerer all forretningslogikk. Bygget med:
- **FastAPI** (Python 3.12) for høy ytelse og automatisk OpenAPI-generering
- **SQLAlchemy** (async) for databasetilgang
- **Alembic** for skjemamigrasjoner
- **Pydantic v2** for datavalidering og serialisering
- **python-jose** for JWT-håndtering
- **bcrypt** for passordhasching

API-strukturen følger resource-orientert REST:
```
POST   /api/v1/auth/login
GET    /api/v1/cases/
POST   /api/v1/cases/
GET    /api/v1/cases/{id}
POST   /api/v1/cases/{id}/documents
GET    /api/v1/cases/{id}/deviations
PATCH  /api/v1/cases/{id}/deviations/{dev_id}
POST   /api/v1/cases/{id}/reports
```

### Services – Domenespesifikke tjenester

Tjenestene er Python-moduler som importeres av API og av ARQ-arbeidere. De er ikke eksponert direkte over nett.

| Tjeneste | Ansvar |
|----------|--------|
| `document_ingestion` | Filvalidering, OCR, MinIO-lagring, kø-posting |
| `plan_parser` | AI-parsing av tegninger til strukturert romdata |
| `deviation_engine` | Sammenligning av planer, avviksdeteksjon |
| `rule_engine` | Regelmatching mot TEK17, PBL, SAK10 |
| `municipality_connectors` | Kommuneintegrasjoner (eByggSak, SEFRAK) |
| `review_workflow` | Tilstandsmaskin for arkitektbehandling |
| `reporting` | PDF-rapportgenerering |
| `dispensation_intelligence` | Dispensasjonsvurdering og søknadsgenerering |

### Database – PostgreSQL 16

PostgreSQL med utvidede funksjoner:
- **JSONB** for semi-strukturerte data (romdata, AI-evidens, rapportinnhold)
- **uuid-ossp** for UUID-primærnøkler
- **pgcrypto** for kryptografiske funksjoner
- **pg_trgm** for trigram-indekser (fulltekstsøk)

Skjemaet styres av **Alembic**-migrasjoner. Se `docs/architecture/data-model.md` for full ER-modell.

### Objektlager – MinIO / S3

MinIO er brukt lokalt og i dev/staging. Produksjon bruker AWS S3 (eller annen S3-kompatibel tjeneste).

Bucket-struktur:
```
byggsjekk-documents/
├── cases/{case_id}/
│   ├── source/{document_id}/original.pdf
│   ├── source/{document_id}/pages/{page_n}.png
│   └── reports/{report_id}/report.pdf
└── tmp/                         # Midlertidige opplastinger
```

### Jobbkø – ARQ + Redis

Asynkron prosessering via **ARQ** (Async Redis Queue):
- Dokumentparsing (OCR + AI) er tidkrevende og kjøres alltid asynkront
- Jobbstatus trackedes i databasen via `ProcessingStatus`-feltet
- Redis 7 brukes som jobbkøbackend

Arbeiderfunksjoner (definert i `apps/api/workers/`):
- `process_document` – OCR + plan-parsing
- `run_deviation_analysis` – avviksdetektor
- `generate_report` – PDF-generering

---

## Dataflyt

```
Bruker (nettleser)
       │
       │  HTTPS
       ▼
 ┌─────────────┐
 │  Next.js    │
 │  Web (3000) │
 └──────┬──────┘
        │  REST / JSON (HTTP)
        ▼
 ┌─────────────────────┐
 │  FastAPI API (8000) │
 │  ┌───────────────┐  │
 │  │ Auth / JWT    │  │
 │  │ Routers       │  │
 │  │ Services      │  │
 │  └───────────────┘  │
 └──┬──────┬───────┬───┘
    │      │       │
    ▼      ▼       ▼
┌───────┐ ┌─────┐ ┌──────────┐
│  PG   │ │Redis│ │  MinIO   │
│(data) │ │(kø) │ │(filer)   │
└───────┘ └──┬──┘ └──────────┘
             │
             ▼
     ┌──────────────┐
     │  ARQ Worker  │
     │  ┌────────┐  │
     │  │plan_   │  │
     │  │parser  │  │
     │  │dev_    │  │
     │  │engine  │  │
     │  └───┬────┘  │
     └──────┼───────┘
            │
            ▼
     ┌──────────────┐
     │  AI-adapter  │
     │  OpenAI GPT  │
     │  Anthropic   │
     └──────────────┘
```

---

## Sikkerhetsmodell

### Autentisering

JWT-basert autentisering (HS256). Tokens har kort levetid (60 min) med refresh-token-mønster.

```
POST /api/v1/auth/login
→ { access_token: "eyJ...", token_type: "bearer", expires_in: 3600 }
```

### Tilgangskontroll

Rollebasert tilgangskontroll (RBAC):

| Rolle | Rettigheter |
|-------|------------|
| `ADMIN` | Alle operasjoner, brukeradministrasjon |
| `ARCHITECT` | Opprette og behandle saker, generere rapporter |
| `VIEWER` | Lese saker og rapporter (kun egne) |
| `CUSTOMER` | Lese rapporter for egne eiendommer |

### Datasikkerhet

- Alle passord hashes med bcrypt (faktor 12)
- HTTPS påkrevd i produksjon (HSTS)
- CORS-konfigurasjon via `CORS_ORIGINS`-miljøvariabel
- Sensitiv data (API-nøkler) kun i miljøvariabler, aldri i kode eller database
- MinIO-objects er private som standard – presignerte URL-er for nedlasting

---

## AI-integrasjon

### Abstrakt LLM-adapter

AI-integrasjonen er abstrahert bak et adapter-mønster slik at leverandør kan byttes uten å endre domenekoden.

```python
class LLMAdapterInterface(ABC):
    async def analyze_plan_image(self, image_bytes: bytes, prompt: str) -> dict: ...
    async def extract_room_data(self, image_bytes: bytes) -> list[dict]: ...
    async def compare_plans(self, plan_a: dict, plan_b: dict) -> dict: ...
```

Implementasjoner:
- `OpenAIAdapter` – bruker GPT-4o med vision-API
- `AnthropicAdapter` – bruker Claude med vision-API
- `MockLLMAdapter` – deterministiske svar for testing

Valg av leverandør styres av `LLM_PROVIDER`-miljøvariabelen.

### Sporbarhet

Alle AI-kall lagres med:
- Modellnavn og versjon
- Prompt-hash (SHA-256 av input)
- Rå LLM-respons (JSONB)
- Tidsstempel
- Confidence-score

Dette sikrer etterprøvbarhet og gjør det mulig å replay analyse ved modelloppgraderinger.

---

## Skalerbarhetsstrategi

### Horisontal skalering

- **API** er tilstandsløs og skalerer horisontalt bak en load balancer
- **ARQ-arbeidere** kan kjøres i flere instanser
- **PostgreSQL** bruker connection pooling (PgBouncer i produksjon)

### Caching

- Redis brukes for session-cache og jobbkø
- API-svar for statiske data caches med `Cache-Control`-headers
- Plan-parser-resultater caches per dokument-hash (unngår re-parsing)

### Lagringsstrategi

- Originaldokumenter lagres i MinIO – aldri i databasen
- Databasen lagrer kun metadata, strukturerte data og JSONB-innhold
- PDF-export genereres on-demand og caches i MinIO
