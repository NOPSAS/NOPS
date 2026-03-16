# ByggSjekk – Produktbeskrivelse

**Versjon:** 0.1
**Dato:** 2024
**Forfatter:** Konsepthus AS

---

## Problem

Arkitekter og eiendomsaktører bruker betydelig tid på å manuelt sammenligne godkjente byggetegninger med dagens tilstand. Dette er et tidkrevende, feilutsatt og lite skalerbart arbeid – særlig i Norge, der eldre bygningsmasse ofte har uoppdatert dokumentasjon, uregistrerte tiltak og komplekse reguleringshistorikker.

Konkrete utfordringer:

- **Manglende samsvar:** Eiendommer er endret over tid uten at tegningene er oppdatert. Loft er tatt i bruk, boder er gjort om til soverom, balkonger er bygget inn – uten tillatelse.
- **Dokumentasjonsgap:** Kommunale arkiv er inkomplette. Mange tillatelser fra 1970–1990-tallet er ikke digitalisert.
- **Tidspress:** Arkitekter har ofte kort tid til å gjennomgå en eiendom før de skal gi faglig anbefaling.
- **Juridisk usikkerhet:** Det er vanskelig å si hva som er søknadspliktig, hva som er dispensert og hva som faktisk er godkjent – uten å bruke timer på å sette seg inn i hvert enkelt tilfelle.
- **Konsekvenser:** Kjøpere overtar boliger med ulovlige tiltak. Arkitekter stilles til ansvar. Kommuner bruker ressurser på etterhandlinger.

---

## Løsning

ByggSjekk er et **beslutningsstøttesystem** for arkitekter som automatisk oppdager potensielle avvik mellom godkjente byggetegninger og en eiendoms nåværende tilstand.

Systemet er **ikke** et juridisk verktøy og gir aldri kategoriske konklusjoner som «ulovlig» eller «godkjent». Det er et intelligent filtreringslag som hjelper arkitekten å bruke sin fagkompetanse mer effektivt.

Kjerneflyt:

1. Arkitekten laster opp godkjente tegninger (fra kommunalt arkiv eller kunde)
2. Arkitekten laster opp dagens plantegning (fra megler, takstmann eller befaring)
3. ByggSjekk parser begge plantegninger til strukturert romdata
4. Avviksmotoren sammenligner planene og identifiserer potensielle avvik
5. Regelmotoren kobler avvikene mot relevante forskrifter (TEK17, PBL, SAK10)
6. Arkitekten gjennomgår funn, bekrefter eller avviser, og genererer rapport

---

## Faglige prinsipper

ByggSjekk er bygget på fire ufravikelige faglige prinsipper:

### 1. Arkitekten er alltid siste kontrollinstans

Systemet er et verktøy, ikke en erstatning for faglig vurdering. Alle funn presenteres som «potensielle avvik» med tilhørende confidence-score. Arkitekten bestemmer om funnet er reelt og hva som skal gjøres.

### 2. Aldri kategoriske juridiske konklusjoner

Systemet bruker ikke ordene «ulovlig», «godkjent» eller «krever søknad» som endelig konklusjon. Vi sier «indikerer mulig søknadspliktig tiltak» og «bør vurderes av arkitekt». Juridisk konklusjon er arkitektens ansvar.

### 3. Confidence-score på alle vurderinger

Alle AI-vurderinger har en synlig confidence-score (0–1). Brukeren ser alltid usikkerheten. Score under 0.6 varsles eksplisitt som «lav sikkerhet».

### 4. ApprovalStatus-modellen

Godkjenningsstatus er ikke binær. Systemet bruker fire tilstander:
- `RECEIVED` – dokumentet er mottatt, ingen vurdering enda
- `ASSUMED_APPROVED` – sannsynlig godkjent basert på kontekst
- `VERIFIED_APPROVED` – verifisert via kommunekobling
- `UNKNOWN` – kan ikke fastslås

---

## Målgruppe

### Primær: Arkitekter og arkitektfirmaer

