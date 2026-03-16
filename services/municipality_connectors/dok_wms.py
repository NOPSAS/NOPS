"""
DOK-analyse via åpne WMS GetFeatureInfo-tjenester.

Henter DOK-data direkte fra NGU, NVE og andre offentlige WMS-tjenester
uten behov for API-nøkkel. Fungerer fra alle servere.

Datasett som sjekkes:
- Radon aktsomhetsgrad (NGU)
- Flomsoner (NVE)
- Løsmasser/kvikkleire (NGU)
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

import httpx

TIMEOUT = 10


@dataclass
class DokFunn:
    datasett: str
    kilde: str
    status: str  # "berørt" | "ikke_berørt"
    beskrivelse: str
    alvorlighet: str = ""  # "HØY" | "MIDDELS" | "LAV"
    verdi: str = ""
    tek17_referanse: str = ""
    tiltak: str = ""


@dataclass
class DokWmsResultat:
    funn: list[DokFunn] = field(default_factory=list)
    antall_berørt: int = 0
    antall_ikke_berørt: int = 0
    feilmeldinger: list[str] = field(default_factory=list)


async def _wms_get_feature_info(
    client: httpx.AsyncClient,
    wms_url: str,
    layers: str,
    lon: float,
    lat: float,
    info_format: str = "application/vnd.ogc.gml",
) -> str | None:
    """Utfør WMS GetFeatureInfo-forespørsel på et punkt."""
    # Beregn BBOX rundt punktet (ca 20m)
    delta = 0.001  # ~100m
    bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layers,
        "QUERY_LAYERS": layers,
        "BBOX": bbox,
        "WIDTH": "256",
        "HEIGHT": "256",
        "SRS": "EPSG:4326",
        "X": "128",
        "Y": "128",
        "INFO_FORMAT": info_format,
    }
    try:
        resp = await client.get(wms_url, params=params)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


async def sjekk_radon(client: httpx.AsyncClient, lon: float, lat: float) -> DokFunn:
    """Sjekk radon aktsomhetsgrad fra NGU."""
    xml = await _wms_get_feature_info(
        client,
        "https://geo.ngu.no/mapserver/RadonWMS2",
        "Radon_aktsomhet",
        lon, lat,
    )
    if xml and "aktsomhetgrad" in xml:
        try:
            root = ET.fromstring(xml)
            feat = root.find(".//{http://www.opengis.net/gml}boundedBy/..")
            if feat is None:
                # Prøv uten namespace
                for elem in root.iter():
                    if "aktsomhetgrad_besk" in (elem.tag or ""):
                        grad_besk = elem.text or ""
                        grad = ""
                        for e2 in root.iter():
                            if e2.tag == "aktsomhetgrad":
                                grad = e2.text or ""
                        return DokFunn(
                            datasett="Radon aktsomhetskart",
                            kilde="NGU",
                            status="berørt" if grad in ("2", "3", "4") else "ikke_berørt",
                            beskrivelse=grad_besk,
                            alvorlighet="HØY" if grad in ("3", "4") else "MIDDELS" if grad == "2" else "LAV",
                            verdi=f"Aktsomhetsgrad {grad}: {grad_besk}",
                            tek17_referanse="TEK17 §13-5: Radon maks 200 Bq/m³",
                            tiltak="Radonmåling anbefales. Ved bygging: radonmembran og evt. radonbrønn." if grad in ("2", "3", "4") else "",
                        )
            # Parse med namespace
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag == "aktsomhetgrad_besk":
                    grad_besk = elem.text or ""
                if tag == "aktsomhetgrad":
                    grad = elem.text or ""
            return DokFunn(
                datasett="Radon aktsomhetskart",
                kilde="NGU",
                status="berørt" if grad in ("2", "3", "4") else "ikke_berørt",
                beskrivelse=grad_besk,
                alvorlighet="HØY" if grad in ("3", "4") else "MIDDELS" if grad == "2" else "LAV",
                verdi=f"Aktsomhetsgrad {grad}: {grad_besk}",
                tek17_referanse="TEK17 §13-5: Radon maks 200 Bq/m³",
                tiltak="Radonmåling anbefales. Ved bygging: radonmembran og evt. radonbrønn." if grad in ("2", "3", "4") else "",
            )
        except Exception:
            pass

    return DokFunn(
        datasett="Radon aktsomhetskart",
        kilde="NGU",
        status="ikke_berørt",
        beskrivelse="Ingen radondata funnet for dette punktet",
        alvorlighet="LAV",
    )


async def sjekk_flom(client: httpx.AsyncClient, lon: float, lat: float) -> DokFunn:
    """Sjekk flomsoner fra NVE."""
    xml = await _wms_get_feature_info(
        client,
        "https://nve.geodataonline.no/arcgis/services/Flomsoner1/MapServer/WMSServer",
        "Flomsone_50arsflom,Flomsone_100arsflom,Flomsone_200arsflom",
        lon, lat,
        info_format="text/xml",
    )
    if xml and "FIELDS" in xml:
        return DokFunn(
            datasett="Flomsoner (NVE)",
            kilde="NVE",
            status="berørt",
            beskrivelse="Eiendommen ligger i en flomsone",
            alvorlighet="HØY",
            tek17_referanse="TEK17 §7-2: Sikkerhet mot flom, sikkerhetsklasse F1-F3",
            tiltak="Flomvurdering kreves ved byggesøknad. Sjekk NVE flomsonekart.",
        )
    return DokFunn(
        datasett="Flomsoner (NVE)",
        kilde="NVE",
        status="ikke_berørt",
        beskrivelse="Ikke i registrert flomsone",
        alvorlighet="LAV",
    )


async def sjekk_losmasser(client: httpx.AsyncClient, lon: float, lat: float) -> DokFunn:
    """Sjekk løsmasser/kvikkleire fra NGU."""
    xml = await _wms_get_feature_info(
        client,
        "https://geo.ngu.no/mapserver/LosijordWMS",
        "Losmasse_flate",
        lon, lat,
    )
    if xml and ("leire" in xml.lower() or "kvikk" in xml.lower() or "marin" in xml.lower()):
        return DokFunn(
            datasett="Løsmasser / kvikkleire",
            kilde="NGU",
            status="berørt",
            beskrivelse="Området har marine avsetninger – risiko for kvikkleire",
            alvorlighet="KRITISK" if "kvikk" in xml.lower() else "HØY",
            tek17_referanse="TEK17 §7-3: Sikkerhet mot skred",
            tiltak="Geoteknisk vurdering PÅKREVD ved byggetiltak.",
        )
    return DokFunn(
        datasett="Løsmasser / kvikkleire",
        kilde="NGU",
        status="ikke_berørt",
        beskrivelse="Ingen kvikkleirerisiko registrert",
        alvorlighet="LAV",
    )


async def dok_analyse_wms(lon: float, lat: float) -> DokWmsResultat:
    """
    Komplett DOK-analyse via åpne WMS-tjenester.
    Krever ingen API-nøkkel. Fungerer fra alle servere.
    """
    resultat = DokWmsResultat()

    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        headers={"User-Agent": "nops.no/1.0 ByggSjekk DOK-analyse"},
    ) as client:
        import asyncio
        funn_list = await asyncio.gather(
            sjekk_radon(client, lon, lat),
            sjekk_flom(client, lon, lat),
            sjekk_losmasser(client, lon, lat),
            return_exceptions=True,
        )

        for funn in funn_list:
            if isinstance(funn, DokFunn):
                resultat.funn.append(funn)
                if funn.status == "berørt":
                    resultat.antall_berørt += 1
                else:
                    resultat.antall_ikke_berørt += 1
            elif isinstance(funn, Exception):
                resultat.feilmeldinger.append(str(funn))

    return resultat
