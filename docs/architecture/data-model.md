# Datamodell – ByggSjekk

**Versjon:** 0.1
**Sist oppdatert:** 2024

---

## Oversikt

Databaseskjemaet er designet for å:
- Støtte den fulle saksbehandlingsflyten fra dokumentopplasting til rapportgenerering
- Lagre semi-strukturerte AI-resultater i JSONB uten å ofre relasjonsintegritet
- Sikre full sporbarhet av alle AI-vurderinger og arkitektbeslutninger
- Skalere til multitenant SaaS (fremtidig `organization`-lag)

Alle tabeller bruker UUID som primærnøkkel (generert av `uuid_generate_v4()`).

---

## Tabeller

### `users`
Arkitekter og administratorer som bruker systemet.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik bruker-ID |
| `email` | VARCHAR(255) UNIQUE | E-postadresse (innlogging) |
| `hashed_password` | TEXT | bcrypt-hash av passord |
| `full_name` | VARCHAR(255) | Fullt navn |
| `role` | ENUM | `ADMIN`, `ARCHITECT`, `VIEWER`, `CUSTOMER` |
| `is_active` | BOOLEAN | Deaktivert bruker kan ikke logge inn |
| `created_at` | TIMESTAMPTZ | Opprettelsestidspunkt |
| `last_login_at` | TIMESTAMPTZ | Siste innlogging |

### `properties`
Eiendommer som er gjenstand for avviksvurdering.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik eiendoms-ID |
| `street_address` | VARCHAR(255) | Gateadresse |
| `municipality` | VARCHAR(100) | Kommune |
| `municipality_number` | VARCHAR(4) | Kommunenummer (f.eks. 0301 for Oslo) |
| `postal_code` | VARCHAR(10) | Postnummer |
| `gnr` | VARCHAR(10) | Gårdsnummer |
| `bnr` | VARCHAR(10) | Bruksnummer |
| `snr` | VARCHAR(10) NULLABLE | Seksjonsnummer |
| `fnr` | VARCHAR(10) NULLABLE | Festenummer |
| `property_type` | VARCHAR(50) | `apartment`, `house`, `commercial`, etc. |
| `build_year` | INTEGER NULLABLE | Byggeår |
| `total_area_m2` | FLOAT NULLABLE | Totalt areal (m²) |
| `floors` | INTEGER NULLABLE | Antall etasjer |
| `created_at` | TIMESTAMPTZ | Opprettelsestidspunkt |

### `property_cases`
En avviksvurderingssak knyttet til én eiendom.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik saks-ID |
| `property_id` | UUID FK → properties | Eiendom saken gjelder |
| `created_by` | UUID FK → users | Arkitekt som opprettet saken |
| `case_number` | VARCHAR(50) UNIQUE | Menneskelig lesbart saksnummer (BS-2024-0001) |
| `title` | VARCHAR(255) | Sakstittel |
| `status` | ENUM | `CaseStatus` (se shared_types) |
| `customer_type` | ENUM | `CustomerType` |
| `assigned_architect` | VARCHAR(255) NULLABLE | Navn på ansvarlig arkitekt |
| `notes` | TEXT NULLABLE | Interne notater |
| `created_at` | TIMESTAMPTZ | Opprettelsestidspunkt |
| `updated_at` | TIMESTAMPTZ | Sist oppdatert |
| `completed_at` | TIMESTAMPTZ NULLABLE | Fullforingstidspunkt |

### `source_documents`
Kildedokumenter (PDF-filer) lastet opp til en sak.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik dokument-ID |
| `case_id` | UUID FK → property_cases | Saken dokumentet tilhorer |
| `document_type` | VARCHAR(50) | `APPROVED_PLAN`, `CURRENT_STATE_PLAN`, `REGULATION_PLAN`, etc. |
| `source_type` | ENUM | `SourceType` (CUSTOMER_UPLOAD, MUNICIPALITY_ARCHIVE, etc.) |
| `filename` | VARCHAR(500) | Filnavn i MinIO |
| `original_filename` | VARCHAR(500) | Opprinnelig filnavn fra bruker |
| `storage_key` | TEXT | Full sti i MinIO |
| `file_size_bytes` | BIGINT | Filstørrelse |
| `mime_type` | VARCHAR(100) | MIME-type (application/pdf, etc.) |
| `page_count` | INTEGER NULLABLE | Antall sider (settes etter OCR) |
| `approval_status` | ENUM | `ApprovalStatus` |
| `approval_date` | DATE NULLABLE | Godkjenningsdato |
| `approval_reference` | VARCHAR(255) NULLABLE | Kommunalt saksnummer |
| `issuing_authority` | VARCHAR(255) NULLABLE | Utstedende myndighet |
| `processing_status` | ENUM | `ProcessingStatus` |
| `processing_error` | TEXT NULLABLE | Feilmelding ved mislykket prosessering |
| `created_at` | TIMESTAMPTZ | Opplastingstidspunkt |

