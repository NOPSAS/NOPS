# Hvordan legge til nye regler – ByggSjekk

**Versjon:** 0.1
**Sist oppdatert:** 2024

---

## Oversikt

Nye regler legges til i regelregisteret ved å redigere seed-skriptet og kjøre det mot databasen. Dette sikrer at reglene er versjonskontrollert og kan spores tilbake til en faglig kilde.

---

## Steg-for-steg guide

### Steg 1: Identifiser regelen som skal legges til

Finn den relevante paragrafen i:
- **TEK17** – Teknisk forskrift: https://lovdata.no/dokument/SF/forskrift/2017-06-19-840
- **PBL** – Plan- og bygningsloven: https://lovdata.no/dokument/NL/lov/2008-06-27-71
- **SAK10** – Byggesaksforskriften: https://lovdata.no/dokument/SF/forskrift/2010-03-26-488
- **DiBK** – Veiledere fra Direktoratet for byggkvalitet: https://dibk.no

### Steg 2: Velg riktig avvikskategori

Hvilke avvikskategorier er regelen relevant for? Se `docs/domain/deviation-categories.md` for oversikt.

Eksempel: En regel om rømningsveier er relevant for `DOOR_PLACEMENT_CHANGE` og `WINDOW_PLACEMENT_CHANGE`, men ikke for `BALCONY_TERRACE_DISCREPANCY`.

### Steg 3: Generer regel-ID

Format: `{kilde_lowercase}-{paragraf_slug}-{beskrivende_slug}`

Eksempler:
- `tek17-11-13-romningsvei` (TEK17 § 11-13, rømningsvei)
- `pbl-29-4-teknisk-infrastruktur` (PBL § 29-4)
- `sak10-6-7-midlertidig-brukstillatelse` (SAK10 § 6-7)

Regler for slug:
- Kun lowercase bokstaver, tall og bindestreker
- Ingen æøå (bruk ae, oe, aa)
- Maks 80 tegn total

### Steg 4: Legg til regelen i seed-skriptet

Åpne `scripts/seed_rules.py` og legg til en ny dict i `RULES`-listen:

```python
{
    "id": "tek17-11-13-romningsvei",
    "source": "TEK17",
    "paragraph": "§ 11-13",
    "title": "Rømning fra byggverk",
    "short_description": "Byggverk skal ha tilstrekkelige rømningsveier.",
    "full_text": (
        "Byggverk skal prosjekteres og utføres slik at det er tilfredsstillende "
        "mulighet for rømning ved brann. Rømningsveier skal ha tilstrekkelig "
        "bredde, høyde og lengde slik at alle kan komme seg raskt ut. "
        "Rømningsvei skal ha dør eller vindu som kan åpnes."
    ),
    "applies_to_categories": [
        "DOOR_PLACEMENT_CHANGE",
        "WINDOW_PLACEMENT_CHANGE",
        "ADDITION_DETECTED",
    ],
    "severity_hint": "CRITICAL",
    "version": "2017-06-19",
    "active": True,
    "notes": (
        "Kritisk for brannsikkerhet. Avvik mot rømningsveier skal alltid "
        "flagges som CRITICAL og krever umiddelbar arkitektvurdering."
    ),
},
```

### Steg 5: Valider regelen

Kontroller at:
- [ ] `id` er unikt i `RULES`-listen (søk etter ID-en i filen)
- [ ] `source` er en av: `TEK17`, `PBL`, `SAK10`, `DTILM`, `NS3700`, `LOKAL`
- [ ] `paragraph` er korrekt paragrafhenvisning
- [ ] `applies_to_categories` inneholder gyldige `DeviationCategory`-verdier (se `packages/shared_types/models.py`)
- [ ] `severity_hint` er en av: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- [ ] `version` er ISO-dato for regelens gjeldende versjon
- [ ] `full_text` er en nøyaktig gjengivelse av regelens innhold (kan forkortes, men ikke parafraseres)

### Steg 6: Kjør seed-skriptet

```bash
# Alternativ 1: Via Makefile (anbefalt)
make seed-rules

# Alternativ 2: Direkte (krever at du er i API-containeren)
make shell-api
python scripts/seed_rules.py
```

