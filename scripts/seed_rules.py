"""
ByggSjekk – Seed regelbase

Skriptet legger inn et sett med realistiske norske byggeforskrifter i databasen.
Kildene er:
  - TEK17  : Teknisk forskrift til plan- og bygningsloven (2017)
  - PBL    : Plan- og bygningsloven (2008)
  - SAK10  : Byggesaksforskriften (2010)
  - EMGL   : Eiendomsmeglingsloven (2007)

Kjøring:
    python scripts/seed_rules.py

Forutsetninger:
  - Miljøvariabel DATABASE_URL er satt (leses fra .env via python-dotenv)
  - Alembic-migrasjoner er kjørt (make migrate)
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Last inn .env fra prosjektrot
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    print("python-dotenv ikke installert – forventer at DATABASE_URL er satt i miljøet.")

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Regeldata – kolonnenavn matcher ORM-modellen (Rule i property_case.py)
# rule_code, title, description, legal_reference, source, version,
# applies_to_categories, parameters, is_active
# ---------------------------------------------------------------------------

RULES = [
    # -------------------------------------------------------------------------
    # TEK17 – Teknisk forskrift
    # -------------------------------------------------------------------------
    {
        "rule_code": "TEK17-12-2",
        "title": "Krav til rom for varig opphold",
        "description": (
            "Rom for varig opphold skal ha vindu mot det fri med tilfredsstillende lysflate "
            "og mulighet for naturlig ventilasjon. Minimumsareal for rom for varig opphold er 7 m². "
            "Romhøyde skal minst være 2,4 m for rom for varig opphold."
        ),
        "legal_reference": "TEK17 § 12-2",
        "source": "TEK17",
        "version": "2017-06-19",
        "applies_to_categories": [
            "ROOM_DEFINITION_CHANGE",
            "BEDROOM_UTILITY_DISCREPANCY",
            "USE_CHANGE_INDICATION",
        ],
        "parameters": {"min_area_m2": 7.0, "min_ceiling_height_m": 2.4},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-6",
        "title": "Krav til vindu og naturlig ventilasjon",
        "description": (
            "Rom for varig opphold skal ha vindu med lysflate på minst 10 % av gulvflaten. "
            "Vindu skal kunne åpnes for naturlig ventilasjon. Soverom skal ha åpningsbart vindu "
            "med tilstrekkelig størrelse for rømningsvei der dette ikke ivaretas av annen utgang."
        ),
        "legal_reference": "TEK17 § 12-6",
        "source": "TEK17",
        "version": "2017-06-19",
        "applies_to_categories": [
            "WINDOW_PLACEMENT_CHANGE",
            "ROOM_DEFINITION_CHANGE",
            "MARKETED_FUNCTION_DISCREPANCY",
        ],
        "parameters": {"min_window_ratio": 0.10},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-7",
        "title": "Krav til dør og adkomst",
        "description": (
            "Dører til og i boenhet skal ha tilstrekkelig fri bredde for rullestol "
            "(minst 0,86 m fri åpning). Dørplassering påvirker adkomst, rømningsvei "
            "og branncelleinndeling."
        ),
        "legal_reference": "TEK17 § 12-7",
        "source": "TEK17",
        "version": "2017-06-19",
        "applies_to_categories": [
            "DOOR_PLACEMENT_CHANGE",
            "ROOM_DEFINITION_CHANGE",
        ],
        "parameters": {"min_door_clear_width_m": 0.86},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-9",
        "title": "Krav til uteplass og balkong",
        "description": (
            "Boenhet i blokk og lignende skal ha tilgang til privat uteplass (balkong, terrasse eller "
            "takterrasse) på minst 5 m² med tilfredsstillende solforhold. Rekkverk skal minst være 1,0 m."
        ),
        "legal_reference": "TEK17 § 12-9",
        "source": "TEK17",
        "version": "2017-06-19",
        "applies_to_categories": [
            "BALCONY_TERRACE_DISCREPANCY",
            "ADDITION_DETECTED",
        ],
        "parameters": {"min_outdoor_area_m2": 5.0, "min_railing_height_m": 1.0},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-15",
        "title": "Krav til heis",
        "description": (
            "Byggverk der boenheter, arbeidsplasser eller publikumsrettet virksomhet er lokalisert "
            "mer enn to etasjer over eller én etasje under inngangsplanet, skal ha heis."
        ),
        "legal_reference": "TEK17 § 12-15",
        "source": "TEK17",
        "version": "2017-06-19",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "USE_CHANGE_INDICATION",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-11-9",
        "title": "Brannceller og brannmotstand",
        "description": (
            "Bygning skal inndeles i brannceller slik at brann og røyk ikke "
            "sprer seg uakseptabelt raskt. Vesentlig endring av rominndeling "
            "kan endre branncellestrukturen."
        ),
        "legal_reference": "TEK17 § 11-9",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": [
            "DOOR_PLACEMENT_CHANGE",
            "UNINSPECTED_AREA",
            "ROOM_DEFINITION_CHANGE",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-11-14",
        "title": "Rømningsvei fra branncelle",
        "description": (
            "Fra branncelle skal det finnes minst én rømningsvei til sikkert sted. "
            "Dørplassering og romkonfigurasjon påvirker rømningsveiens egnethet."
        ),
        "legal_reference": "TEK17 § 11-14",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": [
            "DOOR_PLACEMENT_CHANGE",
            "WINDOW_PLACEMENT_CHANGE",
            "UNINSPECTED_AREA",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-8-1",
        "title": "Arealkrav til rom og rommets høyde",
        "description": (
            "Rom for varig opphold skal ha et areal på minst 6 m² og takhøyde "
            "på minst 2,4 m. Romhøyden måles som fri høyde."
        ),
        "legal_reference": "TEK17 § 8-1",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
            "ROOM_DEFINITION_CHANGE",
        ],
        "parameters": {"min_area_m2": 6.0, "min_ceiling_height_m": 2.4},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-8-3",
        "title": "Etasjehøyde og loftsetasje",
        "description": (
            "Beboelig loft eller underetasje skal oppfylle krav til "
            "takhøyde og areal for rom for varig opphold."
        ),
        "legal_reference": "TEK17 § 8-3",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
            "UNINSPECTED_AREA",
        ],
        "parameters": {"min_habitable_loft_area_m2": 15.0},
        "is_active": True,
    },
    # -------------------------------------------------------------------------
    # PBL – Plan- og bygningsloven
    # -------------------------------------------------------------------------
    {
        "rule_code": "PBL-20-1",
        "title": "Tiltak som krever søknad og tillatelse",
        "description": (
            "Følgende tiltak krever søknad og tillatelse: oppføring, tilbygging, påbygging, "
            "underbygging eller plassering av bygning; vesentlig endring; fasadeendring; "
            "bruksendring eller vesentlig utvidelse. Riving av tiltak er også søknadspliktig."
        ),
        "legal_reference": "PBL § 20-1",
        "source": "PBL",
        "version": "2008-06-27",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
            "USE_CHANGE_INDICATION",
            "ROOM_DEFINITION_CHANGE",
            "BALCONY_TERRACE_DISCREPANCY",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "PBL-20-3",
        "title": "Tiltak som krever ansvarlig foretak",
        "description": (
            "Søknadspliktige tiltak etter § 20-1 første ledd bokstav a til j krever bruk av ansvarlige "
            "foretak, unntatt der tiltakshaver selv kan stå ansvarlig etter § 20-2."
        ),
        "legal_reference": "PBL § 20-3",
        "source": "PBL",
        "version": "2008-06-27",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "PBL-29-4",
        "title": "Byggverkets høyde og avstand fra nabogrense",
        "description": (
            "Bygning kan ikke plasseres nærmere nabogrense enn 4 m, med mindre "
            "kommunen eller naboer samtykker. Gjelder tilbygg og påbygg."
        ),
        "legal_reference": "PBL § 29-4",
        "source": "PBL",
        "version": "2008",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "UNINSPECTED_AREA",
        ],
        "parameters": {"min_setback_m": 4.0},
        "is_active": True,
    },
    {
        "rule_code": "PBL-29-3",
        "title": "Estetikk og tilpasning til omgivelsene",
        "description": (
            "Tiltak etter loven skal ha en god utforming og være tilpasset "
            "eksisterende bebyggelse og omgivelsene."
        ),
        "legal_reference": "PBL § 29-3",
        "source": "PBL",
        "version": "2008",
        "applies_to_categories": [
            "USE_CHANGE_INDICATION",
            "BALCONY_TERRACE_DISCREPANCY",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "PBL-31-2",
        "title": "Tiltak på eksisterende byggverk – bruksendring",
        "description": (
            "Kommunen kan gi tillatelse til bruksendring og nødvendig ombygging av "
            "eksisterende byggverk. Vesentlig bruksendring er søknadspliktig. "
            "Viktig ved eldre bygningsmasse med bruksendringer over tid."
        ),
        "legal_reference": "PBL § 31-2",
        "source": "PBL",
        "version": "2008-06-27",
        "applies_to_categories": [
            "USE_CHANGE_INDICATION",
            "MARKETED_FUNCTION_DISCREPANCY",
            "BEDROOM_UTILITY_DISCREPANCY",
        ],
        "parameters": {},
        "is_active": True,
    },
    # -------------------------------------------------------------------------
    # SAK10 – Byggesaksforskriften
    # -------------------------------------------------------------------------
    {
        "rule_code": "SAK10-4-1",
        "title": "Tiltak som er unntatt fra søknadsplikt",
        "description": (
            "Følgende tiltak er unntatt fra krav om søknad og tillatelse: frittliggende bygning "
            "der bygningen ikke er større enn 15 m² BRA og ikke er beregnet for varig opphold; "
            "mindre tiltak i eksisterende byggverk; fasadeendringer som ikke endrer karakter. "
            "Slike tiltak må likevel overholde TEK17."
        ),
        "legal_reference": "SAK10 § 4-1",
        "source": "SAK10",
        "version": "2010-03-26",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "UNINSPECTED_AREA",
            "DOOR_PLACEMENT_CHANGE",
            "WINDOW_PLACEMENT_CHANGE",
        ],
        "parameters": {"max_exempt_area_m2": 15.0},
        "is_active": True,
    },
    {
        "rule_code": "SAK10-4-2",
        "title": "Tiltak som kan forestås av tiltakshaver",
        "description": (
            "Oppføring, tilbygging, påbygging og underbygging av garasje, uthus og tilbygg "
            "til bolig på inntil 50 m² BRA på bebygd eiendom kan forestås av tiltakshaver. "
            "Selv selvbyggertiltak må dokumenteres."
        ),
        "legal_reference": "SAK10 § 4-2",
        "source": "SAK10",
        "version": "2010-03-26",
        "applies_to_categories": [
            "ADDITION_DETECTED",
        ],
        "parameters": {"max_self_build_area_m2": 50.0},
        "is_active": True,
    },
    {
        "rule_code": "SAK10-6-2",
        "title": "Dokumentasjon av endringer fra godkjent søknad",
        "description": (
            "Endringer fra godkjent plan skal dokumenteres og i visse tilfeller "
            "søkes om på nytt (vesentlig avvik). Dette gjelder alle typer avvik."
        ),
        "legal_reference": "SAK10 § 6-2",
        "source": "SAK10",
        "version": "2010",
        "applies_to_categories": [
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
            "ROOM_DEFINITION_CHANGE",
            "USE_CHANGE_INDICATION",
            "UNINSPECTED_AREA",
            "BEDROOM_UTILITY_DISCREPANCY",
            "DOOR_PLACEMENT_CHANGE",
            "WINDOW_PLACEMENT_CHANGE",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "SAK10-6-4",
        "title": "Krav til ferdigattest",
        "description": (
            "Tiltakshaver skal søke om ferdigattest når tiltaket er ferdig utført. "
            "Ferdigattest utstedes av kommunen når det er dokumentert at tiltaket er "
            "utført i samsvar med tillatelsen. Manglende ferdigattest er et eget avvik."
        ),
        "legal_reference": "SAK10 § 6-4",
        "source": "SAK10",
        "version": "2010-03-26",
        "applies_to_categories": [
            "UNINSPECTED_AREA",
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
        ],
        "parameters": {},
        "is_active": True,
    },
    # -------------------------------------------------------------------------
    # Eiendomsmeglingsloven
    # -------------------------------------------------------------------------
    {
        "rule_code": "EMGL-6-7",
        "title": "Markedsføring av boligers funksjon",
        "description": (
            "Boliger skal markedsføres i samsvar med faktisk godkjent bruk. "
            "Markedsføring av rom som soverom krever at rommet oppfyller TEK17-kravene "
            "til soverom (areal, dagslys, takhøyde, ventilasjon). "
            "Villedende markedsføring kan medføre reklamasjonsansvar."
        ),
        "legal_reference": "Eiendomsmeglingsloven § 6-7",
        "source": "EIENDOMSMEGLINGSLOVEN",
        "version": "2007",
        "applies_to_categories": [
            "MARKETED_FUNCTION_DISCREPANCY",
            "BEDROOM_UTILITY_DISCREPANCY",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "EMGL-7-1",
        "title": "Opplysningsplikt ved eiendomssalg",
        "description": (
            "Selger og megler har plikt til å opplyse om kjente mangler, avvik fra "
            "godkjente tegninger og ulovlige bygningstiltak. Avvik fra godkjent plan "
            "er opplysningspliktige forhold."
        ),
        "legal_reference": "Eiendomsmeglingsloven § 7-1 jf. avhendingsloven § 3-7",
        "source": "EIENDOMSMEGLINGSLOVEN",
        "version": "2007",
        "applies_to_categories": [
            "MARKETED_FUNCTION_DISCREPANCY",
            "USE_CHANGE_INDICATION",
            "ADDITION_DETECTED",
            "UNINSPECTED_AREA",
        ],
        "parameters": {},
        "is_active": True,
    },
    # -------------------------------------------------------------------------
    # Avhendingsloven
    # -------------------------------------------------------------------------
    {
        "rule_code": "AVHL-3-9",
        "title": "Vesentlig avvik fra forventet tilstand",
        "description": (
            "Eiendom har mangel dersom den er i vesentlig dårligere stand enn kjøper "
            "hadde grunn til å forvente ut fra kjøpesummen og forholdene ellers. "
            "Avvik fra godkjente tegninger kan utgjøre en slik mangel."
        ),
        "legal_reference": "Avhendingsloven § 3-9",
        "source": "AVHENDINGSLOVEN",
        "version": "1992",
        "applies_to_categories": [
            "MARKETED_FUNCTION_DISCREPANCY",
            "BEDROOM_UTILITY_DISCREPANCY",
            "ROOM_DEFINITION_CHANGE",
        ],
        "parameters": {},
        "is_active": True,
    },
]


async def seed_rules() -> None:
    """Sett inn regler i databasen. Hopper over eksisterende (basert på rule_code)."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))
    from app.models.property_case import Rule
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        async with session.begin():
            for rule_data in RULES:
                # Check if rule already exists by rule_code
                result = await session.execute(
                    select(Rule).where(Rule.rule_code == rule_data["rule_code"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing rule
                    for field, value in rule_data.items():
                        setattr(existing, field, value)
                else:
                    # Insert new rule
                    rule = Rule(
                        id=uuid.uuid4(),
                        **rule_data,
                    )
                    session.add(rule)

    print(f"Seeding fullfort: {len(RULES)} regler lagt inn / oppdatert.")


if __name__ == "__main__":
    asyncio.run(seed_rules())
