"""
ByggSjekk / nops.no – Eiendomsdata og historikk.

Henter eiendomsdata fra offentlig tilgjengelige kilder:
- Geonorge / Kartverket – matrikkelen, koordinater, arealer
- SSB – statistikk om boligmarked per kommune
- Eiendomsverdi – verdsettelse (simulert basert på offentlig data)
- Norsk Eiendomsmeglerforbund / Ambita – historikk (via offentlige data)

MERK: For fullstendig eiendomsomsetningshistorikk kreves avtale med Ambita/Eiendomsverdi.
Denne modulen bruker kun offentlig tilgjengelige data.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(15.0)

# ---------------------------------------------------------------------------
# SSB statistikk URL (åpent API)
# ---------------------------------------------------------------------------

SSB_API = "https://data.ssb.no/api/v0/no/table"


# ---------------------------------------------------------------------------
# Dataklasser
# ---------------------------------------------------------------------------


@dataclass
class EiendomsHistorikkData:
    """Samlet historikkdata for en eiendom."""

    kommunenummer: str
    gnr: int
    bnr: int

    # Boligstatistikk for kommunen
    kommune_median_pris: float | None = None
    kommune_prisvekst_prosent: float | None = None
    kommune_omsatte_boliger: int | None = None
    statistikk_aar: int | None = None

    # Eiendomsinformasjon
    eiendomstype: str = ""
    tomteareal: float | None = None
    byggeaar: int | None = None

    # Estimert verdi (enkel modell basert på offentlige data)
    estimert_verdi: float | None = None
    estimat_konfidensintervall: tuple[float, float] | None = None
    estimat_metode: str = "Kommunebasert statistikk"

    # Nøkkeltall
    pris_per_kvm: float | None = None
    boligtype: str = ""

    feilmeldinger: list[str] = field(default_factory=list)


@dataclass
class NaboEiendom:
    """Nabo-eiendom info."""

    gnr: int
    bnr: int
    avstand_meter: float | None = None
    adresse: str = ""


@dataclass
class NaboAnalyse:
    """Naboanalyse for en eiendom."""

    kommunenummer: str
    gnr: int
    bnr: int
    naboer: list[NaboEiendom] = field(default_factory=list)
    antall_naboer: int = 0
    feilmelding: str | None = None


# ---------------------------------------------------------------------------
# SSB kommunestatistikk
# ---------------------------------------------------------------------------


# Gjennomsnittlig boligpris per kvm i noen norske kommuner
# Basert på SSB/Eiendomsverdi statistikk 2023/2024
# Dette er estimater for illustrasjon - i produksjon bør live API brukes
_KOMMUNE_STATISTIKK: dict[str, dict[str, Any]] = {
    "0301": {  # Oslo
        "navn": "Oslo",
        "median_kvm_pris": 80000,
        "prisvekst_5aar": 0.15,
        "median_total_pris": 5000000,
    },
    "3201": {  # Bærum
        "navn": "Bærum",
        "median_kvm_pris": 65000,
        "prisvekst_5aar": 0.12,
        "median_total_pris": 6500000,
    },
    "3203": {  # Asker
        "navn": "Asker",
        "median_kvm_pris": 50000,
        "prisvekst_5aar": 0.10,
        "median_total_pris": 5500000,
    },
    "3212": {  # Nesodden
        "navn": "Nesodden",
        "median_kvm_pris": 45000,
        "prisvekst_5aar": 0.18,
        "median_total_pris": 5200000,
    },
    "3214": {  # Ås
        "navn": "Ås",
        "median_kvm_pris": 38000,
        "prisvekst_5aar": 0.14,
        "median_total_pris": 4800000,
    },
    "4601": {  # Bergen
        "navn": "Bergen",
        "median_kvm_pris": 45000,
        "prisvekst_5aar": 0.11,
        "median_total_pris": 4200000,
    },
    "5001": {  # Trondheim
        "navn": "Trondheim",
        "median_kvm_pris": 40000,
        "prisvekst_5aar": 0.09,
        "median_total_pris": 3800000,
    },
    "1103": {  # Stavanger
        "navn": "Stavanger",
        "median_kvm_pris": 35000,
        "prisvekst_5aar": 0.05,
        "median_total_pris": 3600000,
    },
}

# Landsgjennomsnitt
_NASJONAL_MEDIAN_KVM = 35000


def _hent_kommune_statistikk(kommunenummer: str) -> dict[str, Any] | None:
    """Henter lokal statistikk for en kommune."""
    return _KOMMUNE_STATISTIKK.get(kommunenummer)


# ---------------------------------------------------------------------------
# SSB live boligprisdata (tabell 06035)
# ---------------------------------------------------------------------------

_SSB_CACHE: dict[str, tuple[dict, float]] = {}
_SSB_CACHE_TTL = 86400.0  # 24 timer


async def hent_ssb_boligpriser(
    kommunenummer: str, client: httpx.AsyncClient
) -> dict[str, Any] | None:
    """
    Henter live kvadratmeterpriser fra SSB tabell 06035
    ("Betalte kvadratmeterpriser, etter boligtype og region").

    Returnerer {"median_kvm_pris": float, "statistikk_aar": int} eller None ved feil.
    """
    # Sjekk cache
    if kommunenummer in _SSB_CACHE:
        cached_data, cached_time = _SSB_CACHE[kommunenummer]
        if time.time() - cached_time < _SSB_CACHE_TTL:
            return cached_data

    url = "https://data.ssb.no/api/v0/no/table/06035"
    payload = {
        "query": [
            {"code": "Region", "selection": {"filter": "item", "values": [kommunenummer]}},
            {"code": "Boligtype", "selection": {"filter": "item", "values": ["00"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["KvPris"]}},
            {"code": "Tid", "selection": {"filter": "top", "values": ["1"]}},
        ],
        "response": {"format": "json-stat2"},
    }

    try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        verdi = data["value"][0]
        if verdi is None:
            return None

        # Hent årstall fra tidsdimensjonen
        tid_kategori = data.get("dimension", {}).get("Tid", {}).get("category", {})
        tid_labels = list(tid_kategori.get("label", {}).values())
        aar_str = tid_labels[0] if tid_labels else ""
        # Årstall kan være "2023" eller "2023K4" – ta første 4 siffer
        aar = int(aar_str[:4]) if aar_str and aar_str[:4].isdigit() else None

        result: dict[str, Any] = {"median_kvm_pris": float(verdi)}
        if aar is not None:
            result["statistikk_aar"] = aar

        _SSB_CACHE[kommunenummer] = (result, time.time())
        logger.info("SSB boligpris hentet for kommune %s: %s kr/m²", kommunenummer, verdi)
        return result

    except Exception as exc:
        logger.debug("Kunne ikke hente SSB boligpris for %s: %s", kommunenummer, exc)
        return None


# ---------------------------------------------------------------------------
# Verdiestimatmodell
# ---------------------------------------------------------------------------


def estimer_eiendomsverdi(
    kommunenummer: str,
    byggeaar: int | None,
    bruksareal: float | None,
    tomteareal: float | None,
    bygningstype: str,
) -> tuple[float | None, tuple[float, float] | None, str]:
    """
    Estimerer eiendomsverdi basert på offentlig statistikk.

    Returnerer: (estimert_verdi, konfidensintervall, metode)

    MERK: Dette er et grovt estimat. For nøyaktig verdsetting anbefales
    faglig takst eller data fra Eiendomsverdi AS.
    """
    statistikk = _hent_kommune_statistikk(kommunenummer)
    kvm_pris = (statistikk or {}).get("median_kvm_pris") or _NASJONAL_MEDIAN_KVM

    if bruksareal is None or bruksareal <= 0:
        if statistikk:
            base = statistikk.get("median_total_pris")
            if base:
                return (base, (base * 0.8, base * 1.2), "Kommunemedian (areal ukjent)")
        return (None, None, "Utilstrekkelig data")

    # Juster for alder
    alder_faktor = 1.0
    if byggeaar:
        alder = 2024 - byggeaar
        if alder < 10:
            alder_faktor = 1.05
        elif alder < 30:
            alder_faktor = 1.0
        elif alder < 60:
            alder_faktor = 0.90
        else:
            alder_faktor = 0.80

    # Juster for bygningstype
    type_faktor = 1.0
    bt = bygningstype.lower()
    if "leilighet" in bt or "blokk" in bt:
        type_faktor = 0.95
    elif "enebolig" in bt:
        type_faktor = 1.05
    elif "tomannsbolig" in bt or "rekkehus" in bt:
        type_faktor = 1.0

    # Tomtefaktor (relevant for enebolig)
    tomt_bonus = 0.0
    if tomteareal and "enebolig" in bt:
        if tomteareal > 1000:
            tomt_bonus = 300000
        elif tomteareal > 500:
            tomt_bonus = 150000

    estimat = (bruksareal * kvm_pris * alder_faktor * type_faktor) + tomt_bonus

    # ±25% konfidensintervall
    margin = estimat * 0.25
    konfidensintervall = (estimat - margin, estimat + margin)

    return (
        round(estimat / 1000) * 1000,
        (round(konfidensintervall[0] / 1000) * 1000, round(konfidensintervall[1] / 1000) * 1000),
        f"BRA {bruksareal:.0f}m² × {kvm_pris:,}/m² (kommunestatistikk)"
    )


# ---------------------------------------------------------------------------
# Komplett eiendomsdata-adapter
# ---------------------------------------------------------------------------


class EiendomsdataAdapter:
    """
    Henter og kombinerer eiendomsdata fra alle tilgjengelige offentlige kilder.
    """

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=TIMEOUT)

    async def hent_historikk(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        bygninger: list[dict[str, Any]] | None = None,
        eiendom: dict[str, Any] | None = None,
    ) -> EiendomsHistorikkData:
        """
        Bygger et komplett eiendomsdataset.

        Kombinerer:
        - Kartverket-data (bygninger, areal)
        - Lokal kommunestatistikk
        - Estimert verdi
        """
        result = EiendomsHistorikkData(
            kommunenummer=kommunenummer,
            gnr=gnr,
            bnr=bnr,
        )

        # Hent kommunestatistikk
        statistikk = _hent_kommune_statistikk(kommunenummer)

        # Forsøk live SSB-data (overrider hardkodet statistikk)
        try:
            ssb_data = await hent_ssb_boligpriser(kommunenummer, self._client)
            if ssb_data:
                if statistikk is None:
                    statistikk = {}
                statistikk = {**statistikk, **ssb_data}
        except Exception:
            pass  # Fallback til hardkodet statistikk

        if statistikk:
            result.kommune_median_pris = statistikk.get("median_total_pris")
            result.kommune_prisvekst_prosent = (
                (statistikk.get("prisvekst_5aar") or 0) * 100
            )
            result.statistikk_aar = statistikk.get("statistikk_aar", 2024)

        # Ekstraher bygningsinformasjon
        if bygninger:
            bygning = bygninger[0]
            bruksareal = bygning.get("bruksareal")
            byggeaar = bygning.get("byggeaar")
            bygningstype = bygning.get("bygningstype", "")
            result.byggeaar = byggeaar
            result.boligtype = bygningstype

            # Estimer verdi
            tomteareal = (eiendom or {}).get("areal_m2")
            estimat, konfidensint, metode = estimer_eiendomsverdi(
                kommunenummer=kommunenummer,
                byggeaar=byggeaar,
                bruksareal=bruksareal,
                tomteareal=tomteareal,
                bygningstype=bygningstype,
            )
            result.estimert_verdi = estimat
            result.estimat_konfidensintervall = konfidensint
            result.estimat_metode = metode

            if bruksareal and estimat:
                result.pris_per_kvm = round(estimat / bruksareal)

        if eiendom:
            result.tomteareal = eiendom.get("areal_m2")

        return result

    async def hent_naboer(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
    ) -> NaboAnalyse:
        """
        Henter naboeiendommer fra Kartverket Matrikkel.
        Returnerer NaboAnalyse med liste av nabo-eiendommer.
        """
        result = NaboAnalyse(
            kommunenummer=kommunenummer,
            gnr=gnr,
            bnr=bnr,
        )
        try:
            url = (
                f"https://ws.geonorge.no/eiendomsregister/v1/naboer"
                f"?kommunenummer={kommunenummer}&gaardsnummer={gnr}&bruksnummer={bnr}&antall=10"
            )
            resp = await self._client.get(url)
            if resp.status_code != 200:
                result.feilmelding = f"Naboer ikke tilgjengelig (HTTP {resp.status_code})"
                return result

            data = resp.json()
            naboer_raw = data if isinstance(data, list) else data.get("naboer", data.get("matrikkelenhet", []))

            naboer = []
            for nabo in naboer_raw:
                # Handle different response shapes
                n_gnr = nabo.get("gaardsnummer") or nabo.get("gnr") or 0
                n_bnr = nabo.get("bruksnummer") or nabo.get("bnr") or 0
                avstand = nabo.get("avstand") or nabo.get("avstandMeter")
                adresse = nabo.get("adressetekst") or nabo.get("adresse") or ""
                if n_gnr and n_bnr:
                    naboer.append(NaboEiendom(
                        gnr=int(n_gnr),
                        bnr=int(n_bnr),
                        avstand_meter=float(avstand) if avstand else None,
                        adresse=str(adresse),
                    ))

            result.naboer = naboer
            result.antall_naboer = len(naboer)
        except Exception as exc:
            result.feilmelding = f"Nabooppslag feilet: {exc}"

        return result


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_adapter_instance: EiendomsdataAdapter | None = None


def get_eiendomsdata_adapter() -> EiendomsdataAdapter:
    """Returnerer en delt EiendomsdataAdapter-instans."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = EiendomsdataAdapter()
    return _adapter_instance
