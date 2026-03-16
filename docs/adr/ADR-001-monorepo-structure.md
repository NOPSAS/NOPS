# ADR-001: Monorepo-struktur

**Status:** Akseptert
**Dato:** 2024
**Beslutningstakere:** Konsepthus AS

---

## Kontekst

Vi trenger å bestemme hvordan vi organiserer kodebasen for ByggSjekk. Systemet består av:
- En Next.js-frontend (`apps/web`)
- En FastAPI-backend (`apps/api`)
- Flere domenespesifikke Python-tjenester (`services/`)
- Delte typedefinisjoner brukt av både Python og (via kodegenerering) TypeScript
- Infrastrukturkonfigurasjon (Docker, Makefile)
- Dokumentasjon

De primære alternativene var:
1. **Seperate repositories** – ett per applikasjon/tjeneste
2. **Monorepo** – én repository med alle komponenter

---

## Beslutning

Vi bruker et **monorepo** organisert etter domeneseparasjon.

Strukturen:
```
byggsjekk/
├── apps/           # Deployerbare applikasjoner
├── services/       # Domenespesifikke tjenester (ikke deployerbare direkte)
├── packages/       # Delte biblioteker
├── infra/          # Infrastrukturkonfigurasjon
├── scripts/        # Hjelpeskript
└── docs/           # Dokumentasjon
```

Vi bruker **ikke** pnpm workspaces eller Turborepo på dette tidspunktet, da Python-siden ikke nyttiggjøres av JavaScript-pakkemanagere. Avhengighetsgrafen håndteres eksplisitt via Docker og imports.

---

## Begrunnelse

### Fordeler med monorepo for dette prosjektet

1. **Én kilde til sannhet for delte typer:** `packages/shared_types/models.py` definerer alle enums og Pydantic-modeller. Disse importeres direkte av `apps/api` og `services/`, og kan generere TypeScript-typer for `apps/web` via `datamodel-codegen`. Med seperate repositories ville vi trenge et publisert pakkeregister eller Git-submoduler.

2. **Atomiske endringer:** En endring som berører API-kontrakt, database-modell og frontend-type kan gjøres i én commit. Med seperate repositories krever det koordinerte commits og versjonering.

3. **Enklere lokal utvikling:** Én `make dev`-kommando starter hele systemet. Én `make test-all` kjører alle tester. Ingen behov for å synkronisere versjonsnumre mellom repositories.

4. **Felles CI/CD-grunnlag:** En enkelt GitHub Actions-konfigurasjon kan håndtere lint, test og deploy for alle komponenter, med caching av avhengigheter.

5. **Lavere overhead i tidlig fase:** For et lite team (1–3 utviklere) er overhead med å vedlikeholde seperate repositories (CI-oppsett, tilgangsstyring, versjonering) ikke proporsjonal med fordelene.

### Ulemper og mottiltak

| Ulempe | Mottiltak |
|--------|-----------|
| Repository kan bli stor over tid | Bruk `apps/`, `services/`, `packages/`-separasjon for tydelig grensesnittet |
| Alle utviklere har tilgang til all kode | Akseptabelt for dette teamet. RBAC på CI/CD-nivå ved behov |
| CI kjøres for hele repo ved endringer | Bruk path-filtre i GitHub Actions (kjør kun API-tester ved endringer i `apps/api/`) |
| Python og Node.js i samme repo | Tydelig separasjon via `apps/`-strukturen. Makefile abstrahere verktøy-spesifikke kommandoer |

---

## Alternativer vurdert

### Seperate repositories

**Forkastet fordi:**
- Delte typedefinisjoner (`packages/shared_types`) ville krevd et eget publisert pakkeregister (PyPI-privat eller GitHub Packages)
- Atomiske endringer på tvers av grenser ville krevd koordinerte commits
- Unødvendig overhead for et lite team i tidlig fase

### Turborepo / Nx

**Vurdert, forkastet foreløpig fordi:**
- Turborepo er optimalisert for JavaScript/TypeScript-monorepos. Python-siden nyttiggjøres ikke
- Tillegger kompleksitet som ikke er nødvendig på dette stadiet
- Kan introduseres senere dersom frontend-siden vokser til å ha flere pakker

---

## Konsekvenser

- **Positiv:** Enkel lokal utvikling og CI/CD i tidlig fase
- **Positiv:** Atomiske endringer på tvers av komponenter
- **Nøytral:** Krever disiplin rundt mappestruktur og modulgrenser for å unngå spaghetti-imports
- **Nøytral:** CI-pipelinen må bruke path-filtre for å unngå å kjøre alle tester ved enhver endring
- **Negativ:** Monorepo-størrelse kan bli en utfordring etter 2–3 år. Vurder splitting ved behov.

---

## Gjennomgangspunkt

Beslutningen revurderes dersom:
- Teamet vokser til > 5 utviklere
- Det oppstår behov for å dele tjenester som separate deployerbare enheter med uavhengige release-sykluser
- CI-kjøretider overstiger 15 minutter konsistent
