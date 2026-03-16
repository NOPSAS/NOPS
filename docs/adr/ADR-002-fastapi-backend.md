# ADR-002: FastAPI som backend-rammeverk

**Status:** Akseptert
**Dato:** 2024
**Beslutningstakere:** Konsepthus AS

---

## Kontekst

ByggSjekk trenger et Python-backend-rammeverk for REST API, autentisering og forretningslogikk. Python er valgt som backend-språk primært fordi:
1. AI/ML-bibliotekene vi bruker (OpenAI SDK, Anthropic SDK, PyMuPDF, Tesseract-bindings) er best støttet i Python
2. Teamet har sterkest Python-kompetanse for domenespesifikk kode

De primære alternativene var:
1. **FastAPI** – moderne, asynkront, Pydantic-basert
2. **Django (+ Django REST Framework)** – batterier inkludert, morent, stor community
3. **Flask** – minimalistisk, fleksibelt

---

## Beslutning

Vi velger **FastAPI** som backend-rammeverk.

---

## Begrunnelse

### FastAPI

**Valgt fordi:**

1. **Asynkron fra start:** FastAPI er bygget på `asyncio` og `Starlette`. ARQ (jobbkøen vår) er 100 % async. SQLAlchemy async-extensions passer perfekt. Django er historisk synkront og asynkron-støtten er tykket på etterskudd.

2. **Automatisk OpenAPI/Swagger:** FastAPI genererer OpenAPI-skjemaet fra Pydantic-modeller og type hints. Vi slipper å vedlikeholde API-dokumentasjon manuelt. Dette er kritisk for et API som eksponeres til et TypeScript-frontend og potensielt tredjeparter.

3. **Pydantic v2-integrasjon:** Pydantic er valgt som valideringslag for hele stacken (`packages/shared_types`). FastAPI bruker Pydantic nativt. Django REST Framework har sin egen serializer-abstraksjon som er overlappende og kan divergere.

4. **Ytelse:** FastAPI er blant de raskeste Python-rammeverkene i benchmarks (sammenlignbart med Go for CPU-bundne oppgaver, og svært god for I/O-bundne asynkrone arbeidsflyter).

5. **Dependency Injection:** FastAPIs avhengighetsinjeksjonssystem (`Depends`) er elegant og testbart. Gjør det enkelt å injisere database-sesjoner, autentiserte brukere og konfigurasjonsavhengigheter.

6. **Minimal boilerplate:** For et API-first system uten server-side rendering er FastAPI riktig abstraksjonsnivå. Django bringer mye vi ikke bruker (templates, admin-UI, ORM med synkront grensesnitt).

### Django – Forkastet

**Forkastet fordi:**
- Tungt, batterier vi ikke bruker (templating, admin, synkron ORM)
- Asynkron-støtte er etterskudd-funksjonalitet med mange hjørne-kanter
- Django REST Framework er et ekstra abstraksjonslag som divergerer fra Pydantic
- Migrasjoner via `django.db.migrations` er veldokumentert, men Alembic er mer fleksibelt for avanserte skjemaoperasjoner (custom types, conditional constraints)

### Flask – Forkastet

**Forkastet fordi:**
- Ingen innebygd asynkron-støtte uten extensions
- Ingen automatisk OpenAPI-generering (ville krevd `flask-smorest` eller `flasgger`)
- Pydantic-integrasjon er ikke nativ
- For minimalistisk – vi ville bygd mange ting selv som FastAPI gir oss gratis

---

## Tekniske valg knyttet til FastAPI

| Komponent | Valg | Alternativ |
|-----------|------|-----------|
| ORM | SQLAlchemy 2.0 (async) | Tortoise ORM, SQLModel |
| Migrasjoner | Alembic | Yoyo, Flyway |
| Validering | Pydantic v2 | Marshmallow, attrs |
| Auth | python-jose + passlib | Authlib, django-allauth |
| Testing | pytest + httpx (async) | unittest |
| Linting | ruff | flake8 + isort + black |

---

## Konsekvenser

- **Positiv:** Automatisk OpenAPI-dokumentasjon som alltid er oppdatert
- **Positiv:** Konsistent Pydantic-bruk på tvers av `packages/shared_types`, `apps/api` og `services/`
- **Positiv:** Asynkron arkitektur fra dag én – ingen refaktorering nødvendig
- **Nøytral:** FastAPI har ingen innebygd admin-UI. Vi lager dette i Next.js
- **Negativ:** Litt mer boilerplate for enkle CRUD-operasjoner sammenlignet med Django REST Framework ViewSets. Akseptabelt.

---

## Gjennomgangspunkt

Beslutningen revurderes dersom:
- Vi trenger tung server-side rendering (lite sannsynlig – vi har Next.js)
- Python-teamet ønsker å migrere til TypeScript/Node.js for backend (vurder i fase 5–6)
