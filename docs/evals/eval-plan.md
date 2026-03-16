# Evalueringsplan – ByggSjekk Avviksmotor

**Versjon:** 0.1
**Sist oppdatert:** 2024

---

## Formål

Sikre at avviksmotoren har tilstrekkelig presisjon og recall for å være nyttig for arkitekter i produksjon. Evalueringene kjøres mot et kontrollert mock-datasett med kjente, annoterte avvik.

Målet er ikke perfeksjon – det er å forstå systemets styrker og svakheter, og å bruke dette til å prioritere forbedringer.

---

## Suksesskriterier

| Metrikk | Minimumskrav | Mål |
|---------|-------------|-----|
| Presisjon (precision) | > 70 % | > 85 % |
| Recall | > 65 % | > 80 % |
| Confidence-kalibrering | Brier score < 0.15 | < 0.10 |
| Behandlingstid per sak | < 5 min | < 2 min |
| Kostnad per sak (AI-tokens) | < 1,00 USD | < 0,30 USD |

---

## Mock-datasett

### Struktur

Mock-datasettet består av par av godkjente planer og «dagens planer» der avvikene er kjente og annotert av fagpersoner.

Datasettet er lagret i `tests/fixtures/evals/` og inneholder:

```
tests/fixtures/evals/
├── cases/
│   ├── case_001/          # Liten leilighet med ett avvik
│   ├── case_002/          # Stor leilighet med fire avvik
│   ├── case_003/          # Enebolig med tilbygg
│   ├── case_004/          # Loftsleilighet med ulovlig innredning
│   ├── case_005/          # Ingen avvik (null-case)
│   └── ...
└── annotations/
    ├── case_001_expected.json
    ├── case_002_expected.json
    └── ...
```

### Annotasjonsformat

```json
{
  "case_id": "case_001",
  "description": "2-roms leilighet, ett avvik: soverom gjort om til kontor",
  "approved_plan": "cases/case_001/approved.json",
  "current_plan": "cases/case_001/current.json",
  "expected_deviations": [
    {
      "category": "BEDROOM_UTILITY_DISCREPANCY",
      "severity": "HIGH",
      "affected_room_ids": ["rom-02"],
      "description_keywords": ["soverom", "kontor", "bruksendring"],
      "minimum_confidence": 0.75,
      "rule_ids_expected": ["pbl-31-2-bruksendring", "tek17-12-2-rom-varig-opphold"]
    }
  ],
  "expected_no_deviation_categories": [
    "ADDITION_DETECTED",
    "BALCONY_TERRACE_DISCREPANCY"
  ]
}
```

### Testtilfeller

| Case | Beskrivelse | Antall avvik | Kategorier |
|------|-------------|-------------|-----------|
| case_001 | 2-roms leilighet, soverom → kontor | 1 | BEDROOM_UTILITY_DISCREPANCY |
| case_002 | Stor leilighet, balkong innbygd + tilbygg | 2 | BALCONY_TERRACE_DISCREPANCY, ADDITION_DETECTED |
| case_003 | Enebolig, uregistrert loftsrom + kjeller | 2 | ADDITION_DETECTED, UNDERBUILDING_DETECTED |
| case_004 | Leilighet, bod → soverom + bad utvidet | 2 | BEDROOM_UTILITY_DISCREPANCY, ROOM_DEFINITION_CHANGE |
| case_005 | Leilighet uten avvik (nullcase) | 0 | – |
| case_006 | Bolig med bruksendring til hybelleilighet | 1 | USE_CHANGE_INDICATION |
| case_007 | Salgsoppgave vs. godkjent plan (3 vs. 4 rom) | 1 | MARKETED_FUNCTION_DISCREPANCY |
| case_008 | Kompleks sak med 5 avvik | 5 | Mix av alle kategorier |
| case_009 | Dårlig tegningskvalitet (lav OCR-score) | 2 | ADDITION_DETECTED, ROOM_DEFINITION_CHANGE |
| case_010 | Eldre eiendom (pre-1970), manglende dokumentasjon | 3 | UNINSPECTED_AREA, UNKNOWN |

---

## Metrikker

### Presisjon (Precision)

Andel riktig detekterte avvik av totalt antall detekterte avvik.

```
Presisjon = Sanne positive / (Sanne positive + Falske positive)
```