### `structured_plans`
Strukturerte romdata ekstrahert fra kildedokumenter via AI-parsing.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik plan-ID |
| `document_id` | UUID FK → source_documents UNIQUE | Ett strukturert plan per dokument |
| `spaces` | JSONB | Liste med rom: `[{room_id, name, function, area_m2, floor, ...}]` |
| `total_area_m2` | FLOAT NULLABLE | Sum av arealer for P-ROM |
| `total_bra_m2` | FLOAT NULLABLE | Bruksareal (BRA) |
| `floor_count` | INTEGER NULLABLE | Antall etasjer i planen |
| `parsing_confidence` | FLOAT | Gjennomsnittlig AI-confidence for parsingen |
| `parsing_model` | VARCHAR(100) NULLABLE | AI-modell brukt |
| `parsing_model_version` | VARCHAR(50) NULLABLE | Modellversjon |
| `raw_llm_response` | JSONB NULLABLE | Rå AI-respons (sporbarhet) |
| `parsed_at` | TIMESTAMPTZ | Tidspunkt for parsing |

**JSONB-skjema for `spaces`:**
```json
[
  {
    "room_id": "rom-01",
    "name": "Stue",
    "function": "LIVING_ROOM",
    "area_m2": 28.0,
    "floor": 1,
    "has_window": true,
    "ceiling_height_m": 2.5,
    "bounding_box": [x1, y1, x2, y2],
    "confidence": 0.94
  }
]
```

### `deviations`
Avvik oppdaget mellom godkjent plan og dagens plan.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik avviks-ID |
| `case_id` | UUID FK → property_cases | Saken avviket tilhorer |
| `deviation_number` | VARCHAR(20) | Menneskelig referanse (AVV-001) |
| `category` | ENUM | `DeviationCategory` |
| `severity` | ENUM | `DeviationSeverity` |
| `status` | ENUM | `DeviationStatus` |
| `title` | VARCHAR(500) | Kort avvikstittel |
| `description` | TEXT | Detaljert beskrivelse |
| `affected_room_ids` | JSONB | Liste med room_id-er fra strukturerte planer |
| `confidence_score` | FLOAT | AI-confidence (0.0–1.0) |
| `ai_model` | VARCHAR(100) NULLABLE | AI-modell brukt |
| `ai_model_version` | VARCHAR(50) NULLABLE | Modellversjon |
| `evidence` | JSONB NULLABLE | Evidens-data fra AI (rådata, bounding boxes, etc.) |
| `architect_note` | TEXT NULLABLE | Arkitektens kommentar |
| `reviewed_by` | UUID FK → users NULLABLE | Arkitekt som gjennomgikk |
| `reviewed_at` | TIMESTAMPTZ NULLABLE | Tidspunkt for gjennomgang |
| `created_at` | TIMESTAMPTZ | Opprettelsestidspunkt |

### `rule_matches`
Koblinger mellom avvik og relevante regelverk.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik match-ID |
| `deviation_id` | UUID FK → deviations | Avviket som matches |
| `rule_id` | VARCHAR(100) FK → rules | Regelen som matches |
| `match_confidence` | FLOAT | Confidence for at regelen er relevant |
| `match_reason` | TEXT | Begrunnelse for koblinga |
| `created_at` | TIMESTAMPTZ | Tidspunkt for matching |

