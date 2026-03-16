# ADR-005: ApprovalStatus-modellen – fire tilstander i stedet for binær godkjent/ikke-godkjent

**Status:** Akseptert
**Dato:** 2024
**Beslutningstakere:** Konsepthus AS

---

## Kontekst

ByggSjekk skal vurdere om byggetegninger og tillatelser er «godkjente». Dette høres enkelt ut, men er i praksis svært komplekst i norsk kontekst:

### Problemet med binær godkjenning

1. **Historisk manko:** Byggetillatelser fra 1950–1990 er i mange tilfeller ikke digitalisert. Kommunale arkiv har hull. Det betyr at vi ikke kan verifisere om noe er godkjent – men det er heller ikke bevis for at det *ikke* er godkjent.

2. **Antakelsesregelen:** Eldre bygningsmasse som har stått i 20+ år uten inngrep antas typisk å ha en form for godkjenning, selv om dokumentasjonen mangler. En binær modell ville kreve at vi merker disse som «ikke godkjent», noe som er misvisende.

3. **Ulike kildetyper:** Et dokument hentet fra eByggSak har høyere tillitsgrad enn et dokument lastet opp av kjøperen av en eiendom. En binær modell skiller ikke mellom disse.

4. **Juridisk ansvar:** Dersom systemet sier «godkjent» uten tilstrekkelig grunnlag, kan dette brukes som bevis i en tvist. Dersom det sier «ikke godkjent» om noe som faktisk er godkjent, skaper det unødvendig støy. Kategoriske konklusjoner fra et automatisert system er juridisk risikabelt.

5. **Arkitektens ansvar:** Arkitekten er siste kontrollinstans. Systemet skal hjelpe arkitekten å forstå *hva vi vet* og *hva vi ikke vet* – ikke gi kategoriske svar som arkitekten ikke kan etterprøve.

---

## Beslutning

Vi bruker en **firetilstands ApprovalStatus-modell** i stedet for binær godkjent/ikke-godkjent:

```python
class ApprovalStatus(str, Enum):
    RECEIVED           = "RECEIVED"
    ASSUMED_APPROVED   = "ASSUMED_APPROVED"
    VERIFIED_APPROVED  = "VERIFIED_APPROVED"
    UNKNOWN            = "UNKNOWN"
```

### Tilstandsdefinisjoner

| Status | Beskrivelse | Tillitsgrad | Typisk kilde |
|--------|-------------|-------------|-------------|
| `RECEIVED` | Dokumentet er mottatt, ingen vurdering enda | N/A | Ny opplasting |
| `ASSUMED_APPROVED` | Antatt godkjent basert på kontekst | MEDIUM | Kommunalt arkiv (eldre), SEFRAK |
| `VERIFIED_APPROVED` | Maskinelt verifisert godkjenning | HIGH | eByggSak, manuell arkitektbekreftelse |
| `UNKNOWN` | Kan ikke fastslås | LOW | Ingen kobling funnet, ingen referanse |

### Regler for tilstandsoverganger

```
RECEIVED
   │
   ├── kommunekobling finner treff med referanse → VERIFIED_APPROVED
   ├── kommunekobling finner trolig-treff (eldre, ingen digital sak) → ASSUMED_APPROVED
   ├── kommunekobling finner ingenting → UNKNOWN
   └── arkitekt bekrefter manuelt → VERIFIED_APPROVED
```

### Hva systemet ALDRI sier

- «Dokumentet er **ikke godkjent**» – vi sier «status er UNKNOWN» eller «godkjenning kan ikke verifiseres»
- «Tiltaket er **ulovlig**» – vi sier «potensielt avvik, bør vurderes av arkitekt»
- «Du **må** søke kommunen» – vi sier «dette kan indikere søknadspliktig tiltak»
- «Dette er **godkjent**» uten `VERIFIED_APPROVED`-status

---

## Begrunnelse

### Epistemisk redelighet

En programvare som sier «dette er godkjent» eller «dette er ikke godkjent» uten å ha tilgang til fullstendig kommunalt arkiv er epistemisk uærlig. Vi vet hva vi vet, og vi vet hva vi ikke vet. Modellen gjenspeiler dette.

### Juridisk trygghet

Kategoriske juridiske konklusjoner fra et automatisert system eksponerer leverandøren for ansvar. «Systemet sa det var godkjent» er et argument en domstol kan ta på alvor. Ved å tydeliggjøre tillitsgrad og overlate konklusjonen til arkitekten, plasseres det juridiske ansvaret der det hører hjemme.

### Brukervennlighet

For arkitekter er det mer nyttig å se «ASSUMED_APPROVED – hentet fra kommunalt arkiv, ingen ferdigattest funnet» enn en binær status. De kan da vurdere om de trenger å kontakte kommunen for bekreftelse.

### Kalibrering av confidence

`ApprovalStatus` brukes av avviksmotoren til å vekte avvik. Et avvik basert på et `UNKNOWN`-kildedokument vektes lavere enn et basert på `VERIFIED_APPROVED`. Binær status ville ikke gi denne nyansen.

---

## Konsekvenser for UI

Grensesnittet kommuniserer status på et forståelig norsk:

| Status | Visning i UI |
|--------|-------------|
| `RECEIVED` | «Mottatt – under behandling» |
| `ASSUMED_APPROVED` | «Sannsynlig godkjent (ikke verifisert)» med gult ikon |
| `VERIFIED_APPROVED` | «Verifisert godkjent» med grønt ikon |
| `UNKNOWN` | «Godkjenningsstatus ukjent» med grått ikon |

Farger: grønn = verifisert, gul = antatt, grå = ukjent. Aldri rød = «ikke godkjent».

---

## Alternativer vurdert

### Binær godkjent/ikke-godkjent

**Forkastet fordi:**
- Gir falsk sikkerhet i begge retninger
- Juridisk risikabelt
- Reflekterer ikke virkeligheten i norsk byggesaksarkiv

### Tredelt modell (godkjent/ukjent/ikke-godkjent)

**Forkastet fordi:**
- «Ikke godkjent» er en kategorisk juridisk konklusjon systemet ikke har grunnlag for å gi
- Setter arkitektens ansvar til side

### Fritekst-status

**Forkastet fordi:**
- Vanskelig å bruke programmatisk for confidence-vekting
- Inkonsistent på tvers av saker

---

## Gjennomgangspunkt

- Vurder om `ASSUMED_APPROVED` bør splittes i `ASSUMED_APPROVED_HISTORICAL` og `ASSUMED_APPROVED_CONTEXT` ved behov for mer granularitet (fase 4)
- Innhent tilbakemelding fra pilotarkitekter om hvorvidt modellen er forståelig
