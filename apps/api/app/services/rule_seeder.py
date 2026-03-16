"""Seed rules table on first startup if empty."""
from __future__ import annotations
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SEED_RULES = [
    {
        "rule_code": "TEK17-12-2",
        "title": "Krav til rom for varig opphold – areal og takhøyde",
        "description": "Rom for varig opphold skal ha fri høyde på minst 2,4 m og et areal tilpasset sin funksjon. Soverom minimum 7 m², stue minimum 15 m².",
        "legal_reference": "TEK17 § 12-2",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": ["ROOM_DEFINITION_CHANGE", "BEDROOM_UTILITY_DISCREPANCY", "UNDERBUILDING_DETECTED"],
        "parameters": {"min_ceiling_height_m": 2.4, "min_bedroom_area_m2": 7.0, "min_living_area_m2": 15.0},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-6",
        "title": "Krav til vindu og ventilasjon",
        "description": "Rom for varig opphold skal ha vindusareal tilsvarende minst 10 % av gulvarealet. Naturlig ventilasjon skal være mulig.",
        "legal_reference": "TEK17 § 12-6",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": ["WINDOW_PLACEMENT_CHANGE", "ROOM_DEFINITION_CHANGE"],
        "parameters": {"min_window_ratio": 0.10},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-7",
        "title": "Krav til dør og adkomst",
        "description": "Dører til og i boenhet skal ha tilstrekkelig fri bredde for rullestol (minst 0,86 m fri åpning).",
        "legal_reference": "TEK17 § 12-7",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": ["DOOR_PLACEMENT_CHANGE", "ROOM_DEFINITION_CHANGE"],
        "parameters": {"min_door_width_m": 0.86},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-15",
        "title": "Krav til balkong og terrasse",
        "description": "Balkong og terrasse tilknyttet boenhet skal ha rekkverk og utformes med hensyn til sikkerhet og brukbarhet.",
        "legal_reference": "TEK17 § 12-15",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": ["BALCONY_TERRACE_DISCREPANCY"],
        "parameters": {"min_railing_height_m": 1.0},
        "is_active": True,
    },
    {
        "rule_code": "PBL-20-1",
        "title": "Tiltak som krever søknad og tillatelse",
        "description": "Oppføring, tilbygg, påbygg, underbygging eller plassering av bygning er søknadspliktige tiltak etter plan- og bygningsloven.",
        "legal_reference": "PBL § 20-1",
        "source": "PBL",
        "version": "2008",
        "applies_to_categories": ["ADDITION_DETECTED", "UNDERBUILDING_DETECTED", "USE_CHANGE_INDICATION"],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "PBL-31-2",
        "title": "Tiltak på eksisterende bebyggelse",
        "description": "Tiltak på eller i eksisterende byggverk skal oppfylle krav i plan- og bygningsloven. Vesentlig endring av bruk er søknadspliktig.",
        "legal_reference": "PBL § 31-2",
        "source": "PBL",
        "version": "2008",
        "applies_to_categories": ["USE_CHANGE_INDICATION", "ROOM_DEFINITION_CHANGE", "MARKETED_FUNCTION_DISCREPANCY"],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "SAK10-4-1",
        "title": "Unntak fra søknadsplikt – mindre tiltak",
        "description": "Mindre tiltak på bebygd eiendom er unntatt søknadsplikt, men må fortsatt oppfylle tekniske krav og arealplankrav.",
        "legal_reference": "SAK10 § 4-1",
        "source": "SAK10",
        "version": "2010",
        "applies_to_categories": ["ADDITION_DETECTED", "DOOR_PLACEMENT_CHANGE", "WINDOW_PLACEMENT_CHANGE"],
        "parameters": {"max_area_exempt_m2": 15.0},
        "is_active": True,
    },
    {
        "rule_code": "SAK10-6-4",
        "title": "Dokumentasjon av avvik fra godkjente tegninger",
        "description": "Dersom utført arbeid avviker fra godkjente tegninger, skal dette dokumenteres og meldes til kommunen.",
        "legal_reference": "SAK10 § 6-4",
        "source": "SAK10",
        "version": "2010",
        "applies_to_categories": [
            "ROOM_DEFINITION_CHANGE", "BEDROOM_UTILITY_DISCREPANCY",
            "DOOR_PLACEMENT_CHANGE", "WINDOW_PLACEMENT_CHANGE",
            "BALCONY_TERRACE_DISCREPANCY", "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED", "USE_CHANGE_INDICATION",
        ],
        "parameters": {},
        "is_active": True,
    },
    {
        "rule_code": "TEK17-12-9",
        "title": "Bod og oppbevaringsplass",
        "description": "Boenhet skal ha tilstrekkelig lagringsplass. Bod på minimum 5 m² for boliger over 50 m².",
        "legal_reference": "TEK17 § 12-9",
        "source": "TEK17",
        "version": "2017",
        "applies_to_categories": ["UNDERBUILDING_DETECTED", "ROOM_DEFINITION_CHANGE"],
        "parameters": {"min_storage_area_m2": 5.0},
        "is_active": True,
    },
    {
        "rule_code": "EIENDOMSMEGLING-6-7",
        "title": "Markedsføring av boligers funksjon",
        "description": "Boliger skal markedsføres i samsvar med faktisk godkjent bruk. Markedsføring av rom som soverom krever at rommet oppfyller krav til soverom.",
        "legal_reference": "Eiendomsmeglingsloven § 6-7",
        "source": "EIENDOMSMEGLINGSLOVEN",
        "version": "2007",
        "applies_to_categories": ["MARKETED_FUNCTION_DISCREPANCY", "BEDROOM_UTILITY_DISCREPANCY"],
        "parameters": {},
        "is_active": True,
    },
]


async def seed_rules_if_empty(db: AsyncSession) -> int:
    """Seed rules table if empty. Returns number of rules inserted."""
    from app.models.property_case import Rule
    import uuid

    count_result = await db.execute(select(func.count()).select_from(Rule))
    count = count_result.scalar()
    if count and count > 0:
        logger.info("Rules table already has %d rules – skipping seed.", count)
        return 0

    inserted = 0
    for rule_data in SEED_RULES:
        rule = Rule(
            id=str(uuid.uuid4()),
            rule_code=rule_data["rule_code"],
            title=rule_data["title"],
            description=rule_data["description"],
            legal_reference=rule_data["legal_reference"],
            source=rule_data["source"],
            version=rule_data["version"],
            applies_to_categories=rule_data["applies_to_categories"],
            parameters=rule_data["parameters"],
            is_active=rule_data["is_active"],
        )
        db.add(rule)
        inserted += 1

    await db.commit()
    logger.info("Seeded %d rules.", inserted)
    return inserted
