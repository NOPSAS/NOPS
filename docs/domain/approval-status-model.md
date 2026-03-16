# Godkjenningsstatus-modellen – ByggSjekk

**Versjon:** 0.1
**Sist oppdatert:** 2024

---

## Innledning

ByggSjekk bruker en **firetilstands ApprovalStatus-modell** for å representere godkjenningsstatusen til kildedokumenter (tegninger, tillatelser). Modellen er designet for å reflektere den faktiske epistemiske situasjonen – hva vi vet, og hva vi ikke vet – fremfor å gi kategoriske svar systemet ikke har grunnlag for.

Se også [ADR-005](../adr/ADR-005-godkjenningsstatus.md) for den arkitektoniske begrunnelsen.

---

## De fire tilstandene

### RECEIVED – Mottatt

```
Tillitsgrad: N/A (ingen vurdering enda)
Ikon i UI: Grå sirkel (in progress)
```

Dokumentet er lastet opp og registrert i systemet. Ingen vurdering av godkjenningsstatus er gjort enda. Dokumentet er i kø for prosessering.

**Overgang fra RECEIVED:**
- Systemet prøver å finne godkjenning via kommunekobling
- Arkitekt kan manuelt bekrefte eller endre status

---

### ASSUMED_APPROVED – Antatt godkjent

```
Tillitsgrad: MEDIUM
Ikon i UI: Gult skjold med spørsmålstegn
```

Dokumentet antas å være godkjent basert på kontekstuell informasjon, men godkjenningen er ikke maskinelt verifisert.

**Grunnlag for ASSUMED_APPROVED:**
- Dokumentet er hentet fra kommunalt arkiv (eldre dokumenter uten digital saksreferanse)
- Dokumentet er registrert i SEFRAK (Statens register over fredete og vernete anlegg)
- Dokumentet har alderskarakter som tilsier det stammer fra en regulær byggesaksprosess (f.eks. tegningsformat og -stil fra 1960–1990)
- Eiendommen har ferdigattest for en tilsvarende periode, men det spesifikke dokumentet mangler referanse

**Viktig:** ASSUMED_APPROVED betyr *ikke* at systemet bekrefter godkjenning. Det betyr at konteksten gjør godkjenning sannsynlig. Arkitekten bør vurdere om dette er tilstrekkelig eller om ytterligere verifisering er nødvendig.

**Avviksvekting:** Avvik basert på ASSUMED_APPROVED-dokumenter har en moderat vekting. De rapporteres, men med en merknad om at kildens godkjenningsstatus ikke er fullstendig verifisert.

---

### VERIFIED_APPROVED – Verifisert godkjent

```
Tillitsgrad: HIGH
Ikon i UI: Grønt skjold med hake
```

Godkjenning er verifisert via én av følgende metoder:

1. **Kommunekobling:** eByggSak eller tilsvarende digital kommuneintegrasjon returnerte et treff med saksreferanse og godkjenningsdato
2. **Manuell arkitektbekreftelse:** En autorisert arkitekt har manuelt bekreftet godkjenningen i systemet (med audit trail)
3. **Ferdigattest:** Kommunen har utstedt ferdigattest for det aktuelle tiltaket

**Avviksvekting:** Avvik basert på VERIFIED_APPROVED-dokumenter vektes høyest. Dette er kilden til sannhet for hva som faktisk er godkjent.

---

### UNKNOWN – Ukjent

```
Tillitsgrad: LOW
Ikon i UI: Grå sirkel med spørsmålstegn
```

Godkjenningsstatus kan ikke fastslås. Dette er **ikke** det samme som «ikke godkjent» – det betyr at vi ikke har tilstrekkelig informasjon til å fastslå noen ting.

**Årsaker til UNKNOWN:**
- Kommunekobling returnerte ingen treff for gnr/bnr-kombinasjonen
- Dokumentet mangler saksreferanse og kjenne-tegn på kommunalt opphav
- Dokumentet er lastet opp av privatperson uten kildeangitt
- Kommunen har ikke digital integrasjon, og manuell forespørsel er ikke gjort
- Dokumentet er for gammelt til å finnes i digitale systemer (pre-1960)

