"""
services/municipality_connectors/adapter.py

Abstrakt grensesnitt og implementasjoner for kommuneintegrasjoner.

Arkitektur:
  - MunicipalityAdapterInterface: ABC som definerer kontrakten
  - MockKommuneAdapter: Mock-implementasjon med realistiske norske testdata
  - FallbackEmailAdapter: Genererer e-postutkast for manuell forespørsel

Bruk:
    adapter = MockKommuneAdapter()
    result = await adapter.fetch_approval_status(
        gnr="207", bnr="123", municipality="Oslo", document_type="RAMMETILLATELSE"
    )
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

try:
    from jinja2 import Template
except ImportError:
    Template = None  # type: ignore


# =============================================================================
# Abstrakt grensesnitt
# =============================================================================

class MunicipalityAdapterInterface(ABC):
    """
    Abstrakt base for kommuneadaptere.

    Alle kommuneadaptere skal implementere dette grensesnittet slik at
    deviation_engine og rule_engine kan bruke dem utskiftbart.
    """

    @abstractmethod
    async def fetch_approval_status(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
        document_type: str,
    ) -> dict[str, Any]:
        """
        Hent godkjenningsstatus for et dokument fra kommunens arkiv.

        Args:
            gnr:           Gårdsnummer
            bnr:           Bruksnummer
            municipality:  Kommunenavn (f.eks. "Oslo")
            document_type: Dokumenttype (f.eks. "RAMMETILLATELSE", "IGANGSETTINGSTILLATELSE")

        Returns:
            Dict med feltene:
              - approval_status: str  (VERIFIED_APPROVED | ASSUMED_APPROVED | UNKNOWN)
              - approval_date: str | None  (ISO 8601)
              - approval_reference: str | None
              - issuing_authority: str | None
              - source: str  (hvilken kobling som returnerte resultatet)
              - confidence: float  (0.0–1.0)
              - raw_data: dict  (rå respons fra kildesystemet, for sporbarhet)
        """
        ...

    @abstractmethod
    async def fetch_case_history(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
    ) -> list[dict[str, Any]]:
        """
        Hent historisk byggesakshistorikk for en eiendom.

        Returns:
            Liste med saksreferanser og metadata.
        """
        ...


# =============================================================================
# Mock-implementasjon
# =============================================================================

class MockKommuneAdapter(MunicipalityAdapterInterface):
    """
    Mock-implementasjon for testing og demonstrasjon.

    Returnerer realistiske norske kommunedata basert på gnr/bnr-kombinasjoner.
    Simulerer nettverksforsinkelse for realistisk testopplevelse.
    """

    # Simulerte godkjente saker (gnr-bnr -> data)
    _MOCK_DATABASE: dict[str, dict[str, Any]] = {
        "207-123": {
            "approval_status": "VERIFIED_APPROVED",
            "approval_date": "2005-06-14",
            "approval_reference": "SAK/2005/1234",
            "issuing_authority": "Oslo kommune, Plan- og bygningsetaten",
            "documents": [
                {
                    "type": "RAMMETILLATELSE",
                    "reference": "SAK/2005/1234-RA",
                    "date": "2005-06-14",
                },
                {
                    "type": "IGANGSETTINGSTILLATELSE",
                    "reference": "SAK/2005/1234-IG",
                    "date": "2005-09-01",
                },
                {
                    "type": "FERDIGATTEST",
                    "reference": "SAK/2006/0456-FA",
                    "date": "2006-11-20",
                },
            ],
        },
        "48-22": {
            "approval_status": "ASSUMED_APPROVED",
            "approval_date": "1987-03-10",
            "approval_reference": "1987/0892",
            "issuing_authority": "Bergen kommune",
            "documents": [
                {
                    "type": "BYGGETILLATELSE",
                    "reference": "1987/0892-BT",
                    "date": "1987-03-10",
                },
            ],
        },
        "12-5": {
            "approval_status": "UNKNOWN",
            "approval_date": None,
            "approval_reference": None,
            "issuing_authority": None,
            "documents": [],
        },
    }

    _MOCK_CASE_HISTORY: dict[str, list[dict[str, Any]]] = {
        "207-123": [
            {
                "reference": "SAK/2005/1234",
                "type": "Rammetillatelse",
                "status": "Godkjent",
                "date": "2005-06-14",
                "description": "Oppføring av leilighetsbygg, 5 etasjer",
            },
            {
                "reference": "SAK/2006/0456",
                "type": "Ferdigattest",
                "status": "Utstedt",
                "date": "2006-11-20",
                "description": "Ferdigattest for Storgata 1",
            },
        ],
    }

    async def fetch_approval_status(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
        document_type: str,
    ) -> dict[str, Any]:
        """Returner mock godkjenningsstatus med simulert nettverksforsinkelse."""

        # Simuler API-kall (50–200 ms)
        await asyncio.sleep(0.05)

        key = f"{gnr}-{bnr}"
        mock_data = self._MOCK_DATABASE.get(key)

        if mock_data is None:
            return {
                "approval_status": "UNKNOWN",
                "approval_date": None,
                "approval_reference": None,
                "issuing_authority": None,
                "source": "MockKommuneAdapter",
                "confidence": 0.0,
                "raw_data": {"gnr": gnr, "bnr": bnr, "municipality": municipality, "found": False},
            }

        # Filtrer på dokumenttype hvis angitt
        matching_docs = [
            d for d in mock_data.get("documents", [])
            if document_type.upper() in d["type"].upper()
        ]

        return {
            "approval_status": mock_data["approval_status"],
            "approval_date": mock_data["approval_date"],
            "approval_reference": mock_data["approval_reference"],
            "issuing_authority": mock_data["issuing_authority"],
            "source": "MockKommuneAdapter",
            "confidence": 0.95 if mock_data["approval_status"] == "VERIFIED_APPROVED" else 0.60,
            "matching_documents": matching_docs,
            "raw_data": {
                "gnr": gnr,
                "bnr": bnr,
                "municipality": municipality,
                "document_type": document_type,
                "found": True,
                "mock": True,
            },
        }

    async def fetch_case_history(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
    ) -> list[dict[str, Any]]:
        """Returner mock byggesakshistorikk."""
        await asyncio.sleep(0.05)
        key = f"{gnr}-{bnr}"
        return self._MOCK_CASE_HISTORY.get(key, [])


# =============================================================================
# E-post fallback
# =============================================================================

_EMAIL_TEMPLATE = """
Til: {{ municipality_email }}
Fra: ByggSjekk <noreply@byggsjekk.no>
Emne: Forespørsel om byggesaksopplysninger – gnr {{ gnr }}, bnr {{ bnr }}

