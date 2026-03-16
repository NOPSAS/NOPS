"""
ByggSjekk – Eiendomsoppslag-skjemaer for kommunekoblingsresultater.

Disse skjemaene brukes av municipality connector-integrasjonen og eksponeres
via /property-endepunktet.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Innkommende forespørsel
# ---------------------------------------------------------------------------


class PropertyLookupRequest(BaseModel):
    """Forespørsel om eiendomsoppslag mot kommunalt register."""

    gnr: int = Field(description="Gårdsnummer")
    bnr: int = Field(description="Bruksnummer")
    snr: int | None = Field(default=None, description="Seksjonsnummer (valgfritt)")
    fnr: int | None = Field(default=None, description="Festenummer (valgfritt)")
    municipality_number: str = Field(
        description="Kommunenummer (4 siffer, f.eks. '0301' for Oslo)",
        min_length=4,
        max_length=4,
    )


# ---------------------------------------------------------------------------
# Dispensasjon
# ---------------------------------------------------------------------------


class Dispensasjon(BaseModel):
    """En dispensasjon knyttet til en eiendom eller et tiltak."""

    id: str | None = None
    sak_id: str | None = Field(default=None, description="Kommunalt saksnummer")
    paragraf: str | None = Field(default=None, description="Hjemmel det er søkt dispensasjon fra")
    dato_innvilget: str | None = Field(default=None, description="ISO 8601 dato for innvilgelse")
    dato_avslatt: str | None = Field(default=None, description="ISO 8601 dato for avslag")
    status: str | None = Field(
        default=None,
        description="Status: INNVILGET | AVSLATT | UNDER_BEHANDLING",
    )
    beskrivelse: str | None = None
    kommunens_begrunnelse: str | None = None
    raw: dict[str, Any] | None = Field(default=None, description="Rådata fra kommunalt API")


# ---------------------------------------------------------------------------
# Arealplan
# ---------------------------------------------------------------------------


class Arealplan(BaseModel):
    """Gjeldende reguleringsplan eller kommuneplan for eiendommen."""

    plan_id: str | None = None
    plan_navn: str | None = None
    plan_type: str | None = Field(
        default=None,
        description="F.eks. 'REGULERINGSPLAN' eller 'KOMMUNEPLAN'",
    )
    formål: str | None = Field(default=None, description="Planformål, f.eks. 'boligbebyggelse'")
    vedtaksdato: str | None = None
    kunngjøringsdato: str | None = None
    utnyttingsgrad: str | None = Field(
        default=None,
        description="Tillatt utnyttingsgrad, f.eks. 'BYA=30%' eller 'BRA=250%'",
    )
    gesims_høyde_m: float | None = None
    møne_høyde_m: float | None = None
    freda: bool = False
    vernet: bool = False
    raw: dict[str, Any] | None = Field(default=None, description="Rådata fra kommunalt API")


# ---------------------------------------------------------------------------
# Dokumentanalyse-resultat (brukt internt av pipeline)
# ---------------------------------------------------------------------------


class DokAnalyseResult(BaseModel):
    """
    Resultat av dokumentanalyse utført av document_ingestion-tjenesten.

    Brukes til å formidle klassifisering og godkjenningsstatus fra
    dokumentprosesseringspipelinen tilbake til API-laget.
    """

    document_type: str = Field(description="Klassifisert dokumenttype")
    document_type_confidence: float = Field(
        ge=0.0, le=1.0, description="Konfidensgrad for dokumenttype-klassifiseringen"
    )
    approval_status: str = Field(
        description="RECEIVED | ASSUMED_APPROVED | VERIFIED_APPROVED | UNKNOWN"
    )
    approval_status_confidence: float = Field(
        ge=0.0, le=1.0, description="Konfidensgrad for godkjenningsstatus"
    )
    classification_method: str = Field(
        description="Metode brukt: 'rule_based' | 'llm' | 'llm_unavailable'"
    )
    extracted_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Strukturerte felter ekstrahert fra dokumentet",
    )


# ---------------------------------------------------------------------------
# Plan-rapport resultat (returneres fra planparser)
# ---------------------------------------------------------------------------


class PlanrapportResult(BaseModel):
    """
    Strukturert resultat fra plan-parseren for et enkeltdokument.

    Mirrors ``StructuredPlanData`` fra services/plan_parser/parser.py,
    men i Pydantic-format for API-serialisering.
    """

    document_id: str
    storage_key: str
    total_area: float | None = None
    room_count: int | None = None
    floor_count: int | None = None
    floors: list[dict[str, Any]] = Field(default_factory=list)
    measurements: list[dict[str, Any]] = Field(default_factory=list)
    parsing_confidence: float | None = Field(
        default=None, ge=0.0, le=1.0
    )
    parse_warnings: list[str] = Field(default_factory=list)
    raw_text_preview: str | None = Field(
        default=None, description="Første 500 tegn av OCR-tekst for feilsøking"
    )
