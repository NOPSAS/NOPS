# ADR-004: Versjonert regelregister

**Status:** Akseptert
**Dato:** 2024
**Beslutningstakere:** Konsepthus AS

---

## Kontekst

ByggSjekk bruker et regelregister for å koble avvik mot relevante norske byggeforskrifter (TEK17, PBL, SAK10). Regelregisteret er en kjernekomponent i systemet – det bestemmer hvilke juridiske referanser som vises i rapporter og hvilke avvik som flagges som høyprioriterte.

Utfordringer som må løses:

1. **Regler endres over tid:** TEK17 revideres (siste revisjon: 2017, med endringsforskrifter). PBL endres av Stortinget. SAK10 oppdateres. Historiske saker bør evalueres mot regelverket som gjaldt *da* saken ble behandlet, ikke dagens regelverk.

2. **Reproduserbarhet:** En sak behandlet i 2024 skal gi samme regeltreff om vi kjører analysen på nytt i 2027 (med en nyere regelbase). Vi må vite hvilken regelversjon som ble brukt.

3. **Gradvis utvidelse:** Regelregisteret starter med et lite sett regler (TEK17 § 12, PBL § 20) og vil vokse over tid. Vi trenger et design som tillater dette uten migrasjoner.

4. **Testbarhet:** Regelmotoren bør testes mot en kjent, fast regelbase – ikke mot en database som kan endres.

---

## Beslutning

Vi bruker et **database-drevet regelregister med versjonering på regel-nivå**, kombinert med seed-skript for initial populering og en uforanderlig `version`-kolonne per regel.

### Regelstruktur

```python
class Rule(Base):
    __tablename__ = "rules"

    id: str                    # Menneskelig ID: "tek17-12-2-rom-varig-opphold"
    source: str                # "TEK17", "PBL", "SAK10"
    paragraph: str             # "§ 12-2"
    title: str
    short_description: str
    full_text: str
    applies_to_categories: list[str]  # JSONB: ["ROOM_DEFINITION_CHANGE", ...]
    severity_hint: str
    version: date              # Dato for gjeldende versjon av regelen
    superseded_by: str | None  # ID til ny regel om denne er erstattet
    active: bool               # False = utdatert, men beholdes for historikk
    notes: str | None
```

### Versjonsstrategi

- Ny versjon av en regel opprettes som en **ny rad** med nytt `id` (f.eks. `tek17-12-2-rom-varig-opphold-2025`)
- Den gamle regelen får `active = False` og `superseded_by = "tek17-12-2-rom-varig-opphold-2025"`
- `RuleMatch`-tabellen lagrer `rule_id` som peker til den spesifikke regelversjonen som ble brukt
- Dette gjør at gamle saker beholder sin opprinnelige regelreferanse

### Regelkilde

Regler vedlikeholdes som seed-skript (`scripts/seed_rules.py`) som kjøres via `make seed-rules`. Skriptet bruker upsert – eksisterende regler oppdateres ikke (for å bevare historikk), men nye legges til.

---

## Begrunnelse

### Hvorfor database (ikke kode-filer)?

- Regler kan redigeres av fagpersoner (ikke nødvendigvis utviklere) via et admin-UI (fremtidig fase)
- Database tillater dynamisk utvidelse uten deployment
- SQL-spørringer mot regler er effektivt for regelmotor-matching

### Hvorfor ikke ren kodebasert regelbase?

- Endringer krever deployment
- Vanskeligere for ikke-tekniske brukere å vedlikeholde
- Vanskelig å implementere versionering pr. sak

### Hvorfor ikke en ekstern regelmotor (Drools, OpenFGA)?

- Overkill for dette bruksområdet
- Python-native løsning er enklere å vedlikeholde
- Vi bruker AI for avviksklassifisering, ikke forretningsregler-motor

### Sporbarhetsdesign

Alle `RuleMatch`-rader lagrer:
- `rule_id`: spesifikk regelversjon som ble brukt
- `match_confidence`: AI-beregnet relevans
- `match_reason`: forklaring på koblingen

Rapporten for en sak inkluderer alltid:
- Regel-ID og versjon
- Tidspunkt for regelmatching
- Hvilken regelmotor-versjon som kjørte

---

## Regelregisteret ved lansering

Initialt rulles ut med regler for:

| Kilde | Paragrafer |
|-------|-----------|
| TEK17 | §§ 12-2, 12-6, 12-7, 12-9, 12-15 |
| PBL | §§ 20-1, 20-3, 31-2 |
| SAK10 | §§ 4-1, 4-2, 6-4 |

Målet er 30–40 regler for MVP, med en vekstplan til 150+ regler ved full produktmodning.

---

## Alternativer vurdert

### JSON-filer i versjonskontroll

**Vurdert, forkastet fordi:**
- Endringer krever deployment
- Ingen dynamisk redigering mulig
- Vanskeligere å spørre (krever JSON-parsing i kode)

### Ekstern regelmotor (Drools / Rego / OpenPolicyAgent)

**Forkastet fordi:**
- Overkill for dette bruksområdet
- Legger til et ekstra system å vedlikeholde
- Dårlig integrasjon med Python/Pydantic-stakken vår

---

## Konsekvenser

- **Positiv:** Regler kan redigeres via admin-UI uten deployment
- **Positiv:** Full sporbarhet – vi vet alltid hvilken regelversjon som genererte en rapport
- **Positiv:** Historiske saker beholdes korrekte ved regelrevisjoner
- **Nøytral:** Seed-skript (`scripts/seed_rules.py`) er autoritativ kilde; database er avledet
- **Negativ:** Upsert-logikken i seed-skriptet må vedlikeholdes nøye for å ikke overskrive historikk
