"""
ByggSjekk – Arealplaner og DOK-analyse integrasjon.

Integrerer med:
1. DOK-analyse API (Geodata AS) – https://dokanalyse.geodataonline.no
   - Analyserer eiendom mot det offentlige kartgrunnlaget (DOK)
   - Returnerer berørte datasett og PDF-rapport
   - Krever API-token fra Geodata AS

2. Arealplaner.no (Norkart) – https://www.arealplaner.no
   - Tilgang til kommunale arealplaner og dispensasjoner
   - Planrapport per eiendom
   - Krever Norkart API-avtale

Spesifikk støtte for Nesodden kommune (kommunenummer 3212).

MERK: Alle data er beslutningsstøtte. Arkitekten er alltid siste kontrollinstans.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Datamodeller
# ---------------------------------------------------------------------------


@dataclass
class Arealplan:
    """Representerer én arealplan fra kommunens planregister."""
    plan_id: str
    plan_navn: str
    plan_type: str           # "reguleringsplan", "kommuneplan", "bebyggelsesplan"
    status: str              # "gjeldende", "under_behandling", "opphevet"
    vedtaksdato: str | None = None
    arealformål: str | None = None
    norkart_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Dispensasjon:
    """Representerer én dispensasjon fra kommunens arkiv."""
    saks_id: str
    saks_type: str           # "dispensasjon_fra_plan", "dispensasjon_fra_lov"
    status: str = ""         # "innvilget", "avslatt", "under_behandling"
    vedtaksdato: str | None = None
    beskrivelse: str | None = None
    paragraf: str | None = None  # PBL-paragraf det er dispensert fra
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DokDataset:
    """Ett DOK-datasett som er berørt av eiendommen."""
    uuid: str = ""
    navn: str = ""
    tema: str = ""
    status: str = ""         # "berørt", "ikke_berørt", "mangler"
    detaljer: dict[str, Any] = field(default_factory=dict)
    url: str | None = None


@dataclass
class DokAnalyseResult:
    """Komplett DOK-analyse for én eiendom."""
    kommunenummer: str
    gnr: int
    bnr: int
    berørte_datasett: list[DokDataset] = field(default_factory=list)
    ikke_berørte_datasett: list[DokDataset] = field(default_factory=list)
    manglende_datasett: list[DokDataset] = field(default_factory=list)
    rapport_url: str | None = None    # URL til PDF-rapport
    feilmelding: str | None = None
    kilde: str = "dok_analyse_api"


@dataclass
class PlanrapportResult:
    """Planrapport for én eiendom fra arealplaner.no."""
    kommunenummer: str
    gnr: int
    bnr: int
    gjeldende_planer: list[Arealplan] = field(default_factory=list)
    dispensasjoner: list[Dispensasjon] = field(default_factory=list)
    planrapport_url: str | None = None
    feilmelding: str | None = None
    kilde: str = "arealplaner_no"


@dataclass
class EiendomsoppslagResult:
    """Komplett eiendomsoppslag – kombinerer DOK-analyse og planrapport."""
    kommunenummer: str
    gnr: int
    bnr: int
    fnr: int | None = None
    snr: int | None = None
    dok_analyse: DokAnalyseResult | None = None
    planrapport: PlanrapportResult | None = None
    feilmeldinger: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DOK-analyse adapter (Geodata AS)
# ---------------------------------------------------------------------------


class DokAnalyseAdapter:
    """
    Klient for DOK-analyse API fra Geodata AS.

    API: https://dokanalyse.geodataonline.no
    Swagger: https://dokanalyse.geodataonline.no/swagger/v1/swagger.json

    Endepunkter brukt:
    - GET /Query/Matrikkel – analyser eiendom via gnr/bnr
    - GET /List/Datasets   – liste tilgjengelige DOK-datasett
    """

    BASE_URL = "https://dokanalyse.geodataonline.no"

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.getenv("GEODATA_TOKEN", "")

    async def analyse_eiendom(
        self,
        knr: str,
        gnr: int,
        bnr: int,
        fnr: int | None = None,
        snr: int | None = None,
        include_rapport: bool = True,
    ) -> DokAnalyseResult:
        """
        Kjør DOK-analyse for en eiendom via matrikkelreferanse.

        Args:
            knr:            Kommunenummer (f.eks. "3212" for Nesodden)
            gnr:            Gårdsnummer
            bnr:            Bruksnummer
            fnr:            Festenummer (valgfritt)
            snr:            Seksjonsnummer (valgfritt)
            include_rapport: Inkluder PDF-rapport-URL i svaret

        Returns:
            DokAnalyseResult med alle berørte datasett
        """
        if not self._token:
            logger.warning("GEODATA_TOKEN ikke satt – returnerer tom DOK-analyse")
            return DokAnalyseResult(
                kommunenummer=knr,
                gnr=gnr,
                bnr=bnr,
                feilmelding="API-token for DOK-analyse (GEODATA_TOKEN) er ikke konfigurert.",
                kilde="dok_analyse_api",
            )

        try:
            import httpx
        except ImportError:
            return DokAnalyseResult(
                kommunenummer=knr, gnr=gnr, bnr=bnr,
                feilmelding="httpx-biblioteket er ikke installert.",
            )

        params: dict[str, Any] = {
            "token": self._token,
            "knr": knr,
            "gnr": gnr,
            "bnr": bnr,
        }
        if fnr is not None:
            params["fnr"] = fnr
        if snr is not None:
            params["snr"] = snr
        if include_rapport:
            params["reportType"] = 1  # ReportType.Url

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/Query/Matrikkel",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("DOK-analyse HTTP-feil %d: %s", exc.response.status_code, exc)
            return DokAnalyseResult(
                kommunenummer=knr, gnr=gnr, bnr=bnr,
                feilmelding=f"DOK-analyse API returnerte feil: {exc.response.status_code}",
            )
        except Exception as exc:
            logger.error("DOK-analyse feilet: %s", exc)
            return DokAnalyseResult(
                kommunenummer=knr, gnr=gnr, bnr=bnr,
                feilmelding=f"Kunne ikke kontakte DOK-analyse API: {exc}",
            )

        return self._parse_response(data, knr, gnr, bnr)

    async def list_datasett(self, knr: str) -> list[DokDataset]:
        """Henter liste over tilgjengelige DOK-datasett for en kommune."""
        if not self._token:
            return []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/List/Datasets",
                    params={"token": self._token, "knr": knr},
                )
                response.raise_for_status()
                data = response.json()
                return [
                    DokDataset(
                        uuid=item.get("uuid", ""),
                        navn=item.get("name", item.get("navn", "")),
                        tema=item.get("theme", item.get("tema", "")),
                        status="tilgjengelig",
                    )
                    for item in (data if isinstance(data, list) else [])
                ]
        except Exception as exc:
            logger.warning("Kunne ikke hente DOK-datasett: %s", exc)
            return []

    def _parse_response(
        self, data: dict, knr: str, gnr: int, bnr: int
    ) -> DokAnalyseResult:
        """Parser API-svar til DokAnalyseResult."""
        berørte: list[DokDataset] = []
        ikke_berørte: list[DokDataset] = []
        manglende: list[DokDataset] = []

        for item in data.get("touchedDatasets", []):
            berørte.append(DokDataset(
                uuid=item.get("uuid", ""),
                navn=item.get("name", ""),
                tema=item.get("theme", ""),
                status="berørt",
                detaljer=item,
                url=item.get("url"),
            ))

        for item in data.get("untouchedDatasets", []):
            ikke_berørte.append(DokDataset(
                uuid=item.get("uuid", ""),
                navn=item.get("name", ""),
                tema=item.get("theme", ""),
                status="ikke_berørt",
                detaljer=item,
            ))

        for item in data.get("missingDatasets", []):
            manglende.append(DokDataset(
                uuid=item.get("uuid", ""),
                navn=item.get("name", ""),
                tema=item.get("theme", ""),
                status="mangler",
                detaljer=item,
            ))

        rapport_url = data.get("reportUrl") or data.get("rapport_url")

        return DokAnalyseResult(
            kommunenummer=knr,
            gnr=gnr,
            bnr=bnr,
            berørte_datasett=berørte,
            ikke_berørte_datasett=ikke_berørte,
            manglende_datasett=manglende,
            rapport_url=rapport_url,
            kilde="dok_analyse_api",
        )


# ---------------------------------------------------------------------------
# Arealplaner.no adapter (Norkart)
# ---------------------------------------------------------------------------


class ArealplanerAdapter:
    """
    Klient for arealplaner.no (Norkart).

    Tilbyr planrapport og dispensasjonsoversikt per eiendom.

    MERK: Arealplaner.no er en JavaScript-SPA uten offentlig dokumentert REST-API.
    Denne adapteren bruker Norkarts private API (krever avtale/API-nøkkel).
    Faller tilbake til mock-data hvis nøkkel ikke er konfigurert.

    Kontakt: norkart.no for API-tilgang.
    """

    # Kjente kommunenummer-til-slug-mapping
    _MUNICIPALITY_SLUGS: dict[str, str] = {
        "3212": "nesodden3212",
        "0301": "oslo0301",
        "1201": "bergen1201",
        "5001": "trondheim5001",
        "1103": "stavanger1103",
        "3207": "frogn3207",
        "3213": "as3213",
    }

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("AREALPLANER_API_KEY", "")
        self._base_url = os.getenv(
            "AREALPLANER_BASE_URL", "https://www.arealplaner.no/api"
        )

    async def hent_planrapport(
        self,
        knr: str,
        gnr: int,
        bnr: int,
        fnr: int | None = None,
        snr: int | None = None,
    ) -> PlanrapportResult:
        """
        Henter planrapport og dispensasjoner for en eiendom.

        Hvis API-nøkkel ikke er konfigurert, returneres mock-data
        med Nesodden-spesifikke eksempler.
        """
        if not self._api_key:
            logger.info("AREALPLANER_API_KEY ikke satt – returnerer mock planrapport")
            return self._mock_planrapport(knr, gnr, bnr)

        try:
            import httpx
        except ImportError:
            return PlanrapportResult(
                kommunenummer=knr, gnr=gnr, bnr=bnr,
                feilmelding="httpx er ikke installert.",
            )

        try:
            slug = self._MUNICIPALITY_SLUGS.get(knr, f"kommune{knr}")
            async with httpx.AsyncClient(
                timeout=20.0,
                headers={"Authorization": f"Bearer {self._api_key}"},
            ) as client:
                # Hent gjeldende planer
                planer_resp = await client.get(
                    f"{self._base_url}/v1/arealplan",
                    params={"kommunenummer": knr, "gnr": gnr, "bnr": bnr},
                )
                planer_resp.raise_for_status()
                planer_data = planer_resp.json()

                # Hent dispensasjoner
                disp_resp = await client.get(
                    f"{self._base_url}/v1/dispensasjon",
                    params={"kommunenummer": knr, "gnr": gnr, "bnr": bnr},
                )
                disp_resp.raise_for_status()
                disp_data = disp_resp.json()

            planer = self._parse_planer(planer_data)
            dispensasjoner = self._parse_dispensasjoner(disp_data)

            return PlanrapportResult(
                kommunenummer=knr,
                gnr=gnr,
                bnr=bnr,
                gjeldende_planer=planer,
                dispensasjoner=dispensasjoner,
                planrapport_url=(
                    f"https://www.arealplaner.no/{slug}/arealplaner?"
                    f"gnr={gnr}&bnr={bnr}"
                ),
                kilde="arealplaner_no",
            )

        except Exception as exc:
            logger.error("Arealplaner.no API-feil: %s", exc)
            return PlanrapportResult(
                kommunenummer=knr, gnr=gnr, bnr=bnr,
                feilmelding=f"Kunne ikke hente planrapport: {exc}",
            )

    def _parse_planer(self, data: Any) -> list[Arealplan]:
        """Parser arealplandata fra API-svar."""
        items = data if isinstance(data, list) else data.get("items", [])
        return [
            Arealplan(
                plan_id=item.get("planId", item.get("id", "")),
                plan_navn=item.get("planNavn", item.get("name", "")),
                plan_type=item.get("planType", "reguleringsplan"),
                status=item.get("status", "gjeldende"),
                vedtaksdato=item.get("vedtaksdato"),
                arealformål=item.get("arealformål"),
                norkart_url=item.get("url"),
                metadata=item,
            )
            for item in items
        ]

    def _parse_dispensasjoner(self, data: Any) -> list[Dispensasjon]:
        """Parser dispensasjonsdata fra API-svar."""
        items = data if isinstance(data, list) else data.get("items", [])
        return [
            Dispensasjon(
                saks_id=item.get("sakId", item.get("id", "")),
                saks_type=item.get("sakType", "dispensasjon_fra_plan"),
                vedtaksdato=item.get("vedtaksdato"),
                status=item.get("status", ""),
                beskrivelse=item.get("beskrivelse"),
                paragraf=item.get("paragraf"),
                metadata=item,
            )
            for item in items
        ]

    def _mock_planrapport(self, knr: str, gnr: int, bnr: int) -> PlanrapportResult:
        """Returnerer realistiske mock-data (nyttig for Nesodden)."""
        is_nesodden = knr == "3212"
        slug = self._MUNICIPALITY_SLUGS.get(knr, f"kommune{knr}")

        mock_planer = [
            Arealplan(
                plan_id=f"R{gnr:03d}-{bnr:04d}" if is_nesodden else f"PLAN-MOCK-01",
                plan_navn="Reguleringsplan for Nesoddtangen" if is_nesodden else "Reguleringsplan (mock)",
                plan_type="reguleringsplan",
                status="gjeldende",
                vedtaksdato="2018-05-14" if is_nesodden else "2015-01-01",
                arealformål="Boligbebyggelse – frittliggende",
                norkart_url=f"https://www.arealplaner.no/{slug}/arealplaner",
            ),
            Arealplan(
                plan_id="KP-2019",
                plan_navn=f"Kommuneplan for {'Nesodden' if is_nesodden else 'kommunen'} 2019–2031",
                plan_type="kommuneplanens_arealdel",
                status="gjeldende",
                vedtaksdato="2019-09-25" if is_nesodden else "2019-01-01",
                arealformål="Boligbebyggelse",
                norkart_url=f"https://www.arealplaner.no/{slug}/arealplaner",
            ),
        ]

        mock_dispensasjoner: list[Dispensasjon] = []
        if is_nesodden and gnr % 3 == 0:  # Simuler at noen eiendommer har dispensasjoner
            mock_dispensasjoner.append(
                Dispensasjon(
                    saks_id=f"DISP/{gnr}/{bnr}/2020",
                    saks_type="dispensasjon_fra_plan",
                    vedtaksdato="2020-03-12",
                    status="innvilget",
                    beskrivelse="Dispensasjon fra avstandskrav til sjø – oppføring av naustplass",
                    paragraf="PBL § 19-2",
                )
            )

        return PlanrapportResult(
            kommunenummer=knr,
            gnr=gnr,
            bnr=bnr,
            gjeldende_planer=mock_planer,
            dispensasjoner=mock_dispensasjoner,
            planrapport_url=(
                f"https://www.arealplaner.no/{slug}/arealplaner?gnr={gnr}&bnr={bnr}"
            ),
            feilmelding=(
                "Mock-data returnert (AREALPLANER_API_KEY ikke konfigurert). "
                "Kontakt Norkart for API-tilgang til arealplaner.no."
            ),
            kilde="arealplaner_mock",
        )


# ---------------------------------------------------------------------------
# Nesodden-spesifikk adapter
# ---------------------------------------------------------------------------


class NesoddenAdapter:
    """
    Spesialisert adapter for Nesodden kommune (kommunenummer 3212).

    Kombinerer DOK-analyse og arealplaner.no for komplett eiendomsoppslag.
    """

    KOMMUNENUMMER = "3212"
    KOMMUNE_EMAIL = "postmottak@nesodden.kommune.no"
    KOMMUNE_NAVN = "Nesodden"

    def __init__(
        self,
        geodata_token: str | None = None,
        arealplaner_api_key: str | None = None,
    ) -> None:
        self._dok = DokAnalyseAdapter(token=geodata_token)
        self._arealplaner = ArealplanerAdapter(api_key=arealplaner_api_key)

    async def full_eiendomsoppslag(
        self,
        gnr: int,
        bnr: int,
        fnr: int | None = None,
        snr: int | None = None,
    ) -> EiendomsoppslagResult:
        """
        Komplett eiendomsoppslag for Nesodden:
        - DOK-analyse (kartgrunnlag)
        - Planrapport + dispensasjoner

        Args:
            gnr: Gårdsnummer
            bnr: Bruksnummer
            fnr: Festenummer (valgfritt)
            snr: Seksjonsnummer (valgfritt)

        Returns:
            EiendomsoppslagResult med alle tilgjengelige data
        """
        knr = self.KOMMUNENUMMER
        result = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr, fnr=fnr, snr=snr)

        # Kjør parallelt
        import asyncio
        dok_task = asyncio.create_task(
            self._dok.analyse_eiendom(knr, gnr, bnr, fnr, snr)
        )
        plan_task = asyncio.create_task(
            self._arealplaner.hent_planrapport(knr, gnr, bnr, fnr, snr)
        )

        dok_result, plan_result = await asyncio.gather(dok_task, plan_task, return_exceptions=True)

        if isinstance(dok_result, Exception):
            result.feilmeldinger.append(f"DOK-analyse: {dok_result}")
        else:
            result.dok_analyse = dok_result
            if dok_result.feilmelding:
                result.feilmeldinger.append(f"DOK-analyse: {dok_result.feilmelding}")

        if isinstance(plan_result, Exception):
            result.feilmeldinger.append(f"Planrapport: {plan_result}")
        else:
            result.planrapport = plan_result
            if plan_result.feilmelding:
                result.feilmeldinger.append(f"Planrapport: {plan_result.feilmelding}")

        return result


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_nesodden_adapter() -> NesoddenAdapter:
    """Returnerer Nesodden-adapter med miljøvariabler."""
    return NesoddenAdapter(
        geodata_token=os.getenv("GEODATA_TOKEN"),
        arealplaner_api_key=os.getenv("AREALPLANER_API_KEY"),
    )


def get_dok_adapter() -> DokAnalyseAdapter:
    """Returnerer DOK-analyse adapter."""
    return DokAnalyseAdapter(token=os.getenv("GEODATA_TOKEN"))


def get_arealplaner_adapter() -> ArealplanerAdapter:
    """Returnerer arealplaner.no adapter."""
    return ArealplanerAdapter(api_key=os.getenv("AREALPLANER_API_KEY"))
