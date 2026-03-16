"""
ByggSjekk / nops.no – Norsk regelverk for byggesaker.

Inneholder nøkkelparagrafer fra:
- Plan og bygningsloven (PBL) – LOV-2008-06-27-71
- Byggteknisk forskrift (TEK17) – FOR-2017-06-19-840
- Byggesaksforskriften (SAK10) – FOR-2010-03-26-488
- Eiendomsmeglingsloven (EMGL)

Brukes av AI-analysatoren for å gi presise lovhenvisninger
og av regelverkmotoren for å matche avvik mot lovgrunnlag.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Paragraf:
    """En enkelt paragraf fra et regelverk."""
    lov: str              # "PBL", "TEK17", "SAK10", "EMGL"
    kode: str             # "PBL-20-1", "TEK17-12-2"
    tittel: str
    ingress: str          # Kort sammendrag (1-2 setninger)
    fulltext: str         # Relevant utdrag fra lovteksten
    relevans: list[str]   # Hvilke avvikskategorier dette er relevant for
    alvorlighet: str = "MIDDELS"  # "LAV", "MIDDELS", "HØY"


# ---------------------------------------------------------------------------
# Plan og bygningsloven (PBL)
# ---------------------------------------------------------------------------

PBL_PARAGRAFER: list[Paragraf] = [
    Paragraf(
        lov="PBL",
        kode="PBL-20-1",
        tittel="§ 20-1. Tiltak som krever søknad og tillatelse",
        ingress="Bestemmer hvilke bygge- og anleggstiltak som krever søknad og tillatelse fra kommunen.",
        fulltext=(
            "Følgende tiltak krever søknad og tillatelse: "
            "a) oppføring, tilbygging, påbygging, underbygging eller plassering av bygning, konstruksjon eller anlegg, "
            "b) vesentlig endring eller vesentlig reparasjon av tiltak som nevnt i bokstav a, "
            "c) fasadeendring, "
            "d) bruksendring eller vesentlig utvidelse eller vesentlig endring av tidligere drift av tiltak som nevnt i bokstav a, "
            "e) riving av tiltak som nevnt i bokstav a, "
            "f) oppføring, endring eller riving av bygningstekniske installasjoner, "
            "g) oppdeling eller sammenføyning av bruksenheter i boliger samt annen ombygging som medfører fravikelse av bolig, "
            "h) oppføring av innhegning mot veg, "
            "i) plassering av skilt- og reklameinnretninger."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED", "USE_CHANGE_INDICATION", "ROOM_DEFINITION_CHANGE"],
        alvorlighet="HØY",
    ),
    Paragraf(
        lov="PBL",
        kode="PBL-19-2",
        tittel="§ 19-2. Dispensasjonsvedtaket",
        ingress="Regulerer når kommunen kan gi dispensasjon fra plan- og bygningslovgivningen.",
        fulltext=(
            "Dispensasjon kan ikke gis dersom hensynene bak bestemmelsen det dispenseres fra, "
            "eller hensynene i lovens formålsbestemmelse, blir vesentlig tilsidesatt. "
            "I tillegg må fordelene ved å gi dispensasjon være klart større enn ulempene etter en samlet vurdering. "
            "Det kan ikke dispenseres fra saksbehandlingsregler."
        ),
        relevans=["ADDITION_DETECTED", "USE_CHANGE_INDICATION"],
        alvorlighet="HØY",
    ),
    Paragraf(
        lov="PBL",
        kode="PBL-29-4",
        tittel="§ 29-4. Byggverkets plassering, høyde og avstand fra nabogrense",
        ingress="Angir krav til plassering, høyde og avstand til nabogrense for byggverk.",
        fulltext=(
            "Byggverk skal plasseres slik at det ikke oppstår fare for liv og helse. "
            "Kommunen kan i særlige tilfeller godkjenne en annen plassering enn den som følger av kommuneplanens arealdel. "
            "Byggverk kan ikke plasseres nærmere nabogrense enn 4,0 m med mindre annet er bestemt i plan eller det foreligger dispensasjon. "
            "Mønehøyde og gesimshøyde fastsettes i reguleringsplan. "
            "Der høyde ikke er angitt i plan, gjelder: gesimshøyde inntil 8 m og mønehøyde inntil 9 m."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED"],
        alvorlighet="HØY",
    ),
    Paragraf(
        lov="PBL",
        kode="PBL-31-2",
        tittel="§ 31-2. Tiltak på eksisterende byggverk",
        ingress="Gir regler for hva som gjelder ved endringer og reparasjoner på eksisterende byggverk.",
        fulltext=(
            "Kommunen kan gi tillatelse til bruksendring og nødvendige ombygginger av eksisterende byggverk også "
            "når det ikke er mulig å tilpasse byggverket til tekniske krav uten uforholdsmessige kostnader. "
            "Dersom eksisterende byggverk eller deler av det er i strid med loven, kan kommunen pålegge utbedring "
            "av lovstridige forhold. Vesentlige endringer og reparasjoner skal bringes i samsvar med lovgivningen."
        ),
        relevans=["USE_CHANGE_INDICATION", "ROOM_DEFINITION_CHANGE", "BEDROOM_UTILITY_DISCREPANCY"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="PBL",
        kode="PBL-21-10",
        tittel="§ 21-10. Ferdigattest og midlertidig brukstillatelse",
        ingress="Krever ferdigattest for alle tiltak som krever søknad og tillatelse, og angir konsekvenser av manglende ferdigattest.",
        fulltext=(
            "Søknad om ferdigattest skal sendes kommunen når tiltaket er ferdigstilt. "
            "Bygning eller del av bygning skal ikke tas i bruk før kommunen har gitt ferdigattest eller midlertidig brukstillatelse. "
            "Kommunen utsteder ferdigattest på grunnlag av søknad fra ansvarlig søker. "
            "Etter 5 år kan kommunen avslå å utstede ferdigattest, men kan i stedet gi brukstillatelse."
        ),
        relevans=["ADDITION_DETECTED", "UNINSPECTED_AREA"],
        alvorlighet="HØY",
    ),
    Paragraf(
        lov="PBL",
        kode="PBL-32-3",
        tittel="§ 32-3. Pålegg om retting og pålegg om stans",
        ingress="Kommunen kan gi pålegg om retting av ulovlige tiltak, og kan kreve stans i pågående ulovlig arbeid.",
        fulltext=(
            "Kommunen kan gi pålegg om retting av forhold som er i strid med bestemmelser gitt i eller i medhold av loven. "
            "Kommunen kan gi pålegg om riving eller fjerning av ulovlig oppførte byggverk, konstruksjoner, anlegg og innretninger. "
            "Kommunen kan kreve at ulovlig arbeid stanses umiddelbart."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED", "USE_CHANGE_INDICATION"],
        alvorlighet="KRITISK",
    ),
]

# ---------------------------------------------------------------------------
# Byggteknisk forskrift (TEK17)
# ---------------------------------------------------------------------------

TEK17_PARAGRAFER: list[Paragraf] = [
    Paragraf(
        lov="TEK17",
        kode="TEK17-8-1",
        tittel="§ 8-1. Uteareal",
        ingress="Krav til utforming av uteareal og uteoppholdsareal.",
        fulltext=(
            "Uteareal skal utformes slik at de er egnet for det formål de er beregnet for og slik at risikoen "
            "for personskade reduseres til et minimum. Uteareal skal tilpasses omgivelsene og klimaforhold."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED"],
        alvorlighet="LAV",
    ),
    Paragraf(
        lov="TEK17",
        kode="TEK17-8-2",
        tittel="§ 8-2. Krav om tilgjengelig uteareal for boligbygning",
        ingress="Stiller krav til størrelse og tilgjengelighet av uteareal for boligbygninger.",
        fulltext=(
            "Byggverk for publikum og arbeidsbygning skal ha uteareal som er tilgjengelig og kan brukes av personer "
            "med funksjonsnedsettelse. Boligbygning med krav om heis skal ha tilgjengelig uteareal."
        ),
        relevans=["ADDITION_DETECTED"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="TEK17",
        kode="TEK17-12-2",
        tittel="§ 12-2. Krav om tilgjengelig boenhet",
        ingress="Definerer krav til tilgjengelig boenhet, herunder krav til soverom og rom i bolig.",
        fulltext=(
            "Boenhet med krav om tilgjengelighet skal ha: "
            "a) snuareal med diameter på minimum 1,5 m i alle rom, "
            "b) minst ett soverom som er tilgjengelig, med fri gulvplass på minst 1,6 m × 2,0 m ved siden av seng, "
            "c) bad/wc tilgjengelig fra soverom eller korridor. "
            "Rom beregnet for varig opphold (soverom, stue) skal ha vindu mot det fri med dagslysflate minst 10% av gulvflaten."
        ),
        relevans=["BEDROOM_UTILITY_DISCREPANCY", "ROOM_DEFINITION_CHANGE"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="TEK17",
        kode="TEK17-12-7",
        tittel="§ 12-7. Krav til rom og annet oppholdsareal",
        ingress="Angir krav til utforming av rom og oppholdsarealer i boliger og byggverk.",
        fulltext=(
            "Rom og annet oppholdsareal skal ha utforming tilpasset sin funksjon. "
            "Soverom og rom for varig opphold skal ha tilfredsstillende dagslysforhold med vindusglass mot det fri, "
            "fri takhøyde på minst 2,4 m og ventilasjon. "
            "Bad/wc i boenhet skal ha tilfredsstillende ventilasjon."
        ),
        relevans=["ROOM_DEFINITION_CHANGE", "BEDROOM_UTILITY_DISCREPANCY", "WINDOW_PLACEMENT_CHANGE"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="TEK17",
        kode="TEK17-11-9",
        tittel="§ 11-9. Rømning fra byggverk",
        ingress="Stiller krav til rømningsvei og rømningsforhold fra byggverk.",
        fulltext=(
            "Byggverk skal ha sikkert og raskt rømning. "
            "Rømningsvei skal ha tilstrekkelig bredde, høyde og kapasitet til å tjene det antall personer som kan befinne seg i byggverket. "
            "Fra boenhet skal rømning kunne skje via dør til rømningsvei, vindu eller balkong i hver etasje. "
            "Dører i rømningsvei skal slå i rømningsretningen ved mer enn 50 personers belastning."
        ),
        relevans=["DOOR_PLACEMENT_CHANGE", "UNINSPECTED_AREA"],
        alvorlighet="HØY",
    ),
    Paragraf(
        lov="TEK17",
        kode="TEK17-13-5",
        tittel="§ 13-5. Radon",
        ingress="Krav til beskyttelse mot radon i byggverk med rom for varig opphold.",
        fulltext=(
            "Bygninger med rom for varig opphold skal prosjekteres og utføres med radonforebyggende tiltak, "
            "slik at innstrømming av radon fra grunnen begrenses. "
            "Årsmiddelkonsentrasjonen av radon i inneluft skal være lavere enn 200 Bq/m3."
        ),
        relevans=["UNDERBUILDING_DETECTED", "USE_CHANGE_INDICATION"],
        alvorlighet="HØY",
    ),
]

# ---------------------------------------------------------------------------
# Byggesaksforskriften (SAK10)
# ---------------------------------------------------------------------------

SAK10_PARAGRAFER: list[Paragraf] = [
    Paragraf(
        lov="SAK10",
        kode="SAK10-4-1",
        tittel="§ 4-1. Tiltak som er unntatt fra søknadsplikt",
        ingress="Lister opp byggetiltak som ikke krever søknad og tillatelse fra kommunen.",
        fulltext=(
            "Følgende tiltak er unntatt fra søknadsplikt etter pbl. § 20-5: "
            "a) mindre tiltak på bebygd eiendom: frittliggende bygning med ett rom og lukket bod "
            "under 15 m² bebygd areal (BYA), frittliggende bygning på bebygd eiendom inntil 50 m² BYA "
            "(kun med én etasje og med høyde inntil 4 m), tilbygg på bebygd eiendom med samlet BYA "
            "eller BRA inntil 15 m². "
            "Tiltaket må ikke plasseres over ledninger i grunnen, ikke plasseres nærmere nabogrense "
            "enn 1,0 m og ikke brukes til beboelse."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="SAK10",
        kode="SAK10-6-2",
        tittel="§ 6-2. Ansvarlig søkers ansvar og oppgaver",
        ingress="Definerer ansvarlig søkers ansvar ved søknad om byggetillatelse.",
        fulltext=(
            "Ansvarlig søker skal: "
            "a) samordne søknaden og forestå kommunikasjon med kommunen, "
            "b) kontrollere at tiltaket ikke er i strid med tillatelser, bestemmelser i plan eller annet regelverk, "
            "c) opplyse i søknaden om tiltaket er i strid med plan, "
            "d) påse at det foreligger ansvarsrett for alle ansvarlige foretak, "
            "e) sende inn dokumentasjon for ferdigattest."
        ),
        relevans=["ADDITION_DETECTED", "USE_CHANGE_INDICATION", "ROOM_DEFINITION_CHANGE"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="SAK10",
        kode="SAK10-8-1",
        tittel="§ 8-1. Ansvarlig prosjekterendes ansvar og oppgaver",
        ingress="Definerer ansvarlig prosjekterendes (arkitektens) ansvar.",
        fulltext=(
            "Ansvarlig prosjekterende skal: "
            "a) forestå prosjektering innenfor sitt ansvarsområde slik at resultatet er i samsvar med krav i plan- og bygningsloven, "
            "b) stå for kontroll av prosjekteringen som del av foretakets kvalitetssikringssystem, "
            "c) erklære overfor ansvarlig søker at prosjekteringen er kontrollert i samsvar med krav i plan- og bygningsloven."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED", "UNINSPECTED_AREA"],
        alvorlighet="MIDDELS",
    ),
]

# ---------------------------------------------------------------------------
# Eiendomsmeglingsloven (EMGL)
# ---------------------------------------------------------------------------

EMGL_PARAGRAFER: list[Paragraf] = [
    Paragraf(
        lov="EMGL",
        kode="EMGL-6-7",
        tittel="§ 6-7. Opplysningsplikt overfor kjøper",
        ingress="Eiendomsmegler plikter å gi kjøper opplysninger om alt som har vesentlig betydning for handelen.",
        fulltext=(
            "Oppdragstaker skal sørge for at kjøperen før handel sluttes får opplysninger om: "
            "a) eiendommens registerbetegnelse og adresse, "
            "b) tinglyste forpliktelser, "
            "c) tilliggende rettigheter, "
            "d) grunnarealer, "
            "e) bebyggelsens arealer og angivelse av alder og byggemåte, "
            "f) reguleringsforhold, herunder om arealet der eiendommen ligger har vern eller båndlegginger, "
            "g) ferdigattest eller midlertidig brukstillatelse for bebyggelsen, "
            "h) om det foreligger pålegg fra offentlige myndigheter."
        ),
        relevans=["MARKETED_FUNCTION_DISCREPANCY", "BEDROOM_UTILITY_DISCREPANCY", "UNINSPECTED_AREA"],
        alvorlighet="HØY",
    ),
]

# ---------------------------------------------------------------------------
# Byggforsk-basert veiledning (fra Konsepthus AS – 1-Veilederere-byggforsk-tegninger)
# Kilde: SINTEF Byggforsk blader og veiledere
# ---------------------------------------------------------------------------

BYGGFORSK_VEILEDERE: list[Paragraf] = [
    Paragraf(
        lov="BYGGFORSK",
        kode="BF-GARASJE",
        tittel="Carport og garasjer – Byggforsk-veileder",
        ingress=(
            "Garasjer og carporter på inntil 50 m² BYA kan i mange tilfeller bygges uten søknad "
            "dersom de plasseres mer enn 1 m fra nabogrense og ikke plasseres over ledninger i grunnen."
        ),
        fulltext=(
            "Frittliggende garasje/uthus på inntil 15 m² kan oppføres uten søknad og ansvarsrett (PBL §20-5). "
            "Frittliggende garasje/uthus på 15–50 m² BYA kan bygges uten søknad dersom: "
            "avstand til nabogrense er minst 1 m, gesimshøyde er inntil 3 m og mønehøyde inntil 4 m, "
            "bygget ikke brukes til beboelse og ikke inneholder rom for varig opphold. "
            "Garasjer over 50 m² BYA krever søknad og tillatelse. "
            "Carport regnes som garasje i reguleringssammenheng. "
            "Merk: kommuneplanen og reguleringsplanen kan stille strengere krav."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED"],
        alvorlighet="LAV",
    ),
    Paragraf(
        lov="BYGGFORSK",
        kode="BF-BRUKSENDRING",
        tittel="Bruksendring av bolig – Byggforsk-veileder",
        ingress=(
            "Veileder om krav og prosess ved bruksendring av kjeller, loft og garasje til oppholdsrom eller boenhet."
        ),
        fulltext=(
            "Bruksendring krever søknad og tillatelse etter PBL §20-1 d. "
            "For at rom skal godkjennes som varig oppholdsrom (soverom, stue, kjøkken) krever TEK17: "
            "takhøyde min. 2,4 m, tilstrekkelig dagslysareal (minst 10% av gulvarealet), "
            "tilfredsstillende luftkvalitet og ventilasjon (0,7 l/s per m²), "
            "lydkrav mellom boenheter (R'w ≥ 55 dB for luftlyd, L'nw ≤ 53 dB for trinnlyd), "
            "brannsikkerhet: røykvarslere, rømningsvei via vindu (min. 0,5 m² åpningsareal), "
            "fukt: rom under terreng krever spesiell fuktbeskyttelse og drenering. "
            "Kjellerboenhet krever separat inngang for å regnes som selvstendig boenhet."
        ),
        relevans=["USE_CHANGE_INDICATION", "BEDROOM_UTILITY_DISCREPANCY", "ROOM_DEFINITION_CHANGE"],
        alvorlighet="HØY",
    ),
    Paragraf(
        lov="BYGGFORSK",
        kode="BF-FASADEENDRING",
        tittel="Fasadeendring – søknadsplikt og unntak",
        ingress=(
            "Fasadeendringer som endrer bygningens utseende vesentlig krever søknad. "
            "Enkle vedlikeholdsarbeider som bytting av kledning i samme farge og material er i utgangspunktet søknadsfritt."
        ),
        fulltext=(
            "Fasadeendring krever søknad etter PBL §20-1 c dersom: "
            "endringen er vesentlig (f.eks. endring av vindusplassering, gesims, takkonstruksjon), "
            "bygget er reguleringsplanregulert med materialbruk eller farge-krav, "
            "bygget er vernet (automatisk fredet eller SEFRAK-registrert). "
            "Ikke søknadspliktig: maling i samme farge, bytting av vinduer i samme størrelser, "
            "vedlikehold av eksisterende kledning i tilsvarende material. "
            "Huskeliste ved fasadeendring: sjekk reguleringsplanens bestemmelser om fasademateriale, "
            "sjekk om eiendommen er i SEFRAK-register, kontakt kulturminneavdelingen ved tvil."
        ),
        relevans=["ADDITION_DETECTED"],
        alvorlighet="LAV",
    ),
    Paragraf(
        lov="BYGGFORSK",
        kode="BF-GRAD-UTNYTTING",
        tittel="Grad av utnytting – BYA og BRA",
        ingress=(
            "Grad av utnytting angir hvor mye av en tomt som kan bebygges. "
            "BYA (bebygd areal) og BRA (bruksareal) beregnes etter NS 3940 og veiledning fra Kommunal- og distriktsdepartementet."
        ),
        fulltext=(
            "BYA (bebygd areal): horisontalprojeksjon av bygningens yttervegger og overbygde arealer. "
            "Inkluderer: garasje, uthus, carport, hagestue og andre bygninger på tomten. "
            "Utelukt fra BYA: takutstikk inntil 1 m, åpen veranda/terrasse uten overbygg, trappe og ramper. "
            "BRA (bruksareal): areal innenfor omsluttende vegger i alle etasjer. "
            "Typiske utnyttingsgrader i reguleringsplaner: %-BYA 30% = 30% av tomten kan bebygges. "
            "TU (tomteutnytting, eldre begrep): beregnes som BRA / tomteareal × 100. "
            "Beregn alltid nøyaktig BYA/BRA-oppsummering i byggesøknaden. "
            "Kjeller under terreng regnes vanligvis ikke i BYA, men kan telle i BRA."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="BYGGFORSK",
        kode="BF-SOKNADSFRITT",
        tittel="Tiltak som er fritatt fra søknadsplikt (SAK10 §3-1, §4-1)",
        ingress=(
            "Visse mindre tiltak kan utføres uten søknad til kommunen, men eier har fortsatt ansvar "
            "for at tiltaket er i samsvar med plan og tekniske krav."
        ),
        fulltext=(
            "Fritatt søknadsplikt etter SAK10 §4-1 (med krav til avstand, høyde og plassering): "
            "1. Frittliggende bygning inntil 15 m² – min. 1 m fra nabogrense, ikke beboelse. "
            "2. Frittliggende bygning 15–50 m² – min. 1 m fra nabogrense, maks gesims 3 m, møne 4 m. "
            "3. Tilbygg inntil 15 m² – min. 4 m fra nabogrense. "
            "4. Levegg inntil 10 m lengde og 1,8 m høyde. "
            "5. Støttemur inntil 1,0 m høyde eller terrengendring inntil 3,0 m fra nabogrense. "
            "6. Innhegning mot vei – inntil 1,5 m. "
            "Viktig: kommuneplanen og reguleringsplanen kan inneholde bestemmelser som begrenser "
            "eller forbyr tiltak som ellers er fritatt søknadsplikt. "
            "Alltid sjekk om eiendommen ligger i et område med særskilte restriksjoner (LNF, vernezone, etc.)."
        ),
        relevans=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED"],
        alvorlighet="LAV",
    ),
    Paragraf(
        lov="BYGGFORSK",
        kode="BF-NABOVARSEL",
        tittel="Nabovarsel – krav og prosess (SAK10 §6-2, §6-3)",
        ingress=(
            "Søker plikter å varsle naboer og gjenboere ved søknadspliktige tiltak. "
            "Naboene har rett til å fremsette merknader innen 2 uker."
        ),
        fulltext=(
            "Nabovarsel skal sendes til alle berørte naboer og gjenboere. "
            "Varselet skal inneholde: "
            "– kopi av søknaden med vedlegg (situasjonsplan, tegninger) "
            "– opplysninger om tiltaket og berørte naboer "
            "– informasjon om rett til å fremsette merknader innen 14 dager. "
            "Nabovarsel kan sendes: personlig overlevering (kvittering), rekommandert brev, eller digitalt. "
            "Dersom naboen har merknader, skal disse vedlegges søknaden til kommunen. "
            "Søker skal kommentere merknadene. "
            "Kommunen avgjør om det skal innhentes ytterligere opplysninger. "
            "Nabovarsel er ikke nødvendig for tiltak etter SAK10 §4-1 (fritatt søknadsplikt)."
        ),
        relevans=["ADDITION_DETECTED"],
        alvorlighet="MIDDELS",
    ),
    Paragraf(
        lov="BYGGFORSK",
        kode="BF-FERDIGATTEST",
        tittel="Ferdigattest – krav og konsekvenser av manglende attest",
        ingress=(
            "Alle søknadspliktige tiltak skal avsluttes med ferdigattest. "
            "Manglende ferdigattest er en lovstridig tilstand og kan påvirke salgsverdi og forsikring."
        ),
        fulltext=(
            "PBL §21-10 krever at søknad om ferdigattest sendes kommunen når tiltaket er ferdigstilt. "
            "Ansvarlig søker er ansvarlig for å sende inn søknad om ferdigattest. "
            "Ferdigattest er bevis på at bygget er godkjent og kan tas i bruk permanent. "
            "Manglende ferdigattest: "
            "– Bygget anses rettslig sett ikke som ferdigstilt. "
            "– Kan ha negativ innvirkning ved salg (kjøper kan ha krav mot selger, jf. avhendingsloven). "
            "– Kan påvirke forsikringsdekning ved skade. "
            "– Kommunen kan i prinsippet pålegge retting eller riving (PBL §32-3). "
            "Fra 1. januar 2016: kommunen kan avslå ferdigattest for gamle byggesaker (>5 år) og "
            "utstede brukstillatelse i stedet. Dette er ikke det samme som ferdigattest. "
            "Anbefaling: løs manglende ferdigattest så tidlig som mulig ved kjøp/salg av eiendom."
        ),
        relevans=["UNINSPECTED_AREA", "ADDITION_DETECTED"],
        alvorlighet="HØY",
    ),
]

# ---------------------------------------------------------------------------
# Samlet register og søkefunksjoner
# ---------------------------------------------------------------------------

ALLE_PARAGRAFER: list[Paragraf] = (
    PBL_PARAGRAFER + TEK17_PARAGRAFER + SAK10_PARAGRAFER + EMGL_PARAGRAFER + BYGGFORSK_VEILEDERE
)

_KODE_INDEX: dict[str, Paragraf] = {p.kode: p for p in ALLE_PARAGRAFER}
_RELEVANS_INDEX: dict[str, list[Paragraf]] = {}
for _p in ALLE_PARAGRAFER:
    for _rel in _p.relevans:
        _RELEVANS_INDEX.setdefault(_rel, []).append(_p)


def hent_paragraf(kode: str) -> Paragraf | None:
    """Hent en spesifikk paragraf etter kode (f.eks. 'PBL-20-1')."""
    return _KODE_INDEX.get(kode)


def finn_relevante_paragrafer(avvikskategori: str) -> list[Paragraf]:
    """Finn alle paragrafer relevante for en avvikskategori."""
    return _RELEVANS_INDEX.get(avvikskategori, [])


def bygg_regelverk_kontekst(avvikskategorier: list[str] | None = None) -> str:
    """
    Bygger en kompakt norsk regelverktekst for bruk i AI-prompt.

    Hvis avvikskategorier er oppgitt, filtreres til relevante paragrafer.
    Ellers inkluderes et utvalg av de viktigste.
    """
    if avvikskategorier:
        paragrafer: list[Paragraf] = []
        seen: set[str] = set()
        for kat in avvikskategorier:
            for p in finn_relevante_paragrafer(kat):
                if p.kode not in seen:
                    paragrafer.append(p)
                    seen.add(p.kode)
    else:
        # Standard utvalg for generell analyse
        prioriterte = [
            "PBL-20-1", "PBL-19-2", "PBL-29-4", "PBL-31-2", "PBL-21-10",
            "TEK17-12-2", "TEK17-12-7", "TEK17-11-9", "SAK10-4-1", "EMGL-6-7",
        ]
        paragrafer = [p for kode in prioriterte if (p := _KODE_INDEX.get(kode))]

    lines = ["## Relevant norsk regelverk\n"]
    for p in paragrafer:
        lines.append(f"**{p.tittel}** ({p.lov})")
        lines.append(f"_{p.ingress}_")
        lines.append(f'"{p.fulltext}"')
        lines.append("")

    return "\n".join(lines)
