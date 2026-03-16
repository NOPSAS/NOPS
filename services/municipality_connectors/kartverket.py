"""
ByggSjekk – Kartverket & eByggesak integration.

Henter eiendomsdata, byggesaksinformasjon og historikk fra:
- Kartverket Matrikkel WS (eiendomsregister)
- Geonorge kommuneinfo
- DIBK eByggesak (kommunale byggesaksarkiver)
- Geonorge stedsnavn
- Geonorge WMS kartlenker (kommuneplan, eiendomskart)

Alle API-er er offentlige og gratis å bruke.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanter
# ---------------------------------------------------------------------------

GEONORGE_BASE = "https://ws.geonorge.no"
MATRIKKEL_BASE = f"{GEONORGE_BASE}/eiendomsregister/v1"
KOMMUNEINFO_BASE = f"{GEONORGE_BASE}/kommuneinfo/v1"
STEDSNAVN_BASE = f"{GEONORGE_BASE}/stedsnavn/v1"

# DIBK eByggesak – nasjonalt API for kommunale byggesaker
EBYGG_BASE = "https://api.ebygg.no/api/v1"

# Kartverket WMS-tjenester
WMS_EIENDOMSKART = "https://wms.geonorge.no/skwms1/wms.eiendomskart4"
WMS_KOMMUNEPLAN = "https://wms.geonorge.no/skwms1/wms.kommuneplan"

# HTTP-timeout
TIMEOUT = httpx.Timeout(30.0)

# ---------------------------------------------------------------------------
# Dataklasser
# ---------------------------------------------------------------------------


@dataclass
class MatrikkelEiendom:
    """Eiendomsinformasjon fra Kartverket Matrikkel."""

    kommunenummer: str
    gnr: int
    bnr: int
    fnr: int = 0
    snr: int = 0
    adresse: str = ""
    postnummer: str = ""
    poststed: str = ""
    areal_m2: float | None = None
    areal_bra: float | None = None
    koordinat_nord: float | None = None
    koordinat_ost: float | None = None
    eierform: str = ""
    tinglyst_hjemmelshaver: str = ""
    heftelser: list[dict[str, Any]] = field(default_factory=list)
    matrikkel_id: str = ""


@dataclass
class MatrikkelBygning:
    """Bygningsinformasjon fra Kartverket Matrikkel."""

    bygningsnummer: int
    bygningstype: str = ""
    bygningstype_kode: str = ""
    byggeaar: int | None = None
    bruksareal: float | None = None
    etasjer: list[dict[str, Any]] = field(default_factory=list)
    bruksenheter: list[dict[str, Any]] = field(default_factory=list)
    koordinat_nord: float | None = None
    koordinat_ost: float | None = None
    representasjonspunkt: dict[str, Any] = field(default_factory=dict)
    bygningstatus: str = ""
    energimerke: str | None = None
    vannforsyning: str = ""
    avlop: str = ""
    renovasjon: str = ""


@dataclass
class Byggesak:
    """Byggesak fra kommunalt arkiv / DIBK eByggesak."""

    saksnummer: str
    sakstype: str = ""
    tittel: str = ""
    status: str = ""
    vedtaksdato: str | None = None
    innsendtdato: str | None = None
    tiltakstype: str = ""
    tiltakshaver: str = ""
    ansvarlig_soeker: str = ""
    beskrivelse: str = ""
    dokumenter: list[dict[str, Any]] = field(default_factory=list)
    kilde: str = "kartverket"


@dataclass
class KommuneInfo:
    """Kommuneinformasjon fra Geonorge."""

    kommunenummer: str
    kommunenavn: str
    fylkesnummer: str = ""
    fylkesnavn: str = ""
    ebygg_url: str | None = None
    innsyn_url: str | None = None


@dataclass
class EiendomsoppslagFullResult:
    """Komplett eiendomsoppslag med alle datakilder."""

    kommunenummer: str
    gnr: int
    bnr: int
    fnr: int = 0
    snr: int = 0

    eiendom: MatrikkelEiendom | None = None
    bygninger: list[MatrikkelBygning] = field(default_factory=list)
    byggesaker: list[Byggesak] = field(default_factory=list)
    kommune: KommuneInfo | None = None
    eiendomskart_wms_url: str = ""
    kommuneplan_wms_url: str = ""
    feilmeldinger: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Bygningstype-koder (Matrikkel)
# ---------------------------------------------------------------------------

_BYGNINGSTYPE_LABELS: dict[str, str] = {
    "111": "Enebolig",
    "112": "Enebolig med hybel/sokkelleilighet",
    "113": "Tomannsbolig, vertikaldelt",
    "114": "Tomannsbolig, horisontaldelt",
    "121": "Kjedehus",
    "122": "Andre småhus (kjede- og atriumhus)",
    "123": "Tomannsbolig m. horisontaldelt leilighet",
    "124": "Kjedehus m. horisontaldelt leilighet",
    "131": "Rekkehus",
    "133": "Andre småhus",
    "135": "Terrassehus",
    "136": "Andre småhus",
    "141": "Store hus / boligblokk",
    "142": "Boligblokk",
    "143": "Leiegård",
    "144": "Annen bygning for bofellesskap",
    "151": "Studentboliger",
    "152": "Pensjonat",
    "159": "Annen bygning for bofellesskap",
    "161": "Enebolig",
    "162": "Hybelhus",
    "163": "Botilbud",
    "171": "Garnison/militærbolig",
    "172": "Internathybler",
    "181": "Garasje/carport (frittstående)",
    "182": "Naust, båthus",
    "183": "Anneks/uthus",
    "191": "Annen boligbygning",
    "211": "Seterhus/utliebu",
    "212": "Rorbuer",
    "216": "Hytte",
    "219": "Annen fritidsbygning",
    "221": "Garasje/uthus tilhørende fritidsbygning",
    "231": "Seter",
    "239": "Annet",
}

_BYGNINGSTATUS_LABELS: dict[str, str] = {
    "IG": "Igangsettingstillatelse gitt",
    "MB": "Midlertidig brukstillatelse",
    "TB": "Tatt i bruk",
    "FS": "Ferdigattest",
    "MT": "Midlertidig brukstillatelse",
    "RA": "Rammetillatelse",
    "IP": "Ikke påbegynt",
    "RM": "Riving/Merking",
    "BF": "Brann/flom",
    "U": "Ukjent",
}


# ---------------------------------------------------------------------------
# Kartverket Matrikkel adapter
# ---------------------------------------------------------------------------


class MatrikkelAdapter:
    """
    Henter eiendoms- og bygningsdata fra Kartverket Matrikkel API.

    API-dokumentasjon: https://ws.geonorge.no/eiendomsregister/v1/
    """

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=TIMEOUT)

    async def hent_eiendom(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int = 0,
        snr: int = 0,
    ) -> MatrikkelEiendom | None:
        """Henter eiendomsdata fra Matrikkel WS."""
        try:
            url = f"{MATRIKKEL_BASE}/eiendom"
            params: dict[str, Any] = {
                "kommunenummer": kommunenummer,
                "gaardsnummer": gnr,
                "bruksnummer": bnr,
            }
            if fnr:
                params["festenummer"] = fnr
            if snr:
                params["seksjonsnummer"] = snr

            r = await self._client.get(url, params=params)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = r.json()

            # API returnerer liste - ta første treff
            items = data.get("matrikkeleiendomResultater", []) or data if isinstance(data, list) else [data]
            if not items:
                return None

            item = items[0] if isinstance(items, list) else items
            return self._parse_eiendom(item, kommunenummer, gnr, bnr, fnr, snr)

        except httpx.HTTPStatusError as e:
            logger.warning("Matrikkel eiendom HTTP-feil: %s", e)
            return None
        except Exception as e:
            logger.error("Matrikkel eiendom feil: %s", e)
            return None

    def _parse_eiendom(
        self,
        data: dict[str, Any],
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int,
        snr: int,
    ) -> MatrikkelEiendom:
        """Parser eiendomsdata fra API-respons."""
        adresser = data.get("adresser", [])
        adresse_str = ""
        postnr = ""
        poststed_str = ""
        if adresser:
            a = adresser[0]
            adresse_str = a.get("adressenavn", "") + " " + str(a.get("husnummer", "")) + (a.get("bokstav", "") or "")
            postnr = a.get("postnummer", "")
            poststed_str = a.get("poststed", "")

        koordinat = data.get("representasjonspunkt", {}) or {}
        return MatrikkelEiendom(
            kommunenummer=kommunenummer,
            gnr=gnr,
            bnr=bnr,
            fnr=fnr,
            snr=snr,
            adresse=adresse_str.strip(),
            postnummer=postnr,
            poststed=poststed_str,
            areal_m2=data.get("areal"),
            koordinat_nord=koordinat.get("nord") or koordinat.get("lat"),
            koordinat_ost=koordinat.get("ost") or koordinat.get("lon"),
            eierform=data.get("eierform", ""),
            matrikkel_id=str(data.get("matrikkeleiendomId") or ""),
        )

    async def hent_bygninger(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int = 0,
        snr: int = 0,
    ) -> list[MatrikkelBygning]:
        """Henter bygningsdata for en eiendom."""
        try:
            url = f"{MATRIKKEL_BASE}/bygning"
            params: dict[str, Any] = {
                "kommunenummer": kommunenummer,
                "gaardsnummer": gnr,
                "bruksnummer": bnr,
            }
            if fnr:
                params["festenummer"] = fnr
            if snr:
                params["seksjonsnummer"] = snr

            r = await self._client.get(url, params=params)
            if r.status_code == 404:
                return []
            r.raise_for_status()
            data = r.json()

            items = data if isinstance(data, list) else data.get("bygninger", [])
            return [self._parse_bygning(b) for b in items]

        except httpx.HTTPStatusError as e:
            logger.warning("Matrikkel bygning HTTP-feil: %s", e)
            return []
        except Exception as e:
            logger.error("Matrikkel bygning feil: %s", e)
            return []

    def _parse_bygning(self, data: dict[str, Any]) -> MatrikkelBygning:
        """Parser bygningsdata fra API-respons."""
        bygningstype_kode = str(data.get("bygningstype") or data.get("byggType", {}).get("kode", ""))
        koordinat = data.get("representasjonspunkt", {}) or {}

        return MatrikkelBygning(
            bygningsnummer=data.get("bygningsnummer", 0),
            bygningstype=_BYGNINGSTYPE_LABELS.get(bygningstype_kode, bygningstype_kode),
            bygningstype_kode=bygningstype_kode,
            byggeaar=data.get("byggeaar") or data.get("byggear"),
            bruksareal=data.get("bruksareal") or data.get("bruksarealTotalt"),
            etasjer=data.get("etasjeliste", []) or data.get("etasjer", []),
            bruksenheter=data.get("bruksenhetsliste", []) or data.get("bruksenheter", []),
            koordinat_nord=koordinat.get("nord") or koordinat.get("lat"),
            koordinat_ost=koordinat.get("ost") or koordinat.get("lon"),
            bygningstatus=_BYGNINGSTATUS_LABELS.get(
                str(data.get("bygningsstatus") or data.get("bygStatus", {}).get("kode", "")), ""
            ),
            vannforsyning=data.get("vannforsyning", ""),
            avlop=data.get("avlop", ""),
        )


# ---------------------------------------------------------------------------
# DIBK eByggesak adapter
# ---------------------------------------------------------------------------


class EByggesakAdapter:
    """
    Henter byggesaker fra kommunale arkiver via DIBK eByggesak API.

    Bruker offentlig API fra DIBK (Direktoratet for byggkvalitet).
    API-dokumentasjon: https://api.ebygg.no/
    """

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=TIMEOUT)

    async def hent_byggesaker(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int = 0,
        snr: int = 0,
    ) -> list[Byggesak]:
        """Henter byggesaker for en eiendom."""
        saker: list[Byggesak] = []

        # Forsøk eByggesak API
        saker = await self._hent_fra_ebygg(kommunenummer, gnr, bnr, fnr, snr)

        # Fallback: søk via Matrikkel-lenket søknad
        if not saker:
            saker = await self._hent_fra_matrikkel_saker(kommunenummer, gnr, bnr, fnr)

        return saker

    async def _hent_fra_ebygg(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int,
        snr: int,
    ) -> list[Byggesak]:
        """Forsøker eByggesak nasjonalt API."""
        try:
            url = f"{EBYGG_BASE}/byggesaker"
            params = {
                "kommunenr": kommunenummer,
                "gnr": gnr,
                "bnr": bnr,
            }
            if fnr:
                params["fnr"] = fnr
            if snr:
                params["snr"] = snr

            r = await self._client.get(url, params=params)
            if r.status_code in (404, 501, 503):
                return []
            r.raise_for_status()
            data = r.json()

            items = data if isinstance(data, list) else data.get("saker", data.get("byggesaker", []))
            return [self._parse_sak(s) for s in items]

        except httpx.HTTPStatusError:
            return []
        except Exception as e:
            logger.debug("eByggesak API ikke tilgjengelig: %s", e)
            return []

    async def _hent_fra_matrikkel_saker(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int,
    ) -> list[Byggesak]:
        """Fallback: byggesaker fra Matrikkel SAK-tjeneste."""
        try:
            url = f"{MATRIKKEL_BASE}/sak"
            params: dict[str, Any] = {
                "kommunenummer": kommunenummer,
                "gaardsnummer": gnr,
                "bruksnummer": bnr,
            }
            if fnr:
                params["festenummer"] = fnr

            r = await self._client.get(url, params=params)
            if r.status_code in (404, 501):
                return []
            r.raise_for_status()
            data = r.json()

            items = data if isinstance(data, list) else data.get("saker", [])
            return [self._parse_matrikkel_sak(s) for s in items]

        except Exception as e:
            logger.debug("Matrikkel SAK ikke tilgjengelig: %s", e)
            return []

    def _parse_sak(self, data: dict[str, Any]) -> Byggesak:
        """Parser byggesak fra eByggesak API."""
        return Byggesak(
            saksnummer=str(data.get("saksnummer") or data.get("id") or ""),
            sakstype=data.get("sakstype", ""),
            tittel=data.get("tittel") or data.get("beskrivelse") or "",
            status=data.get("status") or data.get("saksstatus") or "",
            vedtaksdato=data.get("vedtaksdato") or data.get("avgjortdato"),
            innsendtdato=data.get("innsendtdato") or data.get("mottattdato"),
            tiltakstype=data.get("tiltakstype", ""),
            tiltakshaver=data.get("tiltakshaver", ""),
            ansvarlig_soeker=data.get("ansvarligSoeker") or data.get("ansvarligSøker") or "",
            beskrivelse=data.get("beskrivelse") or data.get("tittel") or "",
            dokumenter=data.get("dokumenter") or [],
            kilde="ebygg",
        )

    def _parse_matrikkel_sak(self, data: dict[str, Any]) -> Byggesak:
        """Parser byggesak fra Matrikkel SAK-tjeneste."""
        return Byggesak(
            saksnummer=str(data.get("saksnummer") or ""),
            sakstype=data.get("sakstype") or data.get("sakType", {}).get("beskrivelse", ""),
            tittel=data.get("tittel") or "",
            status=data.get("saksstatus") or data.get("status") or "",
            vedtaksdato=data.get("vedtaksdato"),
            innsendtdato=data.get("registrertDato") or data.get("innsendtdato"),
            tiltakstype=data.get("tiltakstype") or "",
            beskrivelse=data.get("beskrivelse") or data.get("tittel") or "",
            kilde="matrikkel",
        )


# ---------------------------------------------------------------------------
# Kommuneinfo adapter
# ---------------------------------------------------------------------------


class KommuneInfoAdapter:
    """Henter kommuneinformasjon fra Geonorge."""

    _cache: dict[str, KommuneInfo] = {}

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=TIMEOUT)

    async def hent_kommuneinfo(self, kommunenummer: str) -> KommuneInfo:
        """Henter kommunenavn og metadata."""
        if kommunenummer in self._cache:
            return self._cache[kommunenummer]

        try:
            url = f"{KOMMUNEINFO_BASE}/kommuner/{kommunenummer}"
            r = await self._client.get(url)
            r.raise_for_status()
            data = r.json()

            info = KommuneInfo(
                kommunenummer=kommunenummer,
                kommunenavn=data.get("kommunenavnNorsk") or data.get("kommunenavn") or kommunenummer,
                fylkesnummer=str(data.get("fylkesnummer") or ""),
                fylkesnavn=data.get("fylkesnavn") or "",
                # eByggSak innsyn - ikke alle kommuner har dette offentlig
                innsyn_url=self._bygg_innsyn_url(kommunenummer, data),
            )
            self._cache[kommunenummer] = info
            return info

        except Exception as e:
            logger.warning("Kommuneinfo feil for %s: %s", kommunenummer, e)
            return KommuneInfo(
                kommunenummer=kommunenummer,
                kommunenavn=kommunenummer,
            )

    def _bygg_innsyn_url(self, kommunenummer: str, data: dict[str, Any]) -> str | None:
        """Bygger URL til kommunens innsynsportal basert på kommunenummer."""
        # Kjente kommunale innsynsportaler
        _INNSYN_URLS: dict[str, str] = {
            "3212": "https://www.nesodden.kommune.no/tjenester/plan-bygg-og-eiendom/byggesak/",
            "0301": "https://innsyn.oslo.kommune.no/",
            "4601": "https://www.bergen.kommune.no/hvaskjer/tema/plan-og-bygg",
            "5001": "https://www.trondheim.kommune.no/tema/bygg-og-eiendom/",
            "1103": "https://www.stavanger.kommune.no/plan-og-bygg/",
            "4204": "https://kristiansand.kommune.no/plan-og-bygg/",
            "3005": "https://www.drammen.kommune.no/tjenester/plan-og-bygg/",
            "3201": "https://www.baerum.kommune.no/tjenester/bygg-og-eiendom/",
        }
        return _INNSYN_URLS.get(kommunenummer)


# ---------------------------------------------------------------------------
# WMS kartlenke-bygger
# ---------------------------------------------------------------------------


def bygg_eiendomskart_url(
    nord: float,
    ost: float,
    zoom: int = 4000,
) -> str:
    """Bygger WMS GetMap URL for eiendomskart."""
    half = zoom / 2
    bbox = f"{ost - half},{nord - half},{ost + half},{nord + half}"
    return (
        f"{WMS_EIENDOMSKART}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS=Eiendomskart&STYLES=&CRS=EPSG:25833"
        f"&BBOX={bbox}&WIDTH=800&HEIGHT=600&FORMAT=image/png"
    )


def bygg_kommuneplan_url(
    nord: float,
    ost: float,
    zoom: int = 4000,
) -> str:
    """Bygger WMS GetMap URL for kommuneplan."""
    half = zoom / 2
    bbox = f"{ost - half},{nord - half},{ost + half},{nord + half}"
    return (
        f"{WMS_KOMMUNEPLAN}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS=kommuneplanKartdata&STYLES=&CRS=EPSG:25833"
        f"&BBOX={bbox}&WIDTH=800&HEIGHT=600&FORMAT=image/png"
    )


def bygg_se_eiendom_url(kommunenummer: str, gnr: int, bnr: int) -> str:
    """Bygger lenke til Se Eiendom (seeiendom.kartverket.no)."""
    return f"https://seeiendom.kartverket.no/?kommunenr={kommunenummer}&gnr={gnr}&bnr={bnr}"


# ---------------------------------------------------------------------------
# Kombinert adapter
# ---------------------------------------------------------------------------


class KartverketPropertyAdapter:
    """
    Kombinert adapter for komplett eiendomsdata fra Kartverket og DIBK.
    Kjører parallelle forespørsler for beste ytelse.
    """

    def __init__(self):
        self._http = httpx.AsyncClient(timeout=TIMEOUT)
        self.matrikkel = MatrikkelAdapter(self._http)
        self.ebygg = EByggesakAdapter(self._http)
        self.kommuneinfo = KommuneInfoAdapter(self._http)

    async def full_oppslag(
        self,
        kommunenummer: str,
        gnr: int,
        bnr: int,
        fnr: int = 0,
        snr: int = 0,
    ) -> EiendomsoppslagFullResult:
        """
        Henter komplett eiendomsdata fra alle Kartverket-tjenester parallelt.
        """
        result = EiendomsoppslagFullResult(
            kommunenummer=kommunenummer,
            gnr=gnr,
            bnr=bnr,
            fnr=fnr,
            snr=snr,
        )

        # Kjør alle forespørsler parallelt
        eiendom_task = self.matrikkel.hent_eiendom(kommunenummer, gnr, bnr, fnr, snr)
        bygninger_task = self.matrikkel.hent_bygninger(kommunenummer, gnr, bnr, fnr, snr)
        byggesaker_task = self.ebygg.hent_byggesaker(kommunenummer, gnr, bnr, fnr, snr)
        kommuneinfo_task = self.kommuneinfo.hent_kommuneinfo(kommunenummer)

        eiendom, bygninger, byggesaker, kommune = await asyncio.gather(
            eiendom_task,
            bygninger_task,
            byggesaker_task,
            kommuneinfo_task,
            return_exceptions=True,
        )

        # Sett resultater og håndter feil
        if isinstance(eiendom, Exception):
            result.feilmeldinger.append(f"Matrikkel eiendom: {eiendom}")
        else:
            result.eiendom = eiendom

        if isinstance(bygninger, Exception):
            result.feilmeldinger.append(f"Matrikkel bygninger: {bygninger}")
        else:
            result.bygninger = bygninger or []

        if isinstance(byggesaker, Exception):
            result.feilmeldinger.append(f"Byggesaker: {byggesaker}")
        else:
            result.byggesaker = byggesaker or []

        if isinstance(kommune, Exception):
            result.feilmeldinger.append(f"Kommuneinfo: {kommune}")
        else:
            result.kommune = kommune

        # Bygg WMS-lenker basert på koordinater
        eiendom_data = result.eiendom
        if eiendom_data and eiendom_data.koordinat_nord and eiendom_data.koordinat_ost:
            result.eiendomskart_wms_url = bygg_eiendomskart_url(
                eiendom_data.koordinat_nord,
                eiendom_data.koordinat_ost,
            )
            result.kommuneplan_wms_url = bygg_kommuneplan_url(
                eiendom_data.koordinat_nord,
                eiendom_data.koordinat_ost,
            )

        return result

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._http.aclose()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_adapter_instance: KartverketPropertyAdapter | None = None


def get_kartverket_adapter() -> KartverketPropertyAdapter:
    """Returnerer en delt KartverketPropertyAdapter-instans."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = KartverketPropertyAdapter()
    return _adapter_instance
