# Avvikskategorier – ByggSjekk

**Versjon:** 0.1
**Sist oppdatert:** 2024

---

## Oversikt

ByggSjekk bruker 10 avvikskategorier som dekker de vanligste avvikstypene arkitekter møter ved tilstandsvurdering av norsk boligmasse. Kategoriene er designet for å:

1. Reflektere faktiske avvikstyper i norsk bygningsmasse
2. Koble naturlig til relevante paragrafer i TEK17, PBL og SAK10
3. Være forståelige for arkitekter uten teknisk bakgrunn

---

## Kategori 1: ROOM_DEFINITION_CHANGE
**Norsk navn:** Romdefinisjonsendring

### Beskrivelse
Et rom har endret sin definisjon, inndeling eller bruk siden godkjent tegning ble laget. Dette inkluderer sammenslåing av rom, oppdeling av større rom, eller endring av romgrenser uten at det er registrert søknadsbehandling.

### Eksempelscenarier
- Stue og kjøkken er slått sammen til ett åpent plan (veggen er fjernet)
- Et stort soverom er delt i to med skillevegg
- Entré er blitt del av stuen (skillevegg fjernet)
- Kjøkken er blitt en del av stuen (åpent kjøkken)

### Typisk confidence-spenn
- **0.80–0.95** ved klare geometriske endringer
- **0.55–0.79** ved uklare grenser (f.eks. åpent plan vs. definerte rom)

### Relevante regler
- TEK17 § 12-2 (krav til rom for varig opphold – minste areal)
- PBL § 20-1 (søknadsplikt ved vesentlig endring)

---

## Kategori 2: BEDROOM_UTILITY_DISCREPANCY
**Norsk navn:** Soverom / bruksromsavvik

### Beskrivelse
Et rom er merket som soverom i godkjent tegning men fremstår som noe annet i dagens plan (eller omvendt). Dette er særlig relevant ved eiendomssalg, der selger kan ha markedsfort et rom som soverom uten at det oppfyller kravene.

### Eksempelscenarier
- Soverom 2 i godkjent plan er nå merket «Kontor» i dagens plan
- «Hobbyrom» eller «loft» er markedsfort som soverom i salgsoppgaven
- Bod er gjort om til soverom uten vindusareal som kreves av TEK17

### Typisk confidence-spenn
- **0.85–0.95** ved klare etikettendringer
- **0.60–0.84** ved arealmatch men funksjonsendring

### Relevante regler
- TEK17 § 12-2 (rom for varig opphold: minimum 7 m², vindu mot det fri)
- TEK17 § 12-6 (lysflate minimum 10 % av gulvareal)
- PBL § 31-2 (bruksendring av eksisterende byggverk)

---

## Kategori 3: DOOR_PLACEMENT_CHANGE
**Norsk navn:** Endret dørplassering

### Beskrivelse
Dørens plassering, retning eller eksistens er endret fra godkjent tegning. Endret dørplassering kan ha konsekvenser for rømningsveier og branncelleinndeling.

### Eksempelscenarier
- Dør mellom stue og entré er fjernet
- Ytterdør er flytta til annen vegg
- Ny dør er åpna i bærende vegg uten søknad
- Dør til rømningstrapp er blokkert eller fjernet

### Typisk confidence-spenn
- **0.75–0.92** ved klare endringer
- **0.45–0.74** ved usikker tegningskvalitet eller skjulte dørplasseringer

### Relevante regler
- TEK17 § 11-13 (rømning fra byggverk)
- TEK17 § 11-8 (branncelleinndeling)

---

## Kategori 4: WINDOW_PLACEMENT_CHANGE
**Norsk navn:** Endret vindusplassering

### Beskrivelse
Vindusplassering, -størrelse eller -antall er endret fra godkjent tegning. Vindusendringer kan påvirke lysflate, naturlig ventilasjon og rømningsveier.

### Eksempelscenarier
- Vindu er fjernet fra soverom (bryter lysflate-krav)
- Nytt vindu er satt inn i fasade uten tillatelse (fasadeendring)
- Kjellervindu er forstørret til rømningsvindus-størrelse
- Vindusprofiler er endret (ikke strukturelt, men estetisk – kan utløse fasadeendringssøknad)

### Typisk confidence-spenn
- **0.80–0.95** ved målbare endringer
- **0.50–0.79** ved usikker tegningskvalitet

### Relevante regler
- TEK17 § 12-6 (lysflate og ventilasjon)
- PBL § 20-1 bokstav c (fasadeendring er søknadspliktig)

---

## Kategori 5: BALCONY_TERRACE_DISCREPANCY
**Norsk navn:** Balkong / terrasseavvik

### Beskrivelse
Balkong eller terrasse er lagt til, fjernet eller vesentlig endret i størrelse sammenlignet med godkjent tegning. Innbygging av balkong til rom er et vanlig, søknadspliktig tiltak.

### Eksempelscenarier
- Balkong er bygget inn og gjort til en del av stuen
- Ny terrasse er bygget på taket uten tillatelse
- Balkong er forlenget (utvidet i bredde eller lengde)
- Terrasse er hevet til et høyere nivå enn godkjent (endret konstruksjon)

### Typisk confidence-spenn
- **0.78–0.92** ved klare geometriske avvik
- **0.55–0.77** ved usikker grense mellom balkong og terrasse

### Relevante regler
- TEK17 § 12-9 (krav til uteplass)
- PBL § 20-1 (tilbygg og endring er søknadspliktig)
- SAK10 § 4-1 (noen balkonger kan være unntatt søknad – avhengig av størrelse)

---

## Kategori 6: ADDITION_DETECTED
**Norsk navn:** Tilbygg oppdaget