**Avviksvekting:** Avvik basert på UNKNOWN-dokumenter vektes lavere. De rapporteres med en tydelig merknad om at kildens status er ukjent, og arkitekten bør verifisere manuelt.

---

## Hvorfor ikke binær godkjent/ikke-godkjent?

### Problemet med «Ikke godkjent»

I norsk byggesakshistorie er det normalt at:
- Byggetillatelser fra 1950–1990 ikke er digitalisert
- Kommunale arkiv har hull, særlig for eldre bygningsmasse
- Ferdigattest ikke ble utstedt som en obligatorisk avslutning frem til SAK10 (2010)

Et system som tolker «ingen digital sak funnet» som «ikke godkjent» ville:
- Flagge store deler av norsk boligmasse som problematisk
- Gi falsk trygghet i saker der det faktisk mangler tillatelse (f.eks. nyere ulovlige tiltak som heller ikke finnes digitalt)
- Sette juridisk ansvar på et automatisert system som ikke har grunnlag for konklusjonen

### Problemet med «Godkjent»

Et system som sier «godkjent» uten tilstrekkelig grunnlag:
- Kan brukes som bevis i en tvist («systemet sa det var OK»)
- Gir arkitekten falsk trygghet
- Eksponerer tjenesteleverandøren for juridisk ansvar

### Løsningen: Transparens om usikkerhet

ByggSjekk er ærlig om hva det vet og ikke vet. Tillitsgraden er synlig i brukergrensesnittet og rapportene. Arkitekten får informasjonsgrunnlag til å ta en kvalifisert faglig beslutning – ikke et system som ta beslutningen for dem.

---

## Konfidenssammenheng

ApprovalStatus henger tett sammen med confidence-scorer:

| Status | Typisk doc confidence | Påvirkning på avviksscore |
|--------|----------------------|--------------------------|
| VERIFIED_APPROVED | 0.90–0.99 | Avvik vektes fullt |
| ASSUMED_APPROVED | 0.60–0.89 | Avvik vektes med 0.85× faktor |
| RECEIVED | N/A | Avviksvurdering venter |
| UNKNOWN | 0.00–0.59 | Avvik vektes med 0.70× faktor |

---

## Tilstandsovergangsdiagram

```
                      ┌─────────────────┐
                      │    RECEIVED     │
                      │  (ny opplasting)│
                      └────────┬────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
   ┌──────────────────┐  ┌───────────────────┐  ┌─────────┐
   │ VERIFIED_APPROVED│  │ ASSUMED_APPROVED  │  │ UNKNOWN │
   │ (kommunetreff    │  │ (kontekstuell     │  │ (ingen  │
   │  eller arkitekt  │  │  match)           │  │  treff) │
   │  bekrefter)      │  └────────┬──────────┘  └────┬────┘
   └──────────────────┘          │                   │
                                 │ arkitekt           │ arkitekt
                                 │ verifiserer        │ verifiserer
                                 ▼                   ▼
                       ┌──────────────────┐
                       │ VERIFIED_APPROVED│
                       └──────────────────┘
```

---

## Praktisk eksempel

**Sak: Storgata 1, Oslo – leilighet 3. etg**

| Dokument | Kilde | Status | Begrunnelse |
|----------|-------|--------|-------------|
| Rammetillatelse 2005 | eByggSak Oslo | VERIFIED_APPROVED | Saksreferanse SAK/2005/1234 funnet i eByggSak |
| Ferdigattest 2006 | eByggSak Oslo | VERIFIED_APPROVED | Ferdigattest FA/2006/0456 verifisert |
| Dagens plantegning (2024) | Kundeoplasting | UNKNOWN | Privat opplasting, ingen kommunal referanse |

**Konsekvens for avviksvurdering:**
- Avvik mellom rammetillatelse (VERIFIED_APPROVED) og dagens plan (UNKNOWN) vektes fullt
- Rapporten inneholder en merknad: «Dagens plantegning er ikke kommunalt verifisert. Vurdering er basert på kundens opplastede dokument.»
