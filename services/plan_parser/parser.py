"""
ByggSjekk – Plan parser service.

Provides:
  StructuredPlanData     – Pydantic output model
  PlanParserInterface    – ABC defining the parse() contract
  PDFPlanParser          – real PDF parsing using pdfplumber
  MockPlanParser         – realistic mock implementation for development
  get_plan_parser()      – factory function
"""

from __future__ import annotations

import abc
import io
import logging
import random
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Norwegian room name → space_type mappings
# ---------------------------------------------------------------------------

_ROOM_TYPE_MAP: dict[str, str] = {
    "stue": "living_room",
    "kjøkken": "kitchen",
    "kjokken": "kitchen",
    "spisestue": "dining_room",
    "soverom": "bedroom",
    "bad": "bathroom",
    "wc": "toilet",
    "toalett": "toilet",
    "gang": "hallway",
    "entre": "hallway",
    "hall": "hallway",
    "bod": "storage",
    "lager": "storage",
    "vaskerom": "laundry",
    "teknisk rom": "utility",
    "teknisk": "utility",
    "garasje": "garage",
    "carport": "carport",
    "terrasse": "terrace",
    "balkong": "balcony",
    "veranda": "terrace",
    "kontor": "office",
    "arbeidsrom": "office",
    "kjellerrom": "basement_room",
    "kjeller": "basement_room",
    "loft": "attic",
    "tv-stue": "living_room",
    "allrom": "living_room",
    "garderoberom": "dressing_room",
    "garderobe": "dressing_room",
    "baderom": "bathroom",
    "dusjrom": "bathroom",
    "bibliotek": "library",
    "hobbyrom": "hobby_room",
    "trimrom": "gym",
    "spillerom": "playroom",
    "grovkjøkken": "scullery",
    "anretning": "pantry",
}

_FLOOR_LABELS_MAP: dict[str, int] = {
    "underetasje": -1,
    "kjeller": -1,
    "u.etg": -1,
    "u.etasje": -1,
    "1. etasje": 1,
    "1.etasje": 1,
    "1 etasje": 1,
    "første etasje": 1,
    "hovedetasje": 1,
    "2. etasje": 2,
    "2.etasje": 2,
    "andre etasje": 2,
    "3. etasje": 3,
    "3.etasje": 3,
    "loft": 3,
    "loftsetasje": 3,
}

