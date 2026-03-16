"""
ByggSjekk / nops.no – Planslurpen.no adapter.

Planslurpen (DiBK) bruker AI til å konvertere ustrukturerte reguleringsplan-PDF-er
til maskinlesbare planbestemmelser.

Åpent endepunkt (ingen API-nøkkel):
  GET https://planslurpen.no/api/planregister/{kommunenummer}/{gardsnummer}/{bruksnummer}

Returnerer strukturerte planbestemmelser: høydegrenser, utnyttelsesgrad, tillatt bruk, m.m.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(15.0)
PLANSLURPEN_BASE = "https://planslurpen.no/api"


@dataclass
class Planbestemmelse:
    """En enkelt planbestemmelse fra reguleringsplanen."""
    kode: str = ""
    tittel: str = ""
    tekst: str = ""
    verdi: str | None = None  # f.eks. "9.0 m", "40%"
    kategori: str = ""  # f.eks. "HØYDE", "UTNYTTELSE", "BRUK"


@dataclass
class PlanslurpenPlan:
    """Et reguleringsplan-resultat fra Planslurpen."""
    plan_id: str = ""
    plan_navn: str = ""
    kommunenummer: str = ""
    versjon: str = ""
    bestemmelser: list[Planbestemmelse] = field(default_factory=list)
    # Nøkkelverdier ekstrahert for rask tilgang
    maks_hoyde: str | None = None       # f.eks. "9.0 m"
    maks_utnyttelse: str | None = None  # f.eks. "BYA = 30%"
    tillatt_bruk: list[str] = field(default_factory=list)
    plantype: str = ""
    droemmeplan_url: str | None = None
    kilde_url: str = ""
    feilmelding: str | None = None


@dataclass
class PlanslurpenResult:
    """Samlet resultat for en eiendom fra Planslurpen."""
    kommunenummer: str
    gnr: int
    bnr: int
    planer: list[PlanslurpenPlan] = field(default_factory=list)
    antall_planer: int = 0
    feilmelding: str | None = None


def _ekstraher_nokkelverdi(tekst: str, kategori: str) -> str | None:
    """Forsøk å ekstrahere numerisk verdi fra planbestemmelse-tekst."""
    import re
    tekst_lower = tekst.lower()
    if kategori in ("HØYDE", "HOYDE"):
        # Match "9,0 m", "9.0 m", "9 m", "h = 9 m" etc.
        m = re.search(r'(\d+[,.]?\d*)\s*m', tekst_lower)
        if m:
            return f"{m.group(1)} m"
    elif kategori in ("UTNYTTELSE", "BYA", "BRA"):
        # Match "BYA = 30%", "% BYA = 30", "utnyttelsesgrad 40%"
        m = re.search(r'(\d+)\s*%', tekst)
        if m:
            prefix = "BYA" if "bya" in tekst_lower else ("BRA" if "bra" in tekst_lower else "u-grad")
            return f"{prefix} = {m.group(1)}%"
    return None


def _kategoriser_bestemmelse(kode: str, tittel: str) -> str:
    """Bestem kategori fra kode/tittel."""
    k = (kode + " " + tittel).lower()
    if any(x in k for x in ["høyde", "hoyde", "gesims", "møneh"]):
        return "HØYDE"
    if any(x in k for x in ["utnyttelse", "bya", "bra", "%"]):
        return "UTNYTTELSE"
    if any(x in k for x in ["bruk", "formål", "arealformål"]):
        return "BRUK"
    if any(x in k for x in ["parkering", "garasje"]):
        return "PARKERING"
    if any(x in k for x in ["avstand", "nabogrense", "byggegrense"]):
        return "AVSTAND"
    return "ANNET"


def _parse_planslurpen_response(data: Any, knr: str, gnr: int, bnr: int) -> PlanslurpenResult:
    """Parser Planslurpen API-respons til PlanslurpenResult."""
    result = PlanslurpenResult(kommunenummer=knr, gnr=gnr, bnr=bnr)

    if not data:
        result.feilmelding = "Ingen plandata funnet"
        return result

    # Response kan være en liste av planer eller et enkelt objekt
    planer_raw = data if isinstance(data, list) else [data]

    for plan_raw in planer_raw:
        if not isinstance(plan_raw, dict):
            continue

        plan = PlanslurpenPlan(
            plan_id=str(plan_raw.get("planId") or plan_raw.get("plan_id") or ""),
            plan_navn=str(plan_raw.get("planNavn") or plan_raw.get("plan_navn") or plan_raw.get("navn") or ""),
            kommunenummer=knr,
            versjon=str(plan_raw.get("versjon") or ""),
            plantype=str(plan_raw.get("planType") or plan_raw.get("plantype") or ""),
            kilde_url=f"https://planslurpen.no/api/planregister/{knr}/{gnr}/{bnr}",
        )

        # Drømmeplan-lenke
        if plan.plan_id:
            plan.droemmeplan_url = f"https://droemmeplan.no/{knr}/{plan.plan_id}"

        # Bestemmelser
        bestemmelser_raw = (
            plan_raw.get("bestemmelser") or
            plan_raw.get("planbestemmelser") or
            plan_raw.get("provisions") or
            plan_raw.get("items") or
            []
        )

        maks_hoyde = None
        maks_utnyttelse = None
        tillatt_bruk: list[str] = []

        for b_raw in (bestemmelser_raw if isinstance(bestemmelser_raw, list) else []):
            if not isinstance(b_raw, dict):
                continue
            kode = str(b_raw.get("kode") or b_raw.get("code") or "")
            tittel = str(b_raw.get("tittel") or b_raw.get("title") or b_raw.get("navn") or "")
            tekst = str(b_raw.get("tekst") or b_raw.get("text") or b_raw.get("beskrivelse") or "")
            verdi = str(b_raw.get("verdi") or b_raw.get("value") or "")

            kategori = _kategoriser_bestemmelse(kode, tittel)
            ekst_verdi = _ekstraher_nokkelverdi(tekst, kategori) or (verdi if verdi else None)

            best = Planbestemmelse(
                kode=kode,
                tittel=tittel,
                tekst=tekst,
                verdi=ekst_verdi,
                kategori=kategori,
            )
            plan.bestemmelser.append(best)

            # Oppdater nøkkelverdier
            if kategori == "HØYDE" and not maks_hoyde:
                maks_hoyde = ekst_verdi
            elif kategori == "UTNYTTELSE" and not maks_utnyttelse:
                maks_utnyttelse = ekst_verdi
            elif kategori == "BRUK" and tekst:
                tillatt_bruk.append(tittel or tekst[:60])

        # Sjekk også top-level felter
        if not maks_hoyde:
            for key in ["maksHoyde", "maks_hoyde", "maxHeight", "gesimshøyde"]:
                if plan_raw.get(key):
                    maks_hoyde = str(plan_raw[key])
                    break

        if not maks_utnyttelse:
            for key in ["utnyttelse", "bya", "BYA", "utnyttelsesgrad"]:
                if plan_raw.get(key):
                    maks_utnyttelse = f"BYA = {plan_raw[key]}"
                    break

        plan.maks_hoyde = maks_hoyde
        plan.maks_utnyttelse = maks_utnyttelse
        plan.tillatt_bruk = tillatt_bruk[:5]  # maks 5

        result.planer.append(plan)

    result.antall_planer = len(result.planer)
    if result.antall_planer == 0:
        result.feilmelding = "Ingen reguleringsplaner med strukturerte bestemmelser funnet i Planslurpen"

    return result


class PlanslurpenAdapter:
    """Adapter for Planslurpen.no planbestemmelse-API."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=TIMEOUT)

    async def hent_planbestemmelser(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int = 0,
        snr: int = 0,
    ) -> PlanslurpenResult:
        """
        Henter strukturerte planbestemmelser for en eiendom fra Planslurpen.

        Åpent endepunkt – ingen API-nøkkel nødvendig.
        """
        result = PlanslurpenResult(kommunenummer=kommunenummer, gnr=gnr, bnr=bnr)
        try:
            url = f"{PLANSLURPEN_BASE}/planregister/{kommunenummer}/{gnr}/{bnr}"
            params: dict = {}
            if fnr:
                params["festenummer"] = fnr
            if snr:
                params["seksjonsnummer"] = snr

            headers = {
                "Accept": "application/json",
                "User-Agent": "ByggSjekk/nops.no property-intelligence",
            }

            resp = await self._client.get(url, params=params, headers=headers)

            if resp.status_code == 404:
                result.feilmelding = "Eiendom ikke funnet i Planslurpen. Planen er kanskje ikke klarspråket ennå."
                return result
            if resp.status_code == 204:
                result.feilmelding = "Ingen planbestemmelser tilgjengelig for denne eiendommen i Planslurpen."
                return result
            if resp.status_code != 200:
                result.feilmelding = f"Planslurpen utilgjengelig (HTTP {resp.status_code})"
                return result

            data = resp.json()
            return _parse_planslurpen_response(data, kommunenummer, gnr, bnr)

        except httpx.TimeoutException:
            result.feilmelding = "Planslurpen svarte ikke innen tidsfristen"
        except Exception as exc:
            logger.warning("Planslurpen-oppslag feilet: %s", exc)
            result.feilmelding = f"Planslurpen-oppslag feilet: {exc}"

        return result


_adapter_instance: PlanslurpenAdapter | None = None


def get_planslurpen_adapter() -> PlanslurpenAdapter:
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = PlanslurpenAdapter()
    return _adapter_instance