Hei,

Vi ber om byggesaksopplysninger for følgende eiendom på vegne av ansvarlig arkitekt:

Eiendom:
  Gårdsnummer (gnr): {{ gnr }}
  Bruksnummer (bnr): {{ bnr }}
  Kommune: {{ municipality }}

Forespurte opplysninger:
  - Godkjente tegninger og tillatelser for eiendommen
  - Ferdigattest eller brukstillatelse
  - Eventuelle dispensasjoner

Saksreferanse (ByggSjekk): {{ case_reference }}
Ansvarlig arkitekt: {{ architect_name }}

Dokumentene kan sendes til: arkiv@byggsjekk.no, merket med saksreferansen over.

Vi ber om svar innen 10 virkedager.

Med vennlig hilsen,
ByggSjekk – Beslutningsstøtte for arkitekter
https://byggsjekk.no

---
Denne e-posten er generert automatisk av ByggSjekk (bygget av Konsepthus AS).
"""


class FallbackEmailAdapter(MunicipalityAdapterInterface):
    """
    Fallback-adapter som genererer e-postutkast for manuell forespørsel til kommunen.

    Brukes når kommunen ikke har digital integrasjon tilgjengelig.
    Returnerer UNKNOWN-status med et ferdig e-postutkast i raw_data.
    """

    # Kjente kommunale e-postadresser for byggesak
    _MUNICIPALITY_EMAILS: dict[str, str] = {
        "Oslo": "postmottak@pbe.oslo.kommune.no",
        "Bergen": "postmottak@bergen.kommune.no",
        "Trondheim": "postmottak@trondheim.kommune.no",
        "Stavanger": "postmottak@stavanger.kommune.no",
        "Kristiansand": "postmottak@kristiansand.kommune.no",
        "Nesodden": "postmottak@nesodden.kommune.no",
        "Tromsø": "postmottak@tromso.kommune.no",
        "Bærum": "postmottak@baerum.kommune.no",
        "Lillestrøm": "postmottak@lillestrom.kommune.no",
        "Drammen": "postmottak@drammen.kommune.no",
    }

    _DEFAULT_EMAIL = "postmottak@kommune.no"

    async def fetch_approval_status(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
        document_type: str,
    ) -> dict[str, Any]:
        """
        Kan ikke hente status automatisk – generer e-postutkast i stedet.
        """
        municipality_email = self._MUNICIPALITY_EMAILS.get(municipality, self._DEFAULT_EMAIL)

        email_body = self._generate_email(
            gnr=gnr,
            bnr=bnr,
            municipality=municipality,
            municipality_email=municipality_email,
            case_reference=f"BS-{gnr}-{bnr}",
            architect_name="[Arkitektens navn]",
        )

        return {
            "approval_status": "UNKNOWN",
            "approval_date": None,
            "approval_reference": None,
            "issuing_authority": None,
            "source": "FallbackEmailAdapter",
            "confidence": 0.0,
            "action_required": "SEND_EMAIL",
            "email_draft": {
                "to": municipality_email,
                "subject": f"Forespørsel om byggesaksopplysninger – gnr {gnr}, bnr {bnr}",
                "body": email_body,
            },
            "raw_data": {
                "gnr": gnr,
                "bnr": bnr,
                "municipality": municipality,
                "adapter": "FallbackEmailAdapter",
                "reason": "Ingen digital kommuneintegrasjon tilgjengelig",
            },
        }

    async def fetch_case_history(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
    ) -> list[dict[str, Any]]:
        """Fallback-adapteren kan ikke hente historikk automatisk."""
        return []

    def _generate_email(self, **kwargs: str) -> str:
        """Generer e-posttekst fra Jinja2-mal."""
        if Template is not None:
            return Template(_EMAIL_TEMPLATE).render(**kwargs)
        # Enkel streng-erstatning som fallback uten Jinja2
        text = _EMAIL_TEMPLATE
        for key, value in kwargs.items():
            text = text.replace("{{ " + key + " }}", value)
        return text


# =============================================================================
# Factory-funksjon
# =============================================================================

def get_municipality_adapter(municipality: str, use_mock: bool = True) -> MunicipalityAdapterInterface:
    """
    Returner riktig adapter basert på konfigurasjon.

    Args:
        municipality: Kommunenavn eller adaptertype ("arealplaner", "dok_analyse", "nesodden")
        use_mock:     True for mock-data (utvikling/testing), False for produksjon

    Returns:
        Instans av passende adapter.
    """
    # Støtte eksplisitt adaptervalg
    adapter_key = municipality.lower().strip()
    if adapter_key in ("arealplaner", "arealplaner_norkart"):
        return ArealplanerAdapter()
    if adapter_key in ("dok_analyse", "dok-analyse", "geodata"):
        return DokAnalyseAdapter()
    if adapter_key in ("nesodden", "nesodden kommune", "3212"):
        return ArealplanerAdapter(municipality_number="3212")

    if use_mock:
        return MockKommuneAdapter()
    # I produksjon: konfigurer basert på om kommunen har eByggesak-integrasjon
    # Her ville vi sjekke en konfig-tabell for støttede kommuner
    return FallbackEmailAdapter()


# =============================================================================
# Pydantic-modeller for Arealplaner og DOK-analyse
# =============================================================================

try:
    from pydantic import BaseModel as _BaseModel, Field as _Field
    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False


class PlanrapportResult:
    """Resultat fra planrapport-forespørsel."""

    def __init__(
        self,
        knr: str,
        gnr: str,
        bnr: str,
        planrapport_url: str | None = None,
        plans: list[dict[str, Any]] | None = None,
        error: str | None = None,
        source: str = "ArealplanerAdapter",
    ) -> None:
        self.knr = knr
        self.gnr = gnr
        self.bnr = bnr
        self.planrapport_url = planrapport_url
        self.plans = plans or []
        self.error = error
        self.source = source

    def to_dict(self) -> dict[str, Any]:
        return {
            "knr": self.knr,
            "gnr": self.gnr,
            "bnr": self.bnr,
            "planrapport_url": self.planrapport_url,
            "plans": self.plans,
            "error": self.error,
            "source": self.source,
        }


class DokAnalyseResult:
    """Resultat fra DOK-analyse-forespørsel."""

    def __init__(
        self,
        knr: str,
        gnr: str,
        bnr: str,
        datasets_touched: list[dict[str, Any]] | None = None,
        datasets_untouched: list[dict[str, Any]] | None = None,
        report_url: str | None = None,
        error: str | None = None,
        source: str = "DokAnalyseAdapter",
    ) -> None:
        self.knr = knr
        self.gnr = gnr
        self.bnr = bnr
        self.datasets_touched = datasets_touched or []
        self.datasets_untouched = datasets_untouched or []
        self.report_url = report_url
        self.error = error
        self.source = source

    def to_dict(self) -> dict[str, Any]:
        return {
            "knr": self.knr,
            "gnr": self.gnr,
            "bnr": self.bnr,
            "datasets_touched": self.datasets_touched,
            "datasets_untouched": self.datasets_untouched,
            "report_url": self.report_url,
            "error": self.error,
            "source": self.source,
        }


class Dispensasjon:
    """Representerer en dispensasjon fra kommunen."""

    def __init__(
        self,
        reference: str,
        description: str,
        status: str,
        granted_date: str | None = None,
        plan_reference: str | None = None,
    ) -> None:
        self.reference = reference
        self.description = description
        self.status = status
        self.granted_date = granted_date
        self.plan_reference = plan_reference

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "description": self.description,
            "status": self.status,
            "granted_date": self.granted_date,
            "plan_reference": self.plan_reference,
        }


class Arealplan:
    """Representerer en arealplan fra kommunen."""

    def __init__(
        self,
        plan_id: str,
        plan_name: str,
        plan_type: str,
        plan_status: str,
        municipality_number: str,
        vedtak_date: str | None = None,
        ikrafttredelse_date: str | None = None,
        url: str | None = None,
    ) -> None:
        self.plan_id = plan_id
        self.plan_name = plan_name
        self.plan_type = plan_type
        self.plan_status = plan_status
        self.municipality_number = municipality_number
        self.vedtak_date = vedtak_date
        self.ikrafttredelse_date = ikrafttredelse_date
        self.url = url

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
            "plan_type": self.plan_type,
            "plan_status": self.plan_status,
            "municipality_number": self.municipality_number,
            "vedtak_date": self.vedtak_date,
            "ikrafttredelse_date": self.ikrafttredelse_date,
            "url": self.url,
        }


# =============================================================================
# ArealplanerAdapter – Norkart arealplaner.no
# =============================================================================

import logging as _logging
_logger = _logging.getLogger(__name__)


class ArealplanerAdapter(MunicipalityAdapterInterface):
    """
    Adapter for Norkart arealplaner.no API.

    Leverer planrapport, DOK-analyse, dispensasjoner og arealplaner per eiendom.
    Støtter API-nøkkel-autentisering (konfigureres via AREALPLANER_API_KEY).
    Faller tilbake til mock-data hvis API-nøkkel ikke er konfigurert.

    Nesodden kommunenummer: 3212
    """

    _AREALPLANER_BASE = "https://api.arealplaner.no/v1"
    _PLANREGISTER_BASE = "https://planregister.arealplaner.no"

    def __init__(self, municipality_number: str | None = None, api_key: str | None = None) -> None:
        self._municipality_number = municipality_number
        self._api_key = api_key

    def _get_api_key(self) -> str | None:
        """Hent API-nøkkel fra konfig eller konstruktørparameter."""
        if self._api_key:
            return self._api_key
        try:
            from app.core.config import settings
            return settings.AREALPLANER_API_KEY or None
        except ImportError:
            import os
            return os.environ.get("AREALPLANER_API_KEY") or None

    def _has_api_key(self) -> bool:
        key = self._get_api_key()
        return bool(key and key.strip())

    async def fetch_approval_status(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
        document_type: str,
    ) -> dict[str, Any]:
        """Hent godkjenningsstatus via arealplaner.no."""
        knr = self._municipality_number or self._resolve_knr(municipality)
        planrapport = await self.fetch_planrapport(knr, gnr, bnr)

        if planrapport.error:
            return {
                "approval_status": "UNKNOWN",
                "approval_date": None,
                "approval_reference": None,
                "issuing_authority": None,
                "source": "ArealplanerAdapter",
                "confidence": 0.0,
                "raw_data": {"error": planrapport.error, "mock": not self._has_api_key()},
            }

        has_plans = len(planrapport.plans) > 0
        return {
            "approval_status": "ASSUMED_APPROVED" if has_plans else "UNKNOWN",
            "approval_date": None,
            "approval_reference": None,
            "issuing_authority": f"Kommunenr. {knr}",
            "source": "ArealplanerAdapter",
            "confidence": 0.70 if has_plans else 0.10,
            "planrapport_url": planrapport.planrapport_url,
            "plans": planrapport.plans,
            "raw_data": {"knr": knr, "gnr": gnr, "bnr": bnr, "mock": not self._has_api_key()},
        }

    async def fetch_case_history(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
    ) -> list[dict[str, Any]]:
        """Hent byggesakshistorikk via arealplaner.no (returnerer planer som historikk)."""
        knr = self._municipality_number or self._resolve_knr(municipality)
        plans = await self.fetch_arealplaner(knr, gnr, bnr)
        return [p.to_dict() for p in plans]

    async def fetch_planrapport(
        self,
        knr: str,
        gnr: str,
        bnr: str,
        fnr: str | None = None,
        snr: str | None = None,
    ) -> PlanrapportResult:
        """
        Hent planrapport for en eiendom fra arealplaner.no.

        Args:
            knr: Kommunenummer (f.eks. "3212" for Nesodden)
            gnr: Gårdsnummer
            bnr: Bruksnummer
            fnr: Festenummer (valgfritt)
            snr: Seksjonsnummer (valgfritt)

        Returns:
            PlanrapportResult med URL og plandata.
        """
        if not self._has_api_key():
            _logger.warning(
                "ArealplanerAdapter: Ingen API-nøkkel konfigurert – returnerer mock-planrapport "
                "for knr=%s gnr=%s bnr=%s", knr, gnr, bnr
            )
            return self._mock_planrapport(knr, gnr, bnr)

        try:
            import httpx
            api_key = self._get_api_key()
            params: dict[str, str] = {
                "kommunenr": knr,
                "gnr": gnr,
                "bnr": bnr,
            }
            if fnr:
                params["fnr"] = fnr
            if snr:
                params["snr"] = snr

            headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self._AREALPLANER_BASE}/planrapport",
                    params=params,
                    headers=headers,
                )

                if resp.status_code == 404:
                    return PlanrapportResult(
                        knr=knr, gnr=gnr, bnr=bnr,
                        error="Ingen planrapport funnet for denne eiendommen.",
                    )

                resp.raise_for_status()
                data = resp.json()

                return PlanrapportResult(
                    knr=knr,
                    gnr=gnr,
                    bnr=bnr,
                    planrapport_url=data.get("rapportUrl") or data.get("url"),
                    plans=data.get("planer") or data.get("plans") or [],
                    source="ArealplanerAdapter",
                )

        except Exception as exc:
            _logger.error(
                "ArealplanerAdapter.fetch_planrapport feilet: %s", exc, exc_info=True
            )
            return PlanrapportResult(
                knr=knr, gnr=gnr, bnr=bnr,
                error=f"Feil ved henting av planrapport: {exc}",
            )

    async def fetch_dok_analyse(
        self,
        knr: str,
        gnr: str,
        bnr: str,
    ) -> DokAnalyseResult:
        """
        Hent DOK-analyse for en eiendom.
        Delegerer til DokAnalyseAdapter.
        """
        adapter = DokAnalyseAdapter()
        return await adapter.fetch_dok_analyse(knr, gnr, bnr)

    async def fetch_dispensasjoner(
        self,
        knr: str,
        gnr: str,
        bnr: str,
    ) -> list[Dispensasjon]:
        """
        Hent dispensasjoner for en eiendom fra arealplaner.no.
        """
        if not self._has_api_key():
            _logger.warning(
                "ArealplanerAdapter: Ingen API-nøkkel – returnerer tom dispensasjonsliste."
            )
            return []

        try:
            import httpx
            api_key = self._get_api_key()
            params = {"kommunenr": knr, "gnr": gnr, "bnr": bnr}
            headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self._AREALPLANER_BASE}/dispensasjoner",
                    params=params,
                    headers=headers,
                )
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                data = resp.json()

                result = []
                for item in (data.get("dispensasjoner") or data if isinstance(data, list) else []):
                    result.append(Dispensasjon(
                        reference=item.get("referanse") or item.get("id") or "ukjent",
                        description=item.get("beskrivelse") or item.get("description") or "",
                        status=item.get("status") or "ukjent",
                        granted_date=item.get("innvilgetDato") or item.get("dato"),
                        plan_reference=item.get("planId") or item.get("planReferanse"),
                    ))
                return result

        except Exception as exc:
            _logger.error("ArealplanerAdapter.fetch_dispensasjoner feilet: %s", exc)
            return []

    async def fetch_arealplaner(
        self,
        knr: str,
        gnr: str,
        bnr: str,
    ) -> list[Arealplan]:
        """
        Hent arealplaner som berører en eiendom.
        """
        if not self._has_api_key():
            _logger.warning(
                "ArealplanerAdapter: Ingen API-nøkkel – returnerer mock-arealplaner."
            )
            return self._mock_arealplaner(knr)

        try:
            import httpx
            api_key = self._get_api_key()
            params = {"kommunenr": knr, "gnr": gnr, "bnr": bnr}
            headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self._AREALPLANER_BASE}/arealplaner",
                    params=params,
                    headers=headers,
                )
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                data = resp.json()

                result = []
                items = data.get("arealplaner") or data if isinstance(data, list) else []
                for item in items:
                    result.append(Arealplan(
                        plan_id=item.get("planId") or item.get("id") or "ukjent",
                        plan_name=item.get("planNavn") or item.get("navn") or "Ukjent plan",
                        plan_type=item.get("planType") or "ukjent",
                        plan_status=item.get("planStatus") or "ukjent",
                        municipality_number=item.get("kommunenr") or knr,
                        vedtak_date=item.get("vedtaksDato"),
                        ikrafttredelse_date=item.get("ikrafttredelseDato"),
                        url=item.get("url"),
                    ))
                return result

        except Exception as exc:
            _logger.error("ArealplanerAdapter.fetch_arealplaner feilet: %s", exc)
            return []

    def _resolve_knr(self, municipality: str) -> str:
        """Slå opp kommunenummer fra kommunenavn."""
        _KNOWN = {
            "nesodden": "3212",
            "oslo": "0301",
            "bergen": "4601",
            "trondheim": "5001",
            "stavanger": "1103",
            "kristiansand": "4204",
            "tromsø": "5401",
        }
        return _KNOWN.get(municipality.lower().strip(), "0000")

    def _mock_planrapport(self, knr: str, gnr: str, bnr: str) -> PlanrapportResult:
        """Generer en realistisk mock-planrapport."""
        planrapport_url = (
            f"https://arealplaner.no/{knr}/planrapport?gnr={gnr}&bnr={bnr}"
        )
        plans = [
            {
                "planId": f"{knr}-R{gnr}{bnr}",
                "planNavn": "Reguleringsplan for boligområde",
                "planType": "Detaljregulering",
                "planStatus": "Gjeldende",
                "vedtaksDato": "2010-06-15",
                "kommunenr": knr,
            }
        ]
        return PlanrapportResult(
            knr=knr,
            gnr=gnr,
            bnr=bnr,
            planrapport_url=planrapport_url,
            plans=plans,
            source="ArealplanerAdapter (mock)",
        )

    def _mock_arealplaner(self, knr: str) -> list[Arealplan]:
        """Generer mock-arealplaner for kommunen."""
        return [
            Arealplan(
                plan_id=f"{knr}-R001",
                plan_name="Reguleringsplan for boligfelt",
                plan_type="Detaljregulering",
                plan_status="Gjeldende",
                municipality_number=knr,
                vedtak_date="2010-06-15",
                ikrafttredelse_date="2010-07-01",
                url=f"https://arealplaner.no/{knr}/plan/{knr}-R001",
            ),
            Arealplan(
                plan_id=f"{knr}-K001",
                plan_name="Kommuneplanens arealdel",
                plan_type="Kommuneplan",
                plan_status="Gjeldende",
                municipality_number=knr,
                vedtak_date="2018-03-20",
                ikrafttredelse_date="2018-04-01",
                url=f"https://arealplaner.no/{knr}/plan/{knr}-K001",
            ),
        ]


# =============================================================================
# DokAnalyseAdapter – Geodata AS DOK-analyse API
# =============================================================================

class DokAnalyseAdapter(MunicipalityAdapterInterface):
    """
    Adapter for Geodata AS DOK-analyse API.

    DOK (Det offentlige kartgrunnlaget) analyse returnerer informasjon om
    hvilke offentlige kartlag som berører en eiendom.

    API: https://dokanalyse.geodataonline.no
    Auth: token query-parameter (konfigureres via GEODATA_TOKEN)

    Endepunkter:
      GET /Query/Matrikkel?knr={knr}&gnr={gnr}&bnr={bnr}&token={token}
      GET /List/Datasets?token={token}&knr={knr}
    """

    _BASE_URL = "https://dokanalyse.geodataonline.no"

    def __init__(self, token: str | None = None) -> None:
        self._token = token

    def _get_token(self) -> str | None:
        if self._token:
            return self._token
        try:
            from app.core.config import settings
            return settings.GEODATA_TOKEN or None
        except ImportError:
            import os
            return os.environ.get("GEODATA_TOKEN") or None

    def _has_token(self) -> bool:
        t = self._get_token()
        return bool(t and t.strip())

    async def fetch_approval_status(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
        document_type: str,
    ) -> dict[str, Any]:
        """DOK-analyseadapteren støtter ikke godkjenningsstatus direkte."""
        return {
            "approval_status": "UNKNOWN",
            "approval_date": None,
            "approval_reference": None,
            "issuing_authority": None,
            "source": "DokAnalyseAdapter",
            "confidence": 0.0,
            "raw_data": {
                "message": "DokAnalyseAdapter støtter ikke godkjenningsstatus – bruk ArealplanerAdapter."
            },
        }

    async def fetch_case_history(
        self,
        gnr: str,
        bnr: str,
        municipality: str,
    ) -> list[dict[str, Any]]:
        """DOK-analyseadapteren returnerer ikke byggesakshistorikk."""
        return []

    async def fetch_dok_analyse(
        self,
        knr: str,
        gnr: str,
        bnr: str,
    ) -> DokAnalyseResult:
        """
        Kjør DOK-analyse for en eiendom.

        Args:
            knr: Kommunenummer
            gnr: Gårdsnummer
            bnr: Bruksnummer

        Returns:
            DokAnalyseResult med berørte og uberørte datasett.
        """
        if not self._has_token():
            _logger.warning(
                "DokAnalyseAdapter: Ingen GEODATA_TOKEN konfigurert – returnerer mock DOK-analyse "
                "for knr=%s gnr=%s bnr=%s", knr, gnr, bnr
            )
            return self._mock_dok_analyse(knr, gnr, bnr)

        try:
            import httpx
            token = self._get_token()
            params = {"knr": knr, "gnr": gnr, "bnr": bnr, "token": token, "reportType": "Url"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self._BASE_URL}/Query/Matrikkel",
                    params=params,
                )

                if resp.status_code == 404:
                    return DokAnalyseResult(
                        knr=knr, gnr=gnr, bnr=bnr,
                        error="Ingen DOK-analyseresultat funnet for denne matrikkelen.",
                    )

                resp.raise_for_status()
                data = resp.json()

                touched = data.get("touched") or data.get("berørte") or []
                untouched = data.get("untouched") or data.get("uberørte") or []
                report_url = data.get("reportUrl") or data.get("rapportUrl")

                return DokAnalyseResult(
                    knr=knr,
                    gnr=gnr,
                    bnr=bnr,
                    datasets_touched=touched,
                    datasets_untouched=untouched,
                    report_url=report_url,
                    source="DokAnalyseAdapter",
                )

        except Exception as exc:
            _logger.error("DokAnalyseAdapter.fetch_dok_analyse feilet: %s", exc, exc_info=True)
            return DokAnalyseResult(
                knr=knr, gnr=gnr, bnr=bnr,
                error=f"Feil ved DOK-analyse: {exc}",
            )

    async def list_datasets(self, knr: str) -> list[dict[str, Any]]:
        """
        List tilgjengelige DOK-datasett for en kommune.

        Args:
            knr: Kommunenummer

        Returns:
            Liste med datasett-metadata.
        """
        if not self._has_token():
            return self._mock_datasets()

        try:
            import httpx
            token = self._get_token()

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self._BASE_URL}/List/Datasets",
                    params={"token": token, "knr": knr},
                )
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, list) else data.get("datasets") or []

        except Exception as exc:
            _logger.error("DokAnalyseAdapter.list_datasets feilet: %s", exc)
            return []

    def _mock_dok_analyse(self, knr: str, gnr: str, bnr: str) -> DokAnalyseResult:
        """Generer realistisk mock DOK-analyse."""
        touched = [
            {
                "datasetId": "NVE_FLOMSONER",
                "datasetName": "NVE Flomsoner",
                "theme": "Naturfare",
                "description": "Eiendommen kan berøre kartlagte flomsoner.",
                "url": "https://kartiskolen.no/nve-flomsoner",
            },
            {
                "datasetId": "RIKSANTIKVAREN_KULTURMINNER",
                "datasetName": "Riksantikvarens kulturminneregister",
                "theme": "Kulturmiljø",
                "description": "Potensielle kulturminner i nærheten.",
                "url": "https://kulturminnesok.no",
            },
        ]
        untouched = [
            {"datasetId": "NVE_SKRED", "datasetName": "NVE Skredfare", "theme": "Naturfare"},
            {"datasetId": "BANE_NOR_JERNBANE", "datasetName": "Bane NOR Jernbane", "theme": "Infrastruktur"},
        ]
        report_url = f"https://dokanalyse.geodataonline.no/rapport/{knr}-{gnr}-{bnr}.pdf"
        return DokAnalyseResult(
            knr=knr,
            gnr=gnr,
            bnr=bnr,
            datasets_touched=touched,
            datasets_untouched=untouched,
            report_url=report_url,
            source="DokAnalyseAdapter (mock)",
        )

    def _mock_datasets(self) -> list[dict[str, Any]]:
        """Generer mock datasett-liste."""
        return [
            {"datasetId": "NVE_FLOMSONER", "datasetName": "NVE Flomsoner", "theme": "Naturfare"},
            {"datasetId": "NVE_SKRED", "datasetName": "NVE Skredfare", "theme": "Naturfare"},
            {"datasetId": "RIKSANTIKVAREN_KULTURMINNER", "datasetName": "Kulturminneregisteret", "theme": "Kulturmiljø"},
            {"datasetId": "MILJODIREKTORATET_NATURTYPER", "datasetName": "Naturtyper", "theme": "Miljø"},
            {"datasetId": "MATTILSYNET_DRIKKEVANN", "datasetName": "Drikkevannskilder", "theme": "Helse"},
        ]