_AREA_PATTERN = re.compile(
    r"(\d+[,.]?\d*)\s*m[²2]", re.IGNORECASE
)
_FLOOR_LABEL_PATTERN = re.compile(
    r"(\d+)\.\s*etasje|underetasje|kjeller|loft", re.IGNORECASE
)
_MEASUREMENT_PATTERN = re.compile(
    r"([\w\s]+(?:høyde|lengde|bredde|bygglinje|gesims|møne))[:\s]+(\d+[,.]?\d*)\s*(m|cm|mm)?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Output data models
# ---------------------------------------------------------------------------


class SpaceData(BaseModel):
    name: str
    space_type: str
    floor_number: int | None = None
    area: float | None = None  # m²
    confidence: float = 1.0
    attributes: dict[str, Any] = Field(default_factory=dict)


class FloorData(BaseModel):
    floor_number: int
    label: str  # e.g. "Underetasje", "1. etasje", "Loft"
    total_area: float | None = None
    spaces: list[SpaceData] = Field(default_factory=list)
    raw_annotations: list[str] = Field(default_factory=list)


class MeasurementData(BaseModel):
    label: str
    value: float
    unit: str = "m"
    confidence: float = 1.0


class StructuredPlanData(BaseModel):
    """Complete structured representation of a parsed building plan."""

    document_id: str
    storage_key: str
    floors: list[FloorData] = Field(default_factory=list)
    measurements: list[MeasurementData] = Field(default_factory=list)
    total_area: float | None = None
    room_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def all_spaces(self) -> list[SpaceData]:
        return [space for floor in self.floors for space in floor.spaces]


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class PlanParserInterface(abc.ABC):
    """All plan parsers must implement this async interface."""

    @abc.abstractmethod
    async def parse(
        self,
        document_id: str,
        storage_key: str,
    ) -> StructuredPlanData:
        """Parse the plan document identified by *storage_key* and return
        a structured representation.

        Args:
            document_id: Database UUID of the SourceDocument record.
            storage_key: Object-storage path used to download raw bytes.

        Returns:
            A populated :class:`StructuredPlanData` instance.
        """


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------

_SPACE_TEMPLATES: list[tuple[str, str, float]] = [
    ("Stue", "living_room", 28.0),
    ("Kjøkken", "kitchen", 14.0),
    ("Spisestue", "dining_room", 18.0),
    ("Hovedsoverom", "bedroom", 16.5),
    ("Soverom 2", "bedroom", 12.0),
    ("Soverom 3", "bedroom", 11.0),
    ("Bad", "bathroom", 8.0),
    ("Gjeste-wc", "toilet", 3.5),
    ("Gang", "hallway", 9.0),
    ("Bod", "storage", 5.5),
    ("Vaskerom", "laundry", 6.0),
    ("Garasje", "garage", 32.0),
    ("Terrasse", "terrace", 20.0),
    ("Kjellerrom", "basement_room", 22.0),
]

_FLOOR_LABELS = ["Underetasje", "1. etasje", "2. etasje", "Loft"]


class PDFPlanParser(PlanParserInterface):
    """
    Reell PDF-parser som bruker pdfplumber til å ekstrahere romdata og mål
    fra norske byggetegninger.

    Strategi:
    1. Ekstraher all tekst fra PDF-sider
    2. Identifiser etasjer basert på sideetiketter og innhold
    3. Finn rom via norske romnavn og m²-annoteringer
    4. Ekstraher mål (gesimshøyde, mønehøyde, bygglinje osv.)
    5. Beregn arealer og romtelling
    """

    async def parse(
        self,
        document_id: str,
        storage_key: str,
    ) -> StructuredPlanData:
        logger.info(
            "PDFPlanParser.parse called (document_id=%s, key=%s)",
            document_id,
            storage_key,
        )

        # Import pdfplumber - falls back to mock if not available
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber ikke installert – bruker MockPlanParser som fallback")
            fallback = MockPlanParser()
            return await fallback.parse(document_id, storage_key)

        # Download bytes from storage key (storage_key is a path or URL)
        try:
            pdf_bytes = await self._load_bytes(storage_key)
        except Exception as exc:
            logger.warning("Kunne ikke laste ned PDF '%s': %s – bruker mock", storage_key, exc)
            fallback = MockPlanParser()
            return await fallback.parse(document_id, storage_key)

        # Parse with pdfplumber
        try:
            return self._parse_pdf_bytes(pdf_bytes, document_id, storage_key)
        except Exception as exc:
            logger.error("PDF-parsing feilet for %s: %s", document_id, exc)
            fallback = MockPlanParser()
            return await fallback.parse(document_id, storage_key)

    async def _load_bytes(self, storage_key: str) -> bytes:
        """Laster ned bytes fra MinIO/S3 eller lokal fil."""
        if storage_key.startswith("/") or storage_key.startswith("./"):
            with open(storage_key, "rb") as f:
                return f.read()
        # Try using the storage adapter via environment
        import os
        try:
            import aiobotocore.session
            session = aiobotocore.session.get_session()
            endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
            access_key = os.getenv("MINIO_ACCESS_KEY", "byggsjekk")
            secret_key = os.getenv("MINIO_SECRET_KEY", "byggsjekk123")
            bucket = os.getenv("MINIO_BUCKET", "byggsjekk-documents")
            use_ssl = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

            async with session.create_client(
                "s3",
                endpoint_url=f"{'https' if use_ssl else 'http'}://{endpoint}",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            ) as client:
                response = await client.get_object(Bucket=bucket, Key=storage_key)
                async with response["Body"] as stream:
                    return await stream.read()
        except Exception:
            raise FileNotFoundError(f"Kunne ikke laste '{storage_key}' fra lagring")

    def _parse_pdf_bytes(
        self,
        pdf_bytes: bytes,
        document_id: str,
        storage_key: str,
    ) -> StructuredPlanData:
        import pdfplumber

        floors_dict: dict[int, tuple[str, list[SpaceData], list[str], float]] = {}
        measurements: list[MeasurementData] = []
        all_raw_text: list[str] = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                all_raw_text.append(text)
                self._process_page(text, page_num, floors_dict, measurements)

        if not floors_dict:
            # Fallback: treat entire document as single floor
            all_text = "\n".join(all_raw_text)
            spaces = self._extract_spaces_from_text(all_text, floor_number=1)
            floors_dict[1] = ("1. etasje", spaces, [all_text[:200]], 0.0)

        # Build FloorData list
        floor_list: list[FloorData] = []
        total_area = 0.0
        for floor_num in sorted(floors_dict.keys()):
            label, spaces, annotations, _ = floors_dict[floor_num]
            floor_area = sum(s.area for s in spaces if s.area is not None)
            total_area += floor_area
            floor_list.append(FloorData(
                floor_number=floor_num,
                label=label,
                total_area=round(floor_area, 2),
                spaces=spaces,
                raw_annotations=annotations,
            ))

        room_count = sum(len(f.spaces) for f in floor_list)

        return StructuredPlanData(
            document_id=document_id,
            storage_key=storage_key,
            floors=floor_list,
            measurements=measurements,
            total_area=round(total_area, 2),
            room_count=room_count,
            metadata={
                "parser": "PDFPlanParser",
                "num_floors": len(floor_list),
                "confidence": 0.75 if room_count > 0 else 0.3,
                "num_pdf_pages": len(all_raw_text),
            },
        )

    def _process_page(
        self,
        text: str,
        page_num: int,
        floors_dict: dict,
        measurements: list[MeasurementData],
    ) -> None:
        """Prosesserer én PDF-side og oppdaterer floors_dict og measurements."""
        # Detect floor from text
        floor_num = self._detect_floor(text, page_num)
        label = self._floor_label(floor_num)

        # Extract spaces
        spaces = self._extract_spaces_from_text(text, floor_num)

        # Extract measurements
        for match in _MEASUREMENT_PATTERN.finditer(text):
            label_str = match.group(1).strip()
            value_str = match.group(2).replace(",", ".")
            unit = match.group(3) or "m"
            try:
                measurements.append(MeasurementData(
                    label=label_str,
                    value=float(value_str),
                    unit=unit.lower(),
                    confidence=0.8,
                ))
            except ValueError:
                pass

        # Merge into floors_dict
        if floor_num in floors_dict:
            existing_label, existing_spaces, existing_ann, _ = floors_dict[floor_num]
            combined = existing_spaces + spaces
            floors_dict[floor_num] = (existing_label, combined, existing_ann + [text[:100]], 0.0)
        else:
            floors_dict[floor_num] = (label, spaces, [text[:100]], 0.0)

    def _detect_floor(self, text: str, page_num: int) -> int:
        """Detekterer etasjenummer fra tekstinnhold."""
        text_lower = text.lower()
        for label, floor_num in _FLOOR_LABELS_MAP.items():
            if label in text_lower:
                return floor_num
        # Try pattern: "2. etasje", "3. etasje"
        match = re.search(r"(\d+)\.\s*etasje", text_lower)
        if match:
            return int(match.group(1))
        # Default: assume page order = floor order
        return page_num + 1

    def _floor_label(self, floor_num: int) -> str:
        labels = {-1: "Underetasje / kjeller", 0: "Sokkel", 1: "1. etasje", 2: "2. etasje", 3: "3. etasje / loft"}
        return labels.get(floor_num, f"{floor_num}. etasje")

    def _extract_spaces_from_text(self, text: str, floor_number: int) -> list[SpaceData]:
        """Finner romnavn og arealer fra tekst."""
        spaces: list[SpaceData] = []
        lines = text.split("\n")

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Check for Norwegian room names
            found_room_type: str | None = None
            room_name_found: str | None = None

            line_lower = line_clean.lower()
            for room_name, room_type in _ROOM_TYPE_MAP.items():
                if room_name in line_lower:
                    found_room_type = room_type
                    room_name_found = room_name.capitalize()
                    break

            if found_room_type is None:
                continue

            # Try to find area on same line or nearby
            area_match = _AREA_PATTERN.search(line_clean)
            area: float | None = None
            if area_match:
                try:
                    area = float(area_match.group(1).replace(",", "."))
                except ValueError:
                    pass

            # Use room name from line if available
            display_name = self._extract_room_label(line_clean, room_name_found or found_room_type)

            spaces.append(SpaceData(
                name=display_name,
                space_type=found_room_type,
                floor_number=floor_number,
                area=area,
                confidence=0.8 if area is not None else 0.5,
                attributes={"source": "pdf_parser", "raw_line": line_clean[:80]},
            ))

        return spaces

    def _extract_room_label(self, line: str, fallback: str) -> str:
        """Henter romnavn fra en tekstlinje (kapitalisert)."""
        # Remove area patterns and clean up
        cleaned = _AREA_PATTERN.sub("", line).strip()
        cleaned = re.sub(r"\d+[.,]\d*", "", cleaned).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .-")
        if len(cleaned) > 2:
            return cleaned.capitalize()
        return fallback.capitalize()


def get_plan_parser(use_pdf: bool = True) -> PlanParserInterface:
    """Factory: returnerer riktig parser basert på konfigurasjon."""
    if use_pdf:
        try:
            import pdfplumber  # noqa: F401
            return PDFPlanParser()
        except ImportError:
            pass
    return MockPlanParser()


class MockPlanParser(PlanParserInterface):
    """Return realistic but synthetic plan data.

    Useful during development before a real PDF/IFC parser is wired in.
    The mock generates a plausible 2-floor dwelling with randomised areas
    (within ±10 % of the template values) to exercise downstream logic.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    async def parse(
        self,
        document_id: str,
        storage_key: str,
    ) -> StructuredPlanData:
        logger.info(
            "MockPlanParser.parse called (document_id=%s, key=%s)",
            document_id,
            storage_key,
        )

        num_floors = self._rng.randint(1, 3)
        floors: list[FloorData] = []
        total_area = 0.0

        # Select a subset of spaces to distribute across floors
        available = list(_SPACE_TEMPLATES)
        self._rng.shuffle(available)
        spaces_per_floor = max(3, len(available) // num_floors)

        for floor_idx in range(num_floors):
            label = _FLOOR_LABELS[min(floor_idx, len(_FLOOR_LABELS) - 1)]
            floor_spaces_data = available[
                floor_idx * spaces_per_floor: (floor_idx + 1) * spaces_per_floor
            ]
            spaces: list[SpaceData] = []
            floor_area = 0.0

            for name, space_type, base_area in floor_spaces_data:
                jitter = self._rng.uniform(-0.1, 0.1)
                area = round(base_area * (1 + jitter), 2)
                floor_area += area
                spaces.append(
                    SpaceData(
                        name=name,
                        space_type=space_type,
                        floor_number=floor_idx,
                        area=area,
                        confidence=round(self._rng.uniform(0.75, 0.99), 3),
                        attributes={"source": "mock"},
                    )
                )

            floor_area = round(floor_area, 2)
            total_area += floor_area
            floors.append(
                FloorData(
                    floor_number=floor_idx,
                    label=label,
                    total_area=floor_area,
                    spaces=spaces,
                    raw_annotations=[f"Tegningsnr. A{floor_idx + 1}00", label],
                )
            )

        all_space_count = sum(len(f.spaces) for f in floors)
        measurements = [
            MeasurementData(label="Bygglinje mot veg", value=round(self._rng.uniform(4.0, 10.0), 1), unit="m"),
            MeasurementData(label="Gesimshøyde", value=round(self._rng.uniform(6.0, 8.5), 2), unit="m"),
            MeasurementData(label="Mønehøyde", value=round(self._rng.uniform(8.0, 10.5), 2), unit="m"),
        ]

        return StructuredPlanData(
            document_id=document_id,
            storage_key=storage_key,
            floors=floors,
            measurements=measurements,
            total_area=round(total_area, 2),
            room_count=all_space_count,
            metadata={
                "parser": "MockPlanParser",
                "num_floors": num_floors,
                "confidence": 0.85,
            },
        )
