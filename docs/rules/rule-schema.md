# Regelskjema – ByggSjekk

**Versjon:** 0.1
**Sist oppdatert:** 2024

---

## Oversikt

Regelregisteret inneholder paragrafer fra norsk byggelovgivning som brukes av regelmotoren til å koble detekterte avvik mot relevante juridiske referanser. Reglene er ikke juridisk rådgivning – de er referansepunkter som hjelper arkitekten å vurdere avvikenes potensielle konsekvenser.

---

## Datamodell

### Regel-entiteten

```python
class Rule(Base):
    __tablename__ = "rules"

    # Primærnøkkel – menneskelig lesbar
    id: str  # Eksempel: "tek17-12-2-rom-varig-opphold"

    # Kilde og referanse
    source: str       # "TEK17", "PBL", "SAK10", "DTILM", "NS3700"
    paragraph: str    # "§ 12-2"
    title: str        # "Krav til rom for varig opphold"

    # Innhold
    short_description: str   # 1-2 setninger
    full_text: str           # Fullstendig regelformulering (kan være forkortet)

    # Kobling til avvikskategorier
    applies_to_categories: list[str]  # Liste med DeviationCategory-verdier (JSONB)

    # Alvorlighet
    severity_hint: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"

    # Versjonering
    version: date          # Dato for gjeldende versjon (f.eks. 2017-06-19 for TEK17)
    superseded_by: str     # ID til ny regel om denne er utdatert (nullable)
    active: bool           # False = historisk, ikke aktiv

    # Metadata
    notes: str | None      # Interne notater for redaktørene
```

---

## Felt-beskrivelser

### `id` – Primærnøkkel

Format: `{kilde}-{paragraf}-{slug}`

Eksempler:
- `tek17-12-2-rom-varig-opphold`
- `pbl-20-1-tiltak-krav-soknad`
- `sak10-4-1-unntak-soknad`

Regler er identifisert ved menneskelig lesbar ID for enkel referanse i kode og dokumentasjon. Nye versjoner av en regel får nytt ID med år-suffiks: `tek17-12-2-rom-varig-opphold-2025`.

### `source` – Kilde

Tillatte verdier:

| Kode | Lovverk |
|------|---------|
| `TEK17` | Teknisk forskrift til plan- og bygningsloven (2017) |
| `PBL` | Plan- og bygningsloven (2008) |
| `SAK10` | Byggesaksforskriften (2010) |
| `DTILM` | Direktoratet for byggkvalitet (veiledere) |
| `NS3700` | Norsk Standard 3700 (universell utforming) |
| `LOKAL` | Kommunal reguleringsplan eller vedtekt |

### `paragraph` – Paragraf

Format: `§ {nummer}` eller `§ {nummer} bokstav {X}`.

Eksempler:
- `§ 12-2`
- `§ 20-1`
- `§ 4-1`

### `applies_to_categories` – Avvikskategorier

JSONB-liste med én eller flere `DeviationCategory`-koder. Regelmotoren bruker dette feltet til å begrense søket etter relevante regler per avvik.

```json
["ROOM_DEFINITION_CHANGE", "BEDROOM_UTILITY_DISCREPANCY", "USE_CHANGE_INDICATION"]
```

Se `docs/domain/deviation-categories.md` for fullstendig liste over kategorier.

### `severity_hint` – Alvorlighetsantydning

Antydning om hvilken alvorlighetsgrad avvik mot denne regelen typisk bør ha. Regelmotoren kan overstyres av AI-confidence.

| Verdi | Tolkning |
|-------|---------|
| `CRITICAL` | Brannsikkerhet, rømningsvei – umiddelbar gjennomgang |
| `HIGH` | Søknadspliktig tiltak eller brudd på materielle krav |
| `MEDIUM` | Merkbar endring som bør dokumenteres |
| `LOW` | Mindre endring, begrenset juridisk betydning |

### `version` – Regelversjon

Dato for regelens gjeldende versjon. For TEK17 er dette typisk `2017-06-19` med eventuelle endringsforskrifter angitt i `notes`.

### `superseded_by` – Etterfølger

Nullable. Dersom en regel er erstattet av en nyere versjon, angis etterfølgerens `id` her. Gammel regel beholder `active = True` frem til etterfølgeren er verifisert i produksjon.

---

## JSON-eksempel på en ferdig regel

```json
{
  "id": "tek17-12-2-rom-varig-opphold",
  "source": "TEK17",
  "paragraph": "§ 12-2",
  "title": "Krav til rom for varig opphold",
  "short_description": "Rom for varig opphold skal ha tilfredsstillende lysforhold og ventilasjon.",
  "full_text": "Rom for varig opphold skal ha vindu mot det fri med tilfredsstillende lysflate og mulighet for naturlig ventilasjon. Minimumsareal for rom for varig opphold er 7 m². Romhøyde skal minst være 2,4 m for rom for varig opphold.",
  "applies_to_categories": [
    "ROOM_DEFINITION_CHANGE",
    "BEDROOM_UTILITY_DISCREPANCY",
    "USE_CHANGE_INDICATION"
  ],
  "severity_hint": "HIGH",
  "version": "2017-06-19",
  "superseded_by": null,
  "active": true,
  "notes": "Gjelder boliger, inkludert ombygging. Se også §13-4 for ventilasjonskrav."
}
```

---

## Regeltreff (RuleMatch)

Når regelmotoren kobler et avvik til en regel, opprettes en `RuleMatch`-entitet:

```python
class RuleMatch(Base):
    __tablename__ = "rule_matches"

    id: UUID
    deviation_id: UUID   # Avviket som er matchet
    rule_id: str         # Regel-ID (spesifikk versjon)
    match_confidence: float  # 0.0–1.0
    match_reason: str    # Begrunnelse (vises i intern rapport)
    created_at: datetime
```

`match_confidence` beregnes av regelmotoren basert på:
- Avvikskategori vs. regelens `applies_to_categories`
- AI-analyse av om regelens krav er relevant for det spesifikke avviket
- Avvikets `confidence_score`

---

## Koblingslogikk i regelmotoren

```python
async def match_rules_for_deviation(deviation: Deviation) -> list[RuleMatch]:
    """
    1. Hent alle aktive regler som har avvikets kategori i applies_to_categories
    2. For hver regel: beregn match_confidence basert på AI-analyse
    3. Filtrer ut matcher med confidence < 0.40
    4. Returner sorterte matcher (høyest confidence øverst)
    """
    ...
```

---

## Begrensninger

- Regelregisteret er ikke en fullstendig juridisk database – det er et referanseverktøy
- Lokale reguleringsplaner og kommunale vedtekter er ikke inkludert i MVP
- Tolkninger av paragrafer kan variere – arkitekten er alltid siste instans
- Regler oppdateres ved endringsforskrifter. Det er redaktørens ansvar å vedlikeholde registeret