Den primære brukeren er en autorisert arkitekt (ARK) som utfører teknisk due diligence ved eiendomsoverdragelse, søknad om bruksendring, eller vurdering av rehabiliteringsprosjekt.

Verdien for arkitekten:
- Spar 2–6 timer per sak ved automatisert sammenligning
- Reduser risiko for å overse avvik
- Dokumenterbar prosess som gir juridisk ryggdekning

### Sekundær: Eiendomsmeglere og takstmenn

Kan bruke ByggSjekk som et screening-verktøy for å identifisere eiendommer som bør ha utvidet teknisk gjennomgang.

### Tertiær: Kommuner

Kommuner kan bruke systemet for intern saksbehandling og kontroll av innkomne søknader mot kommunens egne arkiv.

---

## MVP-omfang (8 faser)

### Fase 1: Fundament og infrastruktur
- Monorepo-oppsett (Next.js + FastAPI + PostgreSQL + Redis + MinIO)
- Autentisering (JWT, brukerregistrering, roller)
- Filopplasting og MinIO-integrasjon
- Grunnleggende saksoppretting

### Fase 2: Dokumentingestion og parsing
- PDF-parsing med OCR (PyMuPDF + Tesseract / Azure Document Intelligence)
- AI-basert romekstrahering fra plantegninger (GPT-4V)
- Strukturert romdata i databasen
- Godkjenningsstatus-tracking

### Fase 3: Avviksdetektor
- Romsammenligning (godkjent plan vs. dagens plan)
- Kategorisering av avvik (10 kategorier)
- Confidence-score per avvik
- Grunnleggende regelmatching (TEK17, PBL, SAK10)

### Fase 4: Kommuneintegrasjoner
- Mockadapter for testing
- eByggSak-integrasjon (pilot med Oslo kommune)
- SEFRAK-oppslag for eldre bygningsmasse
- Fallback e-postutkast for kommuner uten digital integrasjon

### Fase 5: Arkitektgjennomgang (UI)
- Avviksliste med filtrering og sortering
- Per-avvik: bekreft / avvis / kommenter
- Side-by-side tegningsvisning (godkjent vs. dagens)
- Audit trail for alle arkitektbeslutninger

### Fase 6: Rapportgenerering
- Intern arkitektrapport (PDF) med full detaljeringsgrad
- Kunderapport (PDF) med høynivå-sammendrag
- Kommunerapport for dispensasjonssøknader
- Rapport-historikk per sak

### Fase 7: Dispensasjonsintelligens
- Vurdering av dispensasjonsgrunnlag per avvik
- Generering av søknadsutkast
- Historisk presedens-analyse (lignende saker i kommunen)
- Risikoscore for dispensasjonsavslag

### Fase 8: Multitenant SaaS
- Firmakontoer med brukeradministrasjon
- Abonnementslogikk (Stripe)
- Saksportal for kunder (skrivebeskyttet)
- API-nøkler for integrasjoner (meglersystemer, takstverktøy)

---

## Teknisk arkitektur (sammendrag)

Se `docs/architecture/system-overview.md` for fullstendig beskrivelse.

- **Frontend:** Next.js 14 (TypeScript, Tailwind CSS, shadcn/ui)
- **Backend:** FastAPI (Python 3.12, SQLAlchemy async, Alembic)
- **Database:** PostgreSQL 16 med JSONB for semi-strukturerte data
- **Objektlager:** MinIO / AWS S3
- **Jobbkø:** ARQ + Redis
- **AI:** OpenAI GPT-4o (primær) / Anthropic Claude (alternativ via abstrakt adapter)

---

## Suksesskriterier for MVP

| Metrikk | Mål |
|---------|-----|
| Avvikspresisjon | > 80 % (andel riktige avvik av totalt detekterte) |
| Avviksrecall | > 70 % (andel detekterte av faktiske avvik) |
| Behandlingstid per sak | < 3 minutter (fra opplasting til avviksrapport) |
| Arkitekttilfredshet | NPS > 40 etter pilotperiode |
| Tidssparing per sak | 2+ timer sammenlignet med manuell gjennomgang |