### Beskrivelse
Et tilbygg eller ny bygningsdel er synlig i dagens plan som ikke finnes i godkjent tegning. Dette er en av de alvorligste kategoriene da tilbygg typisk er søknadspliktige og kan ha store konsekvenser.

### Eksempelscenarier
- Ny stue er bygd på baksiden av huset
- Veranda er lukket og gjort om til vinterhage uten søknad
- Garasje er bygd under terrasse og gjort til boligareal
- Nytt rom er lagt til i loftsetasjen (loftsombygging)

### Typisk confidence-spenn
- **0.85–0.97** ved klare geometriske tillegg
- **0.65–0.84** ved usikker tegning eller delvis synlig tilbygg

### Relevante regler
- PBL § 20-1 (tilbygging er eksplisitt søknadspliktig)
- SAK10 § 4-1 (unntak for tilbygg under 15 m² uten varig opphold)
- TEK17 § 12-15 (kan utløse heiskrav ved økt etasjetall)

---

## Kategori 7: UNDERBUILDING_DETECTED
**Norsk navn:** Underbygging oppdaget

### Beskrivelse
Underbygging (utgraving av kjeller under eksisterende bygg) er synlig i dagens plan men mangler i godkjent tegning. Underbygging er et konstruksjonskrevende og søknadspliktig tiltak.

### Eksempelscenarier
- Kjeller er gravd ut under boligens grunnmur uten søknad
- Lager i underetasje er gjort om til stue ved utgraving
- Parkeringskjeller er anlagt under felles uteplass

### Typisk confidence-spenn
- **0.70–0.90** – underbygging er sjelden, men klart detekterbar ved etasje-analyse

### Relevante regler
- PBL § 20-1 (underbygging er søknadspliktig)
- PBL § 20-3 (krever ansvarlig foretak)

---

## Kategori 8: UNINSPECTED_AREA
**Norsk navn:** Udokumentert areal

### Beskrivelse
Et område (rom, etasje, uthus) er synlig i dagens plan men mangler dokumentasjon i form av ferdigattest eller godkjent tegning. Dette er en indikasjon på at arbeidene ikke er formelt avsluttet.

### Eksempelscenarier
- Loft er innredet til rom, men mangler ferdigattest
- Uthus er bygd uten søknad og ikke etterregistrert
- Kjellerstue mangler ferdigattest, men er synlig i salgsoppgavens plantegning
- Garasje er konvertert til boligareal uten oppdaterte papirer

### Typisk confidence-spenn
- **0.60–0.85** – krever kryss-referanse mot kommunekobling for å fastslå manglende dokumentasjon

### Relevante regler
- SAK10 § 6-4 (krav til ferdigattest)
- PBL § 21-10 (ferdigattest – kommunens plikt til å utstede)

---

## Kategori 9: USE_CHANGE_INDICATION
**Norsk navn:** Bruksendring indikert

### Beskrivelse
Indikasjoner på at bygget eller deler av det brukes til noe annet enn godkjent formål. Bruksendring er søknadspliktig og kan ha store konsekvenser for brannsikkerhet, universell utforming og skattlegging.

### Eksempelscenarier
- Bolig brukt som kontorlokale (skilting, møtelokale i stue)
- Butikklokale konvertert til bolig uten søknad
- Hybelleilighet i kjeller (uten separat inngang i godkjent plan)
- Garasje brukt som verksted med næringsformål

### Typisk confidence-spenn
- **0.55–0.85** – bruksendring er vanskelig å detektere fra tegninger alene; krever kontekstuell analyse

### Relevante regler
- PBL § 20-1 bokstav d (bruksendring er søknadspliktig)
- PBL § 31-2 (tillatelse til bruksendring av eksisterende byggverk)

---

## Kategori 10: MARKETED_FUNCTION_DISCREPANCY
**Norsk navn:** Markedsfort funksjon avviker

### Beskrivelse
Et rom er markedsfort eller merket med en funksjon (f.eks. «soverom 3») som avviker fra hva godkjent tegning viser (f.eks. «bod» eller «stue»). Særlig relevant ved eiendomssalg og takstvurderinger, der feil markedsføring kan eksponere selger for ansvar.

### Eksempelscenarier
- Salgsoppgave viser «4-roms» men godkjent plan har 3 soverom og én bod
- «Soverom» i salgsoppgave er ikke godkjent som rom for varig opphold (mangler vindu)
- «Hybel» i underetasje er ikke godkjent som separat boenhet

### Typisk confidence-spenn
- **0.80–0.95** ved klare merkingsavvik
- **0.55–0.79** ved krevende tolkning av romfunksjon

### Relevante regler
- TEK17 § 12-2 (krav til rom for varig opphold)
- Avhendingslova § 3-8 (opplysningsplikt ved eiendomssalg)
- Eiendomsmeglingsloven § 6-7 (plikt til å opplyse om vesentlige forhold)

---

## Confidence-kalibrering

Systemet bruker følgende retningslinjer for confidence-scoring:

| Score | Etikett | Tolkning |
|-------|---------|----------|
| 0.90–1.00 | Svært høy | Avviket er nær sikkert. Anbefales bekreftet av arkitekt. |
| 0.75–0.89 | Høy | Avviket er sannsynlig. Bør gjennomgås. |
| 0.55–0.74 | Middels | Avviket er mulig. Krever mer dokumentasjon eller befaring. |
| 0.35–0.54 | Lav | Avviket er usikkert. Arkitekten bør bruke eget skjønn. |
| 0.00–0.34 | Svært lav | Automatisk avvisning vurderes. Vises kun i intern rapport. |

Avvik med confidence under 0.40 genererer ikke regeltreff og vises ikke i kunderapport.
