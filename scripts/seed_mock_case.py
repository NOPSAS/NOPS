"""
ByggSjekk – Seed mock-sak

Skriptet oppretter en realistisk mock-sak for testing og demonstrasjon:
  - Eiendom: Storgata 1, Oslo (gnr 207, bnr 123)
  - Sak: Avviksvurdering av leilighet
  - To kildedokumenter: godkjent rammetillatelse (2005) og dagens plantegning
  - Strukturerte planar med rom-data
  - 4 realistiske avvik med konfidensscorer
  - Regeltreff knyttet til avvikene

Kjøring:
    python scripts/seed_mock_case.py

Forutsetninger:
  - DATABASE_URL er satt (fra .env)
  - make migrate er kjørt
  - make seed-rules er kjørt (for regelreferanser)
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Mock-data
# ---------------------------------------------------------------------------

PROPERTY = {
    "id": str(uuid.uuid4()),
    "street_address": "Storgata 1",
    "municipality": "Oslo",
    "municipality_number": "0301",
    "postal_code": "0182",
    "gnr": "207",
    "bnr": "123",
    "snr": None,
    "fnr": None,
    "property_type": "apartment",
    "build_year": 1965,
    "total_area_m2": 82.0,
    "floors": 5,
    "created_at": datetime.now(timezone.utc),
}

CASE = {
    "id": str(uuid.uuid4()),
    "property_id": PROPERTY["id"],
    "case_number": "BS-2024-0001",
    "title": "Avviksvurdering – Storgata 1 leilighet 3. etg",
    "status": "ACTIVE",
    "customer_type": "ARCHITECT_FIRM",
    "assigned_architect": "Arkitekt Marte Olsen",
    "notes": "Mock-sak generert av seed_mock_case.py for testing og demonstrasjon.",
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc),
}

SOURCE_DOCUMENTS = [
    {
        "id": str(uuid.uuid4()),
        "case_id": CASE["id"],
        "document_type": "APPROVED_PLAN",
        "source_type": "MUNICIPALITY_ARCHIVE",
        "filename": "rammetillatelse_2005_storgata1.pdf",
        "original_filename": "rammetillatelse_2005_storgata1.pdf",
        "storage_key": "mock/rammetillatelse_2005_storgata1.pdf",
        "file_size_bytes": 2_456_789,
        "mime_type": "application/pdf",
        "page_count": 12,
        "approval_status": "VERIFIED_APPROVED",
        "approval_date": datetime(2005, 6, 14, tzinfo=timezone.utc),
        "approval_reference": "SAK/2005/1234",
        "issuing_authority": "Oslo kommune, Plan- og bygningsetaten",
        "processing_status": "COMPLETED",
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "case_id": CASE["id"],
        "document_type": "CURRENT_STATE_PLAN",
        "source_type": "CUSTOMER_UPLOAD",
        "filename": "dagens_tilstand_storgata1_2024.pdf",
        "original_filename": "dagens_tilstand_storgata1_2024.pdf",
        "storage_key": "mock/dagens_tilstand_storgata1_2024.pdf",
        "file_size_bytes": 1_834_512,
        "mime_type": "application/pdf",
        "page_count": 8,
        "approval_status": "UNKNOWN",
        "approval_date": None,
        "approval_reference": None,
        "issuing_authority": None,
        "processing_status": "COMPLETED",
        "created_at": datetime.now(timezone.utc),
    },
]

# Rom i godkjent tegning (2005)
APPROVED_SPACES = [
    {"room_id": "rom-01", "name": "Entré", "function": "HALLWAY", "area_m2": 6.5, "floor": 3},
    {"room_id": "rom-02", "name": "Stue", "function": "LIVING_ROOM", "area_m2": 28.0, "floor": 3},
    {"room_id": "rom-03", "name": "Kjøkken", "function": "KITCHEN", "area_m2": 12.0, "floor": 3},
    {"room_id": "rom-04", "name": "Soverom 1", "function": "BEDROOM", "area_m2": 14.5, "floor": 3},
    {"room_id": "rom-05", "name": "Soverom 2", "function": "BEDROOM", "area_m2": 11.0, "floor": 3},
    {"room_id": "rom-06", "name": "Bad", "function": "BATHROOM", "area_m2": 5.5, "floor": 3},
    {"room_id": "rom-07", "name": "WC", "function": "TOILET", "area_m2": 2.5, "floor": 3},
    {"room_id": "rom-08", "name": "Bod", "function": "STORAGE", "area_m2": 4.0, "floor": 3},
    {"room_id": "rom-09", "name": "Balkong", "function": "BALCONY", "area_m2": 8.0, "floor": 3},
]

# Rom i dagens tilstand (2024) – med endringer
CURRENT_SPACES = [
    {"room_id": "rom-01", "name": "Entré", "function": "HALLWAY", "area_m2": 6.5, "floor": 3},
    {"room_id": "rom-02", "name": "Stue", "function": "LIVING_ROOM", "area_m2": 22.0, "floor": 3},
    {"room_id": "rom-03", "name": "Kjøkken", "function": "KITCHEN", "area_m2": 12.0, "floor": 3},
    {"room_id": "rom-04", "name": "Soverom 1", "function": "BEDROOM", "area_m2": 14.5, "floor": 3},
    # rom-05 er nå kontoret (bruksendring)
    {"room_id": "rom-05", "name": "Kontor", "function": "OFFICE", "area_m2": 11.0, "floor": 3},
    {"room_id": "rom-06", "name": "Bad", "function": "BATHROOM", "area_m2": 8.5, "floor": 3},  # utvidet
    {"room_id": "rom-07", "name": "WC", "function": "TOILET", "area_m2": 2.5, "floor": 3},
    # rom-08 mangler (bod er fjernet/integrert i bad)
    # Nytt rom – tilbygg på loft/kjeller?
    {"room_id": "rom-10", "name": "Hobbyrom", "function": "UTILITY_ROOM", "area_m2": 18.0, "floor": 4},
    # Balkongen er bygget inn
    # (mangler i dagens plan)
]

DEVIATIONS = [
    {
        "id": str(uuid.uuid4()),
        "case_id": CASE["id"],
        "deviation_number": "AVV-001",
        "category": "BEDROOM_UTILITY_DISCREPANCY",
        "severity": "HIGH",
        "status": "PENDING_REVIEW",
        "title": "Soverom 2 fremstår som kontor i dagens plan",
        "description": (
            "I godkjent rammetillatelse (2005) er rom 5 tegnet og godkjent som 'Soverom 2' "
            "(11,0 m², varig opphold). I dagens plantegning er det samme rommet merket 'Kontor'. "
            "En slik bruksendring av rom fra soverom til kontor kan være søknadspliktig dersom "
            "det medfører endring i branncelle, rømningsvei eller ventilasjonskrav."
        ),
        "affected_room_ids": ["rom-05"],
        "confidence_score": 0.91,
        "ai_model": "gpt-4o",
        "ai_model_version": "2024-05-13",
        "evidence": {
            "approved_label": "Soverom 2",
            "current_label": "Kontor",
            "approved_function": "BEDROOM",
            "current_function": "OFFICE",
            "area_unchanged": True,
        },
        "architect_note": None,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "case_id": CASE["id"],
        "deviation_number": "AVV-002",
        "category": "ADDITION_DETECTED",
        "severity": "HIGH",
        "status": "PENDING_REVIEW",
        "title": "Nytt rom i 4. etasje ikke tegnet i godkjent plan",
        "description": (
            "Dagens plantegning viser et 'Hobbyrom' på 18,0 m² i 4. etasje. "
            "Godkjent rammetillatelse fra 2005 viser kun 3 etasjer for denne leiligheten. "
            "Rommet er ikke dokumentert i godkjente tegninger og kan indikere ulovlig påbygg "
            "eller loftsombygging uten tillatelse. Søknadspliktig etter PBL § 20-1."
        ),
        "affected_room_ids": ["rom-10"],
        "confidence_score": 0.87,
        "ai_model": "gpt-4o",
        "ai_model_version": "2024-05-13",
        "evidence": {
            "floors_in_approved": [3],
            "floors_in_current": [3, 4],
            "new_area_m2": 18.0,
        },
        "architect_note": None,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "case_id": CASE["id"],
        "deviation_number": "AVV-003",
        "category": "BALCONY_TERRACE_DISCREPANCY",
        "severity": "MEDIUM",
        "status": "PENDING_REVIEW",
        "title": "Balkong mangler i dagens plan",
        "description": (
            "Godkjent rammetillatelse viser en balkong på 8,0 m² tilknyttet stuen. "
            "Balkong er ikke tegnet inn i dagens plantegning. Dette kan indikere at balkongen "
            "er innebygd og gjort om til del av stuen (stue er redusert fra 28 m² til 22 m², "
            "men balkongen er ikke medregnet), eller at den er revet uten tillatelse."
        ),
        "affected_room_ids": ["rom-02", "rom-09"],
        "confidence_score": 0.78,
        "ai_model": "gpt-4o",
        "ai_model_version": "2024-05-13",
        "evidence": {
            "balcony_in_approved": True,
            "balcony_in_current": False,
            "stue_area_reduction_m2": 6.0,
        },
        "architect_note": None,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": str(uuid.uuid4()),
        "case_id": CASE["id"],
        "deviation_number": "AVV-004",
        "category": "ROOM_DEFINITION_CHANGE",
        "severity": "MEDIUM",
        "status": "PENDING_REVIEW",
        "title": "Bad er utvidet fra 5,5 m² til 8,5 m²",
        "description": (
            "Badet er registrert som 5,5 m² i godkjent plan og 8,5 m² i dagens plan. "
            "En utvidelse på 3,0 m² kan skyldes at den godkjente boden (4,0 m²) er delvis "
            "integrert i badet. Boden er ikke lenger synlig i dagens tegning. "
            "Endringen kan medføre endrede ventilasjonskrav og behov for ny godkjenning av VVS-opplegg."
        ),
        "affected_room_ids": ["rom-06", "rom-08"],
        "confidence_score": 0.82,
        "ai_model": "gpt-4o",
        "ai_model_version": "2024-05-13",
        "evidence": {
            "bathroom_area_approved_m2": 5.5,
            "bathroom_area_current_m2": 8.5,
            "storage_missing_in_current": True,
        },
        "architect_note": None,
        "created_at": datetime.now(timezone.utc),
    },
]

RULE_MATCHES = [
    {
        "id": str(uuid.uuid4()),
        "deviation_id": DEVIATIONS[0]["id"],
        "rule_id": "pbl-31-2-bruksendring",
        "match_confidence": 0.88,
        "match_reason": "Bruksendring fra soverom (varig opphold) til kontor indikerer søknadspliktig tiltak etter PBL § 31-2.",
    },
    {
        "id": str(uuid.uuid4()),
        "deviation_id": DEVIATIONS[0]["id"],
        "rule_id": "tek17-12-2-rom-varig-opphold",
        "match_confidence": 0.75,
        "match_reason": "Endret funksjon kan påvirke ventilasjonskrav for rom for varig opphold.",
    },
    {
        "id": str(uuid.uuid4()),
        "deviation_id": DEVIATIONS[1]["id"],
        "rule_id": "pbl-20-1-tiltak-krav-soknad",
        "match_confidence": 0.94,
        "match_reason": "Påbygg og tilbygg er eksplisitt nevnt som søknadspliktige tiltak i PBL § 20-1.",
    },
    {
        "id": str(uuid.uuid4()),
        "deviation_id": DEVIATIONS[2]["id"],
        "rule_id": "tek17-12-9-balkong",
        "match_confidence": 0.80,
        "match_reason": "Balkong som ikke lenger er synlig i tegning kan indikere innbygging uten tillatelse.",
    },
    {
        "id": str(uuid.uuid4()),
        "deviation_id": DEVIATIONS[3]["id"],
        "rule_id": "sak10-6-4-ferdigattest",
        "match_confidence": 0.70,
        "match_reason": "Utvidelse av bad uten dokumentasjon indikerer manglende ferdigattest for arbeider.",
    },
]


async def seed_mock_case() -> None:
    """Opprett en komplett mock-sak med alle relaterte entiteter."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Importer modeller dynamisk
            try:
                from app.models.property import Property  # type: ignore
                from app.models.case import PropertyCase  # type: ignore
                from app.models.document import SourceDocument, StructuredPlan  # type: ignore
                from app.models.deviation import Deviation, RuleMatch  # type: ignore
            except ImportError:
                print(
                    "FEIL: Kunne ikke importere modeller. "
                    "Kjor skriptet via 'make seed-mock' for riktig PYTHONPATH."
                )
                return

            # 1. Eiendom
            prop = Property(**PROPERTY)
            session.add(prop)

            # 2. Sak
            case = PropertyCase(**CASE)
            session.add(case)

            # 3. Kildedokumenter
            doc_approved = SourceDocument(**SOURCE_DOCUMENTS[0])
            doc_current = SourceDocument(**SOURCE_DOCUMENTS[1])
            session.add(doc_approved)
            session.add(doc_current)

            # 4. Strukturerte planer
            plan_approved = StructuredPlan(
                id=str(uuid.uuid4()),
                document_id=doc_approved.id,
                spaces=APPROVED_SPACES,
                total_area_m2=sum(s["area_m2"] for s in APPROVED_SPACES if s["function"] != "BALCONY"),
                parsing_confidence=0.95,
                parsed_at=datetime.now(timezone.utc),
            )
            plan_current = StructuredPlan(
                id=str(uuid.uuid4()),
                document_id=doc_current.id,
                spaces=CURRENT_SPACES,
                total_area_m2=sum(s["area_m2"] for s in CURRENT_SPACES if s["function"] != "BALCONY"),
                parsing_confidence=0.92,
                parsed_at=datetime.now(timezone.utc),
            )
            session.add(plan_approved)
            session.add(plan_current)

            # 5. Avvik
            deviation_objects = []
            for dev_data in DEVIATIONS:
                dev = Deviation(**dev_data)
                session.add(dev)
                deviation_objects.append(dev)

            # 6. Regeltreff
            for rm_data in RULE_MATCHES:
                rm = RuleMatch(**rm_data)
                session.add(rm)

    print("Mock-sak seeded:")
    print(f"  Eiendom:         {PROPERTY['street_address']}, {PROPERTY['municipality']}")
    print(f"  Sak:             {CASE['case_number']} – {CASE['title']}")
    print(f"  Kildedokumenter: {len(SOURCE_DOCUMENTS)}")
    print(f"  Avvik:           {len(DEVIATIONS)}")
    print(f"  Regeltreff:      {len(RULE_MATCHES)}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))
    asyncio.run(seed_mock_case())