En lav presisjon betyr at systemet rapporterer mange avvik som ikke er reelle. Arkitekten mister tillit og bruker mye tid på å avvise falske alarmer.

### Recall

Andel detekterte avvik av totalt antall faktiske avvik.

```
Recall = Sanne positive / (Sanne positive + Falske negative)
```

En lav recall betyr at systemet overser reelle avvik. For byggesaker er dette potensielt mer alvorlig enn lav presisjon.

### Confidence-kalibrering (Brier Score)

Brier score måler om systemets confidence-skorer er kalibrerte – altså om en 0.80-score faktisk betyr at avviket er riktig 80 % av tilfellene.

```
Brier = (1/N) × Σ(confidence_i - outcome_i)²
```

Der `outcome_i = 1` for sanne positive og `0` for falske positive. Lavere Brier er bedre. Perfekt kalibrering = 0.

### Kategori-presisjon

Presisjon og recall beregnes per avvikskategori for å identifisere svakheter i spesifikke deteksjonstyper.

### Kostnad per sak

Beregnes som summen av OpenAI/Anthropic token-kostnader for alle AI-kall i en saksbehandling.

---

## Kjøre evalueringer

### Forutsetninger

```bash
make seed         # Seed regelbase og mock-testdata
```

### Kjøre alle evalueringer

```bash
make eval
# Tilsvarer: docker compose exec api python scripts/run_evals.py
```

### Kjøre spesifikk case

```bash
make shell-api
python scripts/run_evals.py --case case_002
```

### Output-format

```
ByggSjekk Eval – 2024-01-15 14:23:01
=====================================

Testtilfeller kjørt: 10
Totalt kjøretid:     42.3 sekunder

SAMMENDRAG
----------
Presisjon:           82.4 %
Recall:              76.8 %
F1:                  79.5 %
Brier score:         0.112

KATEGORI-PRESISJON
------------------
BEDROOM_UTILITY_DISCREPANCY  Presisjon: 91 %  Recall: 88 %
ADDITION_DETECTED             Presisjon: 85 %  Recall: 80 %
BALCONY_TERRACE_DISCREPANCY  Presisjon: 78 %  Recall: 70 %
USE_CHANGE_INDICATION         Presisjon: 65 %  Recall: 55 %
UNINSPECTED_AREA              Presisjon: 60 %  Recall: 45 %

SVAKE CASE
----------
case_009 (lav tegningskvalitet):  Presisjon: 50 %  Recall: 67 %
case_010 (eldre eiendom):         Presisjon: 45 %  Recall: 33 %

KOSTNAD
-------
Gjennomsnitt per sak:  $0.18
Totalt for 10 saker:   $1.82
```

---

## Forbedringsstrategi

### Lav presisjon i en kategori

1. Analyser falske positive: hvilke tegningspar trigger feilaktig avvik?
2. Juster prompten i `apps/api/prompts/` for den aktuelle kategorien
3. Vurder om confidence-terskelen bør heves for kategorien

### Lav recall i en kategori

1. Analyser falske negative: hvilke kjente avvik overser systemet?
2. Berik prompten med eksempler på det utelatte avvikstypen
3. Vurder om planparser-konfidensen er for lav (dårlig OCR → dårlig romdeteksjon)

### Dårlig kalibrering (høy Brier score)

1. Se på fordelingen av confidence-scorer for sanne positive vs. falske positive
2. Vurder om modellen systematisk over- eller underestimerer
3. Implementer isotonic regression (post-hoc kalibrering) for confidence-scorer

---

## Kontinuerlig evaluering

Evalueringer kjøres automatisk:
- **Ved PR til main:** GitHub Actions kjører eval-skriptet mot mock-datasettet
- **Ukentlig:** Full evaluering mot utvidet datasett med nye testtilfeller
- **Ved AI-modelloppgradering:** Fullstendig re-evaluering mot alle kjente testtilfeller

Resultater lagres i `tests/eval_results/` med tidsstempel og modellversjon.

```
tests/eval_results/
├── 2024-01-15_gpt-4o-2024-05-13.json
├── 2024-01-22_gpt-4o-2024-05-13.json
└── 2024-02-01_gpt-4o-2024-08-06.json  ← ny modellversjon
```

Dette gjør det mulig å spore ytelsesutvikling over tid og oppdage regrediering ved modelloppgraderinger.