### `rules`
Regelregisteret med TEK17, PBL og SAK10-paragrafer.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | VARCHAR(100) PK | Menneskelig ID (tek17-12-2-rom-varig-opphold) |
| `source` | VARCHAR(20) | `TEK17`, `PBL`, `SAK10`, etc. |
| `paragraph` | VARCHAR(20) | Paragrafhenvisning (§ 12-2) |
| `title` | VARCHAR(255) | Tittel på regelen |
| `short_description` | TEXT | Kort beskrivelse |
| `full_text` | TEXT | Fullstendig regelformulering |
| `applies_to_categories` | JSONB | Liste med `DeviationCategory`-koder |
| `severity_hint` | VARCHAR(20) | Typisk alvorlighetsgrad for avvik |
| `version` | DATE | Gjeldende versjon av regelen |
| `active` | BOOLEAN | Aktiv i regelregisteret |
| `notes` | TEXT NULLABLE | Interne notater |

### `reports`
Genererte rapporter for en sak.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik rapport-ID |
| `case_id` | UUID FK → property_cases | Saken rapporten gjelder |
| `report_type` | ENUM | `ReportType` (INTERNAL, CUSTOMER, MUNICIPALITY) |
| `generated_by` | UUID FK → users | Arkitekt som genererte |
| `content` | JSONB | Rapportinnhold (fra ReportGenerator) |
| `storage_key` | TEXT NULLABLE | MinIO-sti til PDF-fil |
| `version` | INTEGER | Versjonsnummer (økes ved re-generering) |
| `created_at` | TIMESTAMPTZ | Genereringstidspunkt |

### `municipality_lookups`
Cache for kommuneoppslag (unngår gjentatte API-kall).

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| `id` | UUID PK | Unik oppslags-ID |
| `gnr` | VARCHAR(10) | Gårdsnummer |
| `bnr` | VARCHAR(10) | Bruksnummer |
| `municipality` | VARCHAR(100) | Kommunenavn |
| `result` | JSONB | Resultat fra kommunekobling |
| `source_adapter` | VARCHAR(100) | Adapter som returnerte resultatet |
| `confidence` | FLOAT | Confidence for resultatet |
| `looked_up_at` | TIMESTAMPTZ | Oppslagstidspunkt |
| `expires_at` | TIMESTAMPTZ | Utløpstidspunkt for cache |

---

## ER-diagram

```
users
  │
  │ created_by / reviewed_by
  ▼
property_cases ──── properties
  │
  │ case_id
  ├──────────────── source_documents ──── structured_plans
  │                                           │
  │                                           │ JSONB: spaces[]
  │
  ├──────────────── deviations
  │                     │
  │                     │ deviation_id
  │                     └──── rule_matches ──── rules
  │
  └──────────────── reports
```

```
┌──────────┐      ┌────────────────┐      ┌────────────┐
│  users   │──────│ property_cases │──────│ properties │
└──────────┘      └───────┬────────┘      └────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
     ┌────────────┐  ┌─────────┐  ┌──────────┐
     │  source_   │  │deviati- │  │ reports  │
     │ documents  │  │  ons    │  └──────────┘
     └─────┬──────┘  └────┬────┘
           │              │
     ┌─────────────┐  ┌───────────────┐    ┌────────┐
     │ structured_ │  │ rule_matches  │────│ rules  │
     │   plans     │  └───────────────┘    └────────┘
     └─────────────┘
```

---

## Indekser

```sql
-- Hyppige oppslag
CREATE INDEX idx_property_cases_status ON property_cases(status);
CREATE INDEX idx_source_documents_case_id ON source_documents(case_id);
CREATE INDEX idx_deviations_case_id ON deviations(case_id);
CREATE INDEX idx_deviations_status ON deviations(status);
CREATE INDEX idx_deviations_severity ON deviations(severity);
CREATE INDEX idx_rule_matches_deviation_id ON rule_matches(deviation_id);

-- Eiendomsoppslag (gnr + bnr + kommune)
CREATE INDEX idx_properties_gnr_bnr ON properties(gnr, bnr);
CREATE INDEX idx_municipality_lookups_gnr_bnr ON municipality_lookups(gnr, bnr, municipality);

-- JSONB-indekser for romdata
CREATE INDEX idx_structured_plans_spaces ON structured_plans USING GIN(spaces);
```

---

## Migrasjonshistorikk

Alle skjemaendringer gjøres via **Alembic**:

```bash
# Kjør alle migrasjoner
make migrate

# Generer ny migrasjon
make migrate-generate MSG="legg til kolonne X i tabell Y"

# Vis historikk
make migrate-history
```

Migrasjonsfiler ligger i `apps/api/alembic/versions/`.