Seed-skriptet bruker upsert. Eksisterende regler oppdateres hvis `id` allerede finnes.

### Steg 7: Verifiser i databasen

```bash
make shell-db
```

```sql
-- Sjekk at regelen er lagt inn
SELECT id, source, paragraph, title, active
FROM rules
WHERE id = 'tek17-11-13-romningsvei';

-- Sjekk at avvikskategoriene er korrekte
SELECT applies_to_categories
FROM rules
WHERE id = 'tek17-11-13-romningsvei';
```

### Steg 8: Test regelmatching

Kjør API-testene for å verifisere at den nye regelen matcher riktige avvik:

```bash
make test-api
```

Legg til en enhetstest i `apps/api/tests/test_rule_engine.py` dersom den nye regelen krever spesiell matchlogikk.

---

## Oppdatere en eksisterende regel

### Mindre rettelse (f.eks. skrivefeil)

Endre teksten direkte i `seed_rules.py` og kjør `make seed-rules`. Upsert vil oppdatere eksisterende rad.

**Obs:** Oppdater `version`-feltet dersom den juridiske kilden er endret.

### Vesentlig regelendring (ny versjon av forskriften)

Dersom en paragraf er vesentlig endret i en ny versjon av loven:

1. Sett `active = False` på den gamle regelen
2. Legg til `superseded_by = "ny-regel-id"` på den gamle
3. Opprett ny regel med nytt `id` (f.eks. `tek17-12-2-rom-varig-opphold-2025`)
4. Kjør `make seed-rules`

Historiske regeltreff beholder referansen til den gamle regelen (for sporbarhet).

---

## Slette en regel

Regler **slettes aldri** fra databasen – de deaktiveres:

```python
# I seed_rules.py: sett active = False
{
    "id": "gammel-regel-id",
    ...
    "active": False,
    "superseded_by": "ny-regel-id",
}
```

Deaktiverte regler brukes ikke av regelmotoren, men beholdes for historiske saksreferanser.

---

## Kvalitetskrav til regler

### Hva som er tillatt

- Direkte sitat fra lovteksten (med kildeangivelse)
- Lett forkortet versjon som bevarer det juridisk relevante innholdet
- Kombinasjon av to relaterte ledd i samme paragraf

### Hva som ikke er tillatt

- Parafrasering som endrer regelens juridiske innhold
- Tolkninger («dette betyr at...») i `full_text`-feltet
- Bruk av ordene «ulovlig», «godkjent» eller «krever søknad» som absolutte konklusjoner i beskrivelsene

### Faglig gjennomgang

Nye regler som er juridisk komplekse bør gjennomgås av en faglig ansvarlig arkitekt (ARK) eller jurist med byggesakkompetanse før de settes til `active = True` i produksjon.

---

## Eksempler på gode og dårlige regelbeskrivelser

### God beskrivelse

```
short_description: "Rom for varig opphold skal ha vindu mot det fri og naturlig ventilasjon."
full_text: "Rom for varig opphold skal ha vindu mot det fri med tilfredsstillende lysflate
            og mulighet for naturlig ventilasjon. Minimumsareal er 7 m²."
```

### Dårlig beskrivelse (unngå)

```
# For absolutt – vi vet ikke hva arkitektens vurdering er
short_description: "Det er ulovlig å bruke rom under 7 m² som soverom."

# For vag – gir ikke nok kontekst
short_description: "Krav til rom."

# Tolkning, ikke regelhenvisning
full_text: "Dette betyr at du alltid må søke kommunen dersom rommet er for lite."
```

---

## Vedlikehold av regelregisteret

Regelregisteret bør gjennomgås:
- **Årlig:** Sjekk om det er kommet endringsforskrifter til TEK17, PBL eller SAK10
- **Ved lansering av ny lov:** Rask gjennomgang og merking av berørte regler
- **Ved tilbakemeldinger fra arkitekter:** Regeltreff som konsistent avvises av arkitekter indikerer svak matching-logikk

Ansvarsforhold:
- **Teknisk redaktør:** Ansvarlig for at seed-skriptet er oppdatert
- **Faglig ansvarlig (ARK):** Godkjenner regelinnhold før `active = True` i produksjon
