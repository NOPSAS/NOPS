"""
ByggSjekk – Eiendomsoppslag-endepunkter.

Henter planrapport, DOK-analyse og dispensasjoner for en eiendom
direkte fra arealplaner.no og Geodata DOK-analyse API.
Henter eiendomsdata, bygningsinfo og byggesaker fra Kartverket.

Endepunkter:
  GET /property/lookup          – komplett eiendomsoppslag (DOK + planrapport)
  GET /property/planrapport     – planrapport fra arealplaner.no
  GET /property/dok-analyse     – DOK-analyse fra Geodata
  GET /property/dispensasjoner  – dispensasjonsoversikt
  GET /property/matrikkel       – Kartverket Matrikkel eiendomsdata + bygninger
  GET /property/byggesaker      – byggesaker fra kommunalt arkiv (eByggesak)
  GET /property/full            – komplett oppslag fra alle kilder
"""

from __future__ import annotations

import asyncio
import sys
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.core.deps import get_current_user, get_optional_user, require_ai_access, require_pdf_access
from app.models.user import User

router = APIRouter()

# Legg til services-stien (fungerer både lokalt og i Docker)
for _p in ["/app", "/app/services", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")),
           os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../services"))]:
    if _p not in sys.path and os.path.isdir(_p):
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Endepunkter
# ---------------------------------------------------------------------------


@router.get(
    "/lookup",
    summary="Komplett eiendomsoppslag – DOK-analyse + planrapport",
    response_model=dict,
)
async def property_lookup(
    knr: Annotated[str, Query(description="Kommunenummer, f.eks. '3212' for Nesodden")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query(description="Festenummer (valgfritt)")] = None,
    snr: Annotated[int | None, Query(description="Seksjonsnummer (valgfritt)")] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Henter komplett eiendomsinformasjon fra kommunale systemer:
    - DOK-analyse (berørte kartdatasett)
    - Planrapport (gjeldende reguleringsplaner)
    - Dispensasjoner

    Støtter alle norske kommuner. Spesialtilpasset for Nesodden (knr=3212).
    """
    try:
        from services.municipality_connectors.arealplaner import (
            get_nesodden_adapter, NesoddenAdapter,
            DokAnalyseAdapter, ArealplanerAdapter,
            get_dok_adapter, get_arealplaner_adapter,
        )
        import asyncio

        # Bruk Nesodden-adapter for knr=3212, generisk for andre
        if knr == "3212":
            adapter = get_nesodden_adapter()
            result = await adapter.full_eiendomsoppslag(gnr, bnr, fnr, snr)
        else:
            dok = get_dok_adapter()
            plan = get_arealplaner_adapter()
            dok_result, plan_result = await asyncio.gather(
                dok.analyse_eiendom(knr, gnr, bnr, fnr, snr),
                plan.hent_planrapport(knr, gnr, bnr, fnr, snr),
                return_exceptions=True,
            )

            from services.municipality_connectors.arealplaner import EiendomsoppslagResult
            result = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
            if not isinstance(dok_result, Exception):
                result.dok_analyse = dok_result
            if not isinstance(plan_result, Exception):
                result.planrapport = plan_result

        return _serialize_oppslag(result)

    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Arealplaner-modulen er ikke tilgjengelig: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Eiendomsoppslag feilet: {exc}",
        )


@router.get(
    "/planrapport",
    summary="Planrapport fra arealplaner.no",
    response_model=dict,
)
async def get_planrapport(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query()] = None,
    snr: Annotated[int | None, Query()] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """Henter planrapport og dispensasjonsoversikt fra arealplaner.no."""
    try:
        from services.municipality_connectors.arealplaner import get_arealplaner_adapter
        adapter = get_arealplaner_adapter()
        result = await adapter.hent_planrapport(knr, gnr, bnr, fnr, snr)

        return {
            "kommunenummer": result.kommunenummer,
            "gnr": result.gnr,
            "bnr": result.bnr,
            "gjeldende_planer": [
                {
                    "plan_id": p.plan_id,
                    "plan_navn": p.plan_navn,
                    "plan_type": p.plan_type,
                    "status": p.status,
                    "vedtaksdato": p.vedtaksdato,
                    "arealformål": p.arealformål,
                    "url": p.norkart_url,
                }
                for p in result.gjeldende_planer
            ],
            "dispensasjoner": [
                {
                    "saks_id": d.saks_id,
                    "saks_type": d.saks_type,
                    "vedtaksdato": d.vedtaksdato,
                    "status": d.status,
                    "beskrivelse": d.beskrivelse,
                    "paragraf": d.paragraf,
                }
                for d in result.dispensasjoner
            ],
            "planrapport_url": result.planrapport_url,
            "feilmelding": result.feilmelding,
            "kilde": result.kilde,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Planrapport feilet: {exc}",
        )


@router.get(
    "/dok-analyse",
    summary="DOK-analyse fra Geodata AS",
    response_model=dict,
)
async def get_dok_analyse(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query()] = None,
    snr: Annotated[int | None, Query()] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """Kjører DOK-analyse via åpne WMS-tjenester (radon, flom, kvikkleire)."""
    try:
        # Hent koordinater fra adresse-API
        lon, lat = None, None
        try:
            import httpx as _httpx
            async with _httpx.AsyncClient(timeout=8) as _c:
                resp = await _c.get(
                    f"https://ws.geonorge.no/adresser/v1/sok",
                    params={"kommunenummer": knr, "gardsnummer": gnr, "bruksnummer": bnr, "treffPerSide": "1"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("adresser"):
                        a = data["adresser"][0]
                        lat = a.get("representasjonspunkt", {}).get("lat")
                        lon = a.get("representasjonspunkt", {}).get("lon")
        except Exception:
            pass

        if lon and lat:
            from services.municipality_connectors.dok_wms import dok_analyse_wms
            result = await dok_analyse_wms(lon, lat)
            return {
                "kommunenummer": knr,
                "gnr": gnr,
                "bnr": bnr,
                "berørte_datasett": [
                    {
                        "uuid": "",
                        "navn": f.datasett,
                        "tema": f.kilde,
                        "status": f.status,
                        "beskrivelse": f.beskrivelse,
                        "alvorlighet": f.alvorlighet,
                        "verdi": f.verdi,
                        "tek17": f.tek17_referanse,
                        "tiltak": f.tiltak,
                    }
                    for f in result.funn if f.status == "berørt"
                ],
                "ikke_berørte_datasett": [
                    {"uuid": "", "navn": f.datasett, "tema": f.kilde}
                    for f in result.funn if f.status == "ikke_berørt"
                ],
                "alle_funn": [
                    {
                        "datasett": f.datasett,
                        "kilde": f.kilde,
                        "status": f.status,
                        "beskrivelse": f.beskrivelse,
                        "alvorlighet": f.alvorlighet,
                        "verdi": f.verdi,
                        "tek17": f.tek17_referanse,
                        "tiltak": f.tiltak,
                    }
                    for f in result.funn
                ],
                "antall_berørt": result.antall_berørt,
                "antall_ikke_berørt": result.antall_ikke_berørt,
                "rapport_url": None,
                "feilmelding": None,
                "kilde": "WMS (NGU, NVE) – åpne data, ingen API-nøkkel nødvendig",
            }
        else:
            return {
                "kommunenummer": knr, "gnr": gnr, "bnr": bnr,
                "berørte_datasett": [], "ikke_berørte_datasett": [],
                "antall_berørt": 0, "antall_ikke_berørt": 0,
                "rapport_url": None,
                "feilmelding": "Kunne ikke finne koordinater for eiendommen.",
                "kilde": None,
            }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DOK-analyse feilet: {exc}",
        )


@router.get(
    "/dispensasjoner",
    summary="Dispensasjoner for en eiendom",
    response_model=dict,
)
async def get_dispensasjoner(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    current_user: User = Depends(get_optional_user),
) -> dict:
    """Henter dispensasjonsoversikt for en eiendom fra arealplaner.no."""
    try:
        from services.municipality_connectors.arealplaner import get_arealplaner_adapter
        adapter = get_arealplaner_adapter()
        result = await adapter.hent_planrapport(knr, gnr, bnr)

        return {
            "kommunenummer": knr,
            "gnr": gnr,
            "bnr": bnr,
            "antall_dispensasjoner": len(result.dispensasjoner),
            "dispensasjoner": [
                {
                    "saks_id": d.saks_id,
                    "saks_type": d.saks_type,
                    "vedtaksdato": d.vedtaksdato,
                    "status": d.status,
                    "beskrivelse": d.beskrivelse,
                    "paragraf": d.paragraf,
                }
                for d in result.dispensasjoner
            ],
            "kilde": result.kilde,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Dispensasjonshenting feilet: {exc}",
        )


# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------


def _serialize_oppslag(result: "EiendomsoppslagResult") -> dict:
    """Konverterer EiendomsoppslagResult til JSON-serialiserbar dict."""
    out: dict = {
        "kommunenummer": result.kommunenummer,
        "gnr": result.gnr,
        "bnr": result.bnr,
        "fnr": result.fnr,
        "snr": result.snr,
        "feilmeldinger": result.feilmeldinger,
    }

    if result.dok_analyse:
        d = result.dok_analyse
        out["dok_analyse"] = {
            "berørte_datasett": [
                {"uuid": ds.uuid, "navn": ds.navn, "tema": ds.tema, "url": ds.url}
                for ds in d.berørte_datasett
            ],
            "antall_berørt": len(d.berørte_datasett),
            "antall_ikke_berørt": len(d.ikke_berørte_datasett),
            "rapport_url": d.rapport_url,
            "feilmelding": d.feilmelding,
        }
    else:
        out["dok_analyse"] = None

    if result.planrapport:
        p = result.planrapport
        out["planrapport"] = {
            "gjeldende_planer": [
                {
                    "plan_id": pl.plan_id,
                    "plan_navn": pl.plan_navn,
                    "plan_type": pl.plan_type,
                    "status": pl.status,
                    "vedtaksdato": pl.vedtaksdato,
                    "arealformål": pl.arealformål,
                    "url": pl.norkart_url,
                }
                for pl in p.gjeldende_planer
            ],
            "dispensasjoner": [
                {
                    "saks_id": d.saks_id,
                    "saks_type": d.saks_type,
                    "vedtaksdato": d.vedtaksdato,
                    "status": d.status,
                    "beskrivelse": d.beskrivelse,
                    "paragraf": d.paragraf,
                }
                for d in p.dispensasjoner
            ],
            "planrapport_url": p.planrapport_url,
            "feilmelding": p.feilmelding,
        }
    else:
        out["planrapport"] = None

    return out


# ---------------------------------------------------------------------------
# Kartverket Matrikkel + eByggesak endepunkter
# ---------------------------------------------------------------------------


@router.get(
    "/matrikkel",
    summary="Eiendomsdata + bygninger fra Kartverket Matrikkel",
    response_model=dict,
)
async def get_matrikkel(
    knr: Annotated[str, Query(description="Kommunenummer, f.eks. '3212'")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query(description="Festenummer (valgfritt)")] = None,
    snr: Annotated[int | None, Query(description="Seksjonsnummer (valgfritt)")] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Henter eiendomsdata og bygningsinformasjon fra Kartverket Matrikkel.
    Returnerer: adresse, areal, koordinater, bygninger med byggeår og bygningstatus.
    """
    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        adapter = get_kartverket_adapter()

        eiendom, bygninger = await asyncio.gather(
            adapter.matrikkel.hent_eiendom(knr, gnr, bnr, fnr or 0, snr or 0),
            adapter.matrikkel.hent_bygninger(knr, gnr, bnr, fnr or 0, snr or 0),
        )

        return {
            "kommunenummer": knr,
            "gnr": gnr,
            "bnr": bnr,
            "eiendom": _serialize_eiendom(eiendom),
            "bygninger": [_serialize_bygning(b) for b in bygninger],
            "se_eiendom_url": _bygg_se_eiendom_url(knr, gnr, bnr),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Matrikkel-oppslag feilet: {exc}",
        )


@router.get(
    "/byggesaker",
    summary="Byggesaker fra kommunalt arkiv",
    response_model=dict,
)
async def get_byggesaker(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query()] = None,
    snr: Annotated[int | None, Query()] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Henter byggesaker (søknader, tillatelser, ferdigattester) fra kommunalt
    arkiv via DIBK eByggesak og Kartverket Matrikkel SAK.
    """
    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        adapter = get_kartverket_adapter()
        saker = await adapter.ebygg.hent_byggesaker(knr, gnr, bnr, fnr or 0, snr or 0)

        return {
            "kommunenummer": knr,
            "gnr": gnr,
            "bnr": bnr,
            "antall_saker": len(saker),
            "byggesaker": [_serialize_byggesak(s) for s in saker],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Byggesak-oppslag feilet: {exc}",
        )


@router.get(
    "/full",
    summary="Komplett eiendomsoppslag fra alle datakilder",
    response_model=dict,
)
async def property_full_lookup(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query()] = None,
    snr: Annotated[int | None, Query()] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Henter alle tilgjengelige data for en eiendom fra alle datakilder parallelt:
    - Kartverket Matrikkel (eiendom + bygninger)
    - DIBK eByggesak (byggesaker)
    - Geodata DOK-analyse
    - Arealplaner.no (planrapport + dispensasjoner)
    - Kommuneinfo
    """
    try:
        from services.municipality_connectors.kartverket import (
            get_kartverket_adapter, bygg_se_eiendom_url,
        )
        from services.municipality_connectors.arealplaner import (
            get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
            EiendomsoppslagResult,
        )
        import asyncio

        kartverket = get_kartverket_adapter()

        # Kjør Kartverket-oppslag og arealplaner-oppslag parallelt
        kartverket_task = kartverket.full_oppslag(knr, gnr, bnr, fnr or 0, snr or 0)

        if knr == "3212":
            arealplaner_task = get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, fnr, snr)
        else:
            async def _arealplaner_combined():
                dok = get_dok_adapter()
                plan = get_arealplaner_adapter()
                dok_r, plan_r = await asyncio.gather(
                    dok.analyse_eiendom(knr, gnr, bnr, fnr, snr),
                    plan.hent_planrapport(knr, gnr, bnr, fnr, snr),
                    return_exceptions=True,
                )
                r = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
                if not isinstance(dok_r, Exception):
                    r.dok_analyse = dok_r
                if not isinstance(plan_r, Exception):
                    r.planrapport = plan_r
                return r
            arealplaner_task = _arealplaner_combined()

        # Legg til planslurpen som parallell task
        from services.municipality_connectors.planslurpen import get_planslurpen_adapter

        planslurpen_task = get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, fnr or 0, snr or 0)

        kartverket_result, arealplaner_result, planslurpen_result = await asyncio.gather(
            kartverket_task,
            arealplaner_task,
            planslurpen_task,
            return_exceptions=True,
        )

        result: dict = {
            "kommunenummer": knr,
            "gnr": gnr,
            "bnr": bnr,
            "fnr": fnr,
            "snr": snr,
            "se_eiendom_url": bygg_se_eiendom_url(knr, gnr, bnr),
        }

        bygninger_raw: list = []
        eiendom_raw: dict | None = None

        if isinstance(kartverket_result, Exception):
            result["kartverket"] = {"feil": str(kartverket_result)}
        else:
            kr = kartverket_result
            eiendom_raw = _serialize_eiendom(kr.eiendom)
            bygninger_raw = [_serialize_bygning(b) for b in kr.bygninger]
            result["eiendom"] = eiendom_raw
            result["bygninger"] = bygninger_raw
            result["byggesaker"] = [_serialize_byggesak(s) for s in kr.byggesaker]
            result["kommune"] = {
                "kommunenummer": kr.kommune.kommunenummer if kr.kommune else knr,
                "kommunenavn": kr.kommune.kommunenavn if kr.kommune else knr,
                "innsyn_url": kr.kommune.innsyn_url if kr.kommune else None,
            }
            result["eiendomskart_wms_url"] = kr.eiendomskart_wms_url
            result["kommuneplan_wms_url"] = kr.kommuneplan_wms_url
            result["kartverket_feilmeldinger"] = kr.feilmeldinger

        if isinstance(arealplaner_result, Exception):
            result["arealplaner"] = {"feil": str(arealplaner_result)}
        else:
            ar = arealplaner_result
            result.update(_serialize_oppslag(ar))

        # Planslurpen planbestemmelser
        if isinstance(planslurpen_result, Exception):
            result["planslurpen"] = {"feil": str(planslurpen_result)}
        else:
            ps = planslurpen_result
            result["planslurpen"] = {
                "antall_planer": ps.antall_planer,
                "feilmelding": ps.feilmelding,
                "planer": [
                    {
                        "plan_id": p.plan_id,
                        "plan_navn": p.plan_navn,
                        "plantype": p.plantype,
                        "maks_hoyde": p.maks_hoyde,
                        "maks_utnyttelse": p.maks_utnyttelse,
                        "tillatt_bruk": p.tillatt_bruk,
                        "droemmeplan_url": p.droemmeplan_url,
                        "antall_bestemmelser": len(p.bestemmelser),
                        "bestemmelser": [
                            {
                                "kode": b.kode,
                                "tittel": b.tittel,
                                "tekst": b.tekst[:300] if b.tekst else "",
                                "verdi": b.verdi,
                                "kategori": b.kategori,
                            }
                            for b in p.bestemmelser[:20]  # maks 20 per plan
                        ],
                    }
                    for p in ps.planer
                ],
            }

        # Verdiestimator – kjøres etter Kartverket-data er hentet
        try:
            from services.municipality_connectors.eiendomsdata import get_eiendomsdata_adapter
            eiendomsdata = get_eiendomsdata_adapter()
            historikk = await eiendomsdata.hent_historikk(
                kommunenummer=knr,
                gnr=gnr,
                bnr=bnr,
                bygninger=bygninger_raw if bygninger_raw else None,
                eiendom=eiendom_raw,
            )
            result["verdiestimator"] = {
                "estimert_verdi": historikk.estimert_verdi,
                "konfidensintervall": list(historikk.estimat_konfidensintervall) if historikk.estimat_konfidensintervall else None,
                "estimat_metode": historikk.estimat_metode,
                "pris_per_kvm": historikk.pris_per_kvm,
                "kommune_median_pris": historikk.kommune_median_pris,
                "kommune_prisvekst_prosent": historikk.kommune_prisvekst_prosent,
                "statistikk_aar": historikk.statistikk_aar,
                "boligtype": historikk.boligtype,
                "byggeaar": historikk.byggeaar,
            }
        except Exception:
            result["verdiestimator"] = None

        return result

    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Kartverket-modulen er ikke tilgjengelig: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fullt eiendomsoppslag feilet: {exc}",
        )


# ---------------------------------------------------------------------------
# Serialiseringshjelpere for Kartverket-data
# ---------------------------------------------------------------------------


def _serialize_eiendom(eiendom: "MatrikkelEiendom | None") -> dict | None:
    if not eiendom:
        return None
    return {
        "adresse": eiendom.adresse,
        "postnummer": eiendom.postnummer,
        "poststed": eiendom.poststed,
        "areal_m2": eiendom.areal_m2,
        "koordinat_nord": eiendom.koordinat_nord,
        "koordinat_ost": eiendom.koordinat_ost,
        "eierform": eiendom.eierform,
        "matrikkel_id": eiendom.matrikkel_id,
    }


def _serialize_bygning(bygning: "MatrikkelBygning") -> dict:
    return {
        "bygningsnummer": bygning.bygningsnummer,
        "bygningstype": bygning.bygningstype,
        "bygningstype_kode": bygning.bygningstype_kode,
        "byggeaar": bygning.byggeaar,
        "bruksareal": bygning.bruksareal,
        "bygningstatus": bygning.bygningstatus,
        "etasjer": bygning.etasjer,
        "bruksenheter": bygning.bruksenheter,
        "koordinat_nord": bygning.koordinat_nord,
        "koordinat_ost": bygning.koordinat_ost,
    }


def _serialize_byggesak(sak: "Byggesak") -> dict:
    return {
        "saksnummer": sak.saksnummer,
        "sakstype": sak.sakstype,
        "tittel": sak.tittel,
        "status": sak.status,
        "vedtaksdato": sak.vedtaksdato,
        "innsendtdato": sak.innsendtdato,
        "tiltakstype": sak.tiltakstype,
        "tiltakshaver": sak.tiltakshaver,
        "ansvarlig_soeker": sak.ansvarlig_soeker,
        "beskrivelse": sak.beskrivelse,
        "dokumenter": sak.dokumenter,
        "kilde": sak.kilde,
    }


def _bygg_se_eiendom_url(knr: str, gnr: int, bnr: int) -> str:
    return f"https://seeiendom.kartverket.no/?kommunenr={knr}&gnr={gnr}&bnr={bnr}"


# ---------------------------------------------------------------------------
# AI-analyse endepunkt
# ---------------------------------------------------------------------------


@router.post(
    "/analyse",
    summary="AI-drevet eiendomsanalyse",
    response_model=dict,
)
async def ai_property_analyse(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query()] = None,
    snr: Annotated[int | None, Query()] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Kjører en AI-drevet analyse av en eiendom basert på alle tilgjengelige datakilder.

    Bruker Anthropic Claude (eller OpenAI GPT) til å:
    - Vurdere risiko for ulovlige byggearbeider
    - Analysere dispensasjonshistorikk
    - Vurdere samsvar med reguleringsplan
    - Gi konkrete anbefalinger til arkitekt

    VIKTIG: Analysen er beslutningsstøtte – ikke en juridisk vurdering.
    """
    try:
        # Hent all eiendomsdata først
        from services.municipality_connectors.kartverket import get_kartverket_adapter, bygg_se_eiendom_url
        from services.municipality_connectors.arealplaner import (
            get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
            EiendomsoppslagResult,
        )
        from services.property_intelligence.analyzer import get_property_analyzer

        kartverket = get_kartverket_adapter()
        kartverket_task = kartverket.full_oppslag(knr, gnr, bnr, fnr or 0, snr or 0)

        if knr == "3212":
            arealplaner_task = get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, fnr, snr)
        else:
            async def _arealplaner_combined():
                dok = get_dok_adapter()
                plan = get_arealplaner_adapter()
                dok_r, plan_r = await asyncio.gather(
                    dok.analyse_eiendom(knr, gnr, bnr, fnr, snr),
                    plan.hent_planrapport(knr, gnr, bnr, fnr, snr),
                    return_exceptions=True,
                )
                r = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
                if not isinstance(dok_r, Exception):
                    r.dok_analyse = dok_r
                if not isinstance(plan_r, Exception):
                    r.planrapport = plan_r
                return r
            arealplaner_task = _arealplaner_combined()

        kartverket_result, arealplaner_result = await asyncio.gather(
            kartverket_task, arealplaner_task, return_exceptions=True
        )

        # Bygg eiendomsdata dict for AI-analyse
        eiendom_data: dict = {
            "kommunenummer": knr,
            "gnr": gnr,
            "bnr": bnr,
        }

        if not isinstance(kartverket_result, Exception):
            kr = kartverket_result
            eiendom_data["eiendom"] = _serialize_eiendom(kr.eiendom)
            eiendom_data["bygninger"] = [_serialize_bygning(b) for b in kr.bygninger]
            eiendom_data["byggesaker"] = [_serialize_byggesak(s) for s in kr.byggesaker]
            eiendom_data["kommune"] = {
                "kommunenavn": kr.kommune.kommunenavn if kr.kommune else knr,
            }
            eiendom_data["feilmeldinger"] = kr.feilmeldinger

        if not isinstance(arealplaner_result, Exception):
            arealdata = _serialize_oppslag(arealplaner_result)
            eiendom_data["planrapport"] = arealdata.get("planrapport")
            eiendom_data["dok_analyse"] = arealdata.get("dok_analyse")

        # Planslurpen data for AI
        try:
            from services.municipality_connectors.planslurpen import get_planslurpen_adapter
            ps_result = await get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, fnr or 0, snr or 0)
            if ps_result.antall_planer > 0:
                eiendom_data["planbestemmelser"] = [
                    {
                        "plan_navn": p.plan_navn,
                        "maks_hoyde": p.maks_hoyde,
                        "maks_utnyttelse": p.maks_utnyttelse,
                        "tillatt_bruk": p.tillatt_bruk,
                    }
                    for p in ps_result.planer
                ]
        except Exception:
            pass

        # Kjør AI-analyse
        analyzer = get_property_analyzer()
        analyse = await analyzer.analyser_eiendom(eiendom_data)

        return {
            "eiendom_id": analyse.eiendom_id,
            "risiko_nivaa": analyse.risiko_nivaa,
            "risiko_score": analyse.risiko_score,
            "sammendrag": analyse.sammendrag,
            "nøkkelfinninger": analyse.nøkkelfinninger,
            "anbefalinger": analyse.anbefalinger,
            "avviksvurdering": analyse.avviksvurdering,
            "dispensasjonsgrunnlag": analyse.dispensasjonsgrunnlag,
            "reguleringsplan_vurdering": analyse.reguleringsplan_vurdering,
            "dok_analyse_vurdering": analyse.dok_analyse_vurdering,
            "fraskrivelse": analyse.fraskrivelse,
            "model_used": analyse.model_used,
        }

    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI-analyse modulen er ikke tilgjengelig: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI-analyse feilet: {exc}",
        )


@router.get(
    "/regelverk",
    summary="Relevant norsk regelverk for en eiendomssituasjon",
    response_model=dict,
)
async def get_regelverk(
    avvik: Annotated[str | None, Query(description="Kommaseparert liste av avvikskategorier")] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Returnerer relevante paragrafer fra PBL, TEK17, SAK10 og EMGL.
    Filtrér med ?avvik=ADDITION_DETECTED,USE_CHANGE_INDICATION for målrettede treff.
    """
    try:
        from services.regulations.regelverk import (
            ALLE_PARAGRAFER, finn_relevante_paragrafer, bygg_regelverk_kontekst
        )

        kategorier = [k.strip() for k in avvik.split(",") if k.strip()] if avvik else None

        if kategorier:
            seen: set = set()
            paragrafer = []
            for kat in kategorier:
                for p in finn_relevante_paragrafer(kat):
                    if p.kode not in seen:
                        paragrafer.append(p)
                        seen.add(p.kode)
        else:
            paragrafer = ALLE_PARAGRAFER

        return {
            "antall": len(paragrafer),
            "kategorier_filter": kategorier,
            "paragrafer": [
                {
                    "lov": p.lov,
                    "kode": p.kode,
                    "tittel": p.tittel,
                    "ingress": p.ingress,
                    "fulltext": p.fulltext,
                    "relevans": p.relevans,
                    "alvorlighet": p.alvorlighet,
                }
                for p in paragrafer
            ],
            "sammendrag_tekst": bygg_regelverk_kontekst(kategorier),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Regelverk-oppslag feilet: {exc}")


@router.get(
    "/naboer",
    summary="Naboeiendommer fra Kartverket Matrikkel",
    response_model=dict,
)
async def get_naboer(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Henter liste over naboeiendommer innenfor ca. 50m radius via Kartverket Matrikkel.
    """
    try:
        from services.municipality_connectors.eiendomsdata import get_eiendomsdata_adapter
        adapter = get_eiendomsdata_adapter()
        analyse = await adapter.hent_naboer(knr, gnr, bnr)
        return {
            "kommunenummer": analyse.kommunenummer,
            "gnr": analyse.gnr,
            "bnr": analyse.bnr,
            "antall_naboer": analyse.antall_naboer,
            "naboer": [
                {
                    "gnr": n.gnr,
                    "bnr": n.bnr,
                    "avstand_meter": n.avstand_meter,
                    "adresse": n.adresse,
                    "se_eiendom_url": f"https://seeiendom.kartverket.no/?kommunenr={knr}&gnr={n.gnr}&bnr={n.bnr}",
                }
                for n in analyse.naboer
            ],
            "feilmelding": analyse.feilmelding,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Nabooppslag feilet: {exc}")


@router.post(
    "/nabovarsel",
    summary="AI-generert nabovarsel",
    response_model=dict,
)
async def generer_nabovarsel(
    knr: Annotated[str, Query()],
    gnr: Annotated[int, Query()],
    bnr: Annotated[int, Query()],
    tiltaksbeskrivelse: Annotated[str, Query(description="Hva du planlegger å bygge")],
    tiltakstype: Annotated[str, Query()] = "tilbygg",
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Genererer et komplett nabovarsel-brev etter PBL §21-3 og SAK10 §6-2.

    Henter eiendomsdata fra Kartverket og bruker AI til å skrive et ferdig brev
    med korrekte lovhenvisninger, frist og eiendomsidentifikasjon.

    VIKTIG: Resultatet er beslutningsstøtte – ikke juridisk rådgivning.
    """
    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        from services.property_intelligence.analyzer import get_property_analyzer
        import anthropic
        import json

        # Hent eiendomsdata fra Kartverket
        adapter = get_kartverket_adapter()
        kartverket_result = await adapter.full_oppslag(knr, gnr, bnr, 0, 0)

        eiendom = None
        adresse = f"Gnr. {gnr}, Bnr. {bnr}"
        postnummer = ""
        poststed = ""
        areal_m2 = None
        kommunenavn = knr

        if not isinstance(kartverket_result, Exception):
            if kartverket_result.eiendom:
                e = kartverket_result.eiendom
                adresse = e.adresse or adresse
                postnummer = e.postnummer or ""
                poststed = e.poststed or ""
                areal_m2 = e.areal_m2
            if kartverket_result.kommune:
                kommunenavn = kartverket_result.kommune.kommunenavn or knr

        analyzer = get_property_analyzer()

        system_prompt = (
            "Du er en norsk byggesaksekspert som hjelper huseierne med å skrive korrekte nabovarsel "
            "etter plan- og bygningsloven. Dette er beslutningsstøtte – ikke juridisk rådgivning. "
            "Huseieren må selv kvalitetssikre innholdet og evt. konsultere faglig ansvarlig."
        )

        user_prompt = f"""Skriv et komplett nabovarsel-brev for følgende eiendom og tiltak:

## Eiendom
- Matrikkel: Gnr. {gnr}, Bnr. {bnr}, Kommune: {kommunenavn} (kommunenr: {knr})
- Adresse: {adresse}{f', {postnummer} {poststed}' if postnummer else ''}
- Tomteareal: {f'{areal_m2:.0f} m²' if areal_m2 else 'ukjent'}

## Tiltak
- Tiltakstype: {tiltakstype}
- Beskrivelse: {tiltaksbeskrivelse}

Brevet skal:
1. Følge kravene i PBL §21-3 og SAK10 §6-2
2. Inkludere avsender (med plassholder for navn/adresse/kontakt)
3. Tydelig identifisere eiendommen (gnr/bnr/adresse/kommunenavn)
4. Beskrive tiltaket klart og presist
5. Opplyse om naboens rett til merknader innen 2 uker (14 dager), jf. SAK10 §6-3
6. Opplyse om at nabovarselet gjelder som nabovarsel etter SAK10 §6-2
7. Inkludere plassholder for dato og underskrift
8. Ha en profesjonell og høflig tone

Svar BARE med gyldig JSON i dette formatet:
{{
  "nabovarsel_tekst": "Komplett brevtekst med linjeskift som \\n",
  "paragraf_referanser": ["PBL §21-3", "SAK10 §6-2", "SAK10 §6-3"],
  "tips": [
    "Tips 1 om nabovarslingsprosessen",
    "Tips 2 om hva som skjer videre"
  ]
}}"""

        # Kall Anthropic direkte (samme mønster som analyzer)
        import os
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.AsyncAnthropic(api_key=anthropic_key)
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        result_json = json.loads(text)

        return {
            "nabovarsel_tekst": result_json.get("nabovarsel_tekst", ""),
            "paragraf_referanser": result_json.get("paragraf_referanser", []),
            "tips": result_json.get("tips", []),
            "eiendom": {
                "knr": knr,
                "gnr": gnr,
                "bnr": bnr,
                "adresse": adresse,
                "kommunenavn": kommunenavn,
            },
        }

    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Nabovarsel-modulen er ikke tilgjengelig: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Nabovarsel-generering feilet: {exc}",
        )


@router.post(
    "/sjekkliste",
    summary="Byggesøknad-sjekkliste",
    response_model=dict,
)
async def generer_sjekkliste(
    knr: Annotated[str, Query()],
    gnr: Annotated[int, Query()],
    bnr: Annotated[int, Query()],
    tiltakstype: Annotated[
        str,
        Query(description="tilbygg|garasje|bruksendring|riving|nybygg|terrasse|carport"),
    ] = "tilbygg",
    areal_m2: Annotated[int | None, Query()] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Genererer en byggesøknad-sjekkliste for et planlagt tiltak.

    Henter plandata via Planslurpen og Kartverket og bruker AI til å:
    - Fastslå søknadstype (søknadspliktig / meldingspliktig / ikke søknadspliktig)
    - Liste opp nødvendige dokumenter
    - Sjekke reguleringsplan-krav mot Planslurpen-data
    - Identifisere relevante paragrafer

    VIKTIG: Sjekklisten er beslutningsstøtte – ikke juridisk rådgivning.
    """
    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        from services.municipality_connectors.planslurpen import get_planslurpen_adapter
        import anthropic
        import json

        # Hent eiendoms- og plandata parallelt
        kartverket = get_kartverket_adapter()
        planslurpen = get_planslurpen_adapter()

        kartverket_task = kartverket.full_oppslag(knr, gnr, bnr, 0, 0)
        planslurpen_task = planslurpen.hent_planbestemmelser(knr, gnr, bnr, 0, 0)

        kartverket_result, planslurpen_result = await asyncio.gather(
            kartverket_task, planslurpen_task, return_exceptions=True
        )

        # Ekstraher eiendomsdata
        adresse = f"Gnr. {gnr}, Bnr. {bnr}"
        tomt_areal = None
        kommunenavn = knr
        eksisterende_bygninger: list[dict] = []

        if not isinstance(kartverket_result, Exception):
            if kartverket_result.eiendom:
                e = kartverket_result.eiendom
                adresse = e.adresse or adresse
                tomt_areal = e.areal_m2
            if kartverket_result.kommune:
                kommunenavn = kartverket_result.kommune.kommunenavn or knr
            eksisterende_bygninger = [
                {
                    "type": b.bygningstype,
                    "areal_bra": b.bruksareal,
                    "byggeaar": b.byggeaar,
                }
                for b in (kartverket_result.bygninger or [])[:5]
            ]

        # Ekstraher planbestemmelser
        plandata_tekst = "Ingen planbestemmelser tilgjengelig."
        maks_hoyde = None
        maks_utnyttelse = None

        if not isinstance(planslurpen_result, Exception) and planslurpen_result.antall_planer > 0:
            planer_info = []
            for p in planslurpen_result.planer[:3]:
                if p.maks_hoyde and maks_hoyde is None:
                    maks_hoyde = p.maks_hoyde
                if p.maks_utnyttelse and maks_utnyttelse is None:
                    maks_utnyttelse = p.maks_utnyttelse
                planer_info.append(
                    f"Plan: {p.plan_navn} | Maks høyde: {p.maks_hoyde or 'ukjent'} | "
                    f"Maks utnyttelse: {p.maks_utnyttelse or 'ukjent'} | Tillatt bruk: {p.tillatt_bruk or 'ukjent'}"
                )
            plandata_tekst = "\n".join(planer_info)

        # Formater eksisterende bebyggelse
        byg_tekst = (
            "\n".join(
                f"- {b['type'] or 'Ukjent type'}, BRA={b['areal_bra'] or '?'} m², Byggeår={b['byggeaar'] or '?'}"
                for b in eksisterende_bygninger
            )
            if eksisterende_bygninger
            else "Ingen bygninger registrert"
        )

        system_prompt = (
            "Du er en norsk byggesaksekspert med dyp kunnskap om PBL, SAK10, TEK17 og kommunal byggesaksbehandling. "
            "Du hjelper arkitekter og huseierne med å forstå hvilke søknadskrav som gjelder for et tiltak. "
            "Dette er beslutningsstøtte – ikke juridisk rådgivning. Ansvarlig fagperson må alltid kvalitetssikre."
        )

        user_prompt = f"""Generer en detaljert byggesøknad-sjekkliste for følgende tiltak:

## Eiendom
- Matrikkel: Gnr. {gnr}, Bnr. {bnr}, Kommune: {kommunenavn} (kommunenr: {knr})
- Adresse: {adresse}
- Tomteareal: {f'{tomt_areal:.0f} m²' if tomt_areal else 'ukjent'}

## Eksisterende bebyggelse
{byg_tekst}

## Planlagt tiltak
- Tiltakstype: {tiltakstype}
- Tiltakets areal: {f'{areal_m2} m²' if areal_m2 else 'ikke oppgitt'}

## Gjeldende planbestemmelser
{plandata_tekst}
- Maks tillatt høyde: {maks_hoyde or 'ukjent'}
- Maks utnyttelsesgrad: {maks_utnyttelse or 'ukjent'}

Vurder søknadsplikten basert på PBL §20-1 (søknadspliktige tiltak), §20-2 (tiltak uten søknadsplikt) og SAK10 §3-1 (tiltak som krever søknad og ansvarsrett).

Svar BARE med gyldig JSON i dette formatet:
{{
  "soknadstype": "søknadspliktig|meldingspliktig|ikke søknadspliktig",
  "soknadstype_begrunnelse": "Kort forklaring på hvorfor",
  "dokumenter": [
    {{
      "navn": "Dokumentnavn",
      "beskrivelse": "Hva dokumentet skal inneholde",
      "mal_url": null
    }}
  ],
  "sjekkliste": [
    {{
      "punkt": "Hva som skal gjøres/sjekkes",
      "status": "todo",
      "paragraf": "PBL §20-1"
    }}
  ],
  "advarsler": [
    "Advarsel om spesielle forhold som gjelder for dette tiltaket"
  ]
}}

Inkluder minst:
- Alle nødvendige dokumenter (situasjonsplan, fasadetegninger, nabovarsel, søknadsskjema etc.)
- 8-15 konkrete sjekkliste-punkter med paragrafhenvisninger
- Eventuelle advarsler om reguleringsplan-avvik, nabovarslingskrav etc."""

        import os
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.AsyncAnthropic(api_key=anthropic_key)
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        result_json = json.loads(text)

        return {
            "soknadstype": result_json.get("soknadstype", "søknadspliktig"),
            "soknadstype_begrunnelse": result_json.get("soknadstype_begrunnelse", ""),
            "dokumenter": result_json.get("dokumenter", []),
            "sjekkliste": result_json.get("sjekkliste", []),
            "advarsler": result_json.get("advarsler", []),
            "eiendom": {
                "knr": knr,
                "gnr": gnr,
                "bnr": bnr,
                "adresse": adresse,
                "kommunenavn": kommunenavn,
            },
        }

    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sjekkliste-modulen er ikke tilgjengelig: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sjekkliste-generering feilet: {exc}",
        )


@router.get(
    "/rapport-pdf",
    summary="Last ned eiendomsrapport som PDF",
    response_class=Response,
)
async def download_rapport_pdf(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fnr: Annotated[int | None, Query()] = None,
    snr: Annotated[int | None, Query()] = None,
    current_user: User = Depends(get_optional_user),
):
    """
    Henter all tilgjengelig eiendomsdata og genererer en komplett PDF-rapport.
    """
    try:
        # Hent full eiendomsdata (gjenbruk logikk fra /full)
        from services.municipality_connectors.kartverket import (
            get_kartverket_adapter, bygg_se_eiendom_url,
        )
        from services.municipality_connectors.arealplaner import (
            get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
            EiendomsoppslagResult,
        )
        from services.municipality_connectors.eiendomsdata import get_eiendomsdata_adapter
        from services.reporting.pdf_rapport import generer_eiendomsrapport

        kartverket = get_kartverket_adapter()
        kartverket_task = kartverket.full_oppslag(knr, gnr, bnr, fnr or 0, snr or 0)

        if knr == "3212":
            arealplaner_task = get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, fnr, snr)
        else:
            async def _arealplaner():
                dok = get_dok_adapter()
                plan = get_arealplaner_adapter()
                dok_r, plan_r = await asyncio.gather(
                    dok.analyse_eiendom(knr, gnr, bnr, fnr, snr),
                    plan.hent_planrapport(knr, gnr, bnr, fnr, snr),
                    return_exceptions=True,
                )
                r = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
                if not isinstance(dok_r, Exception): r.dok_analyse = dok_r
                if not isinstance(plan_r, Exception): r.planrapport = plan_r
                return r
            arealplaner_task = _arealplaner()

        kartverket_result, arealplaner_result = await asyncio.gather(
            kartverket_task, arealplaner_task, return_exceptions=True
        )

        eiendom_data: dict = {"kommunenummer": knr, "gnr": gnr, "bnr": bnr}

        bygninger_raw: list = []
        eiendom_raw = None
        if not isinstance(kartverket_result, Exception):
            kr = kartverket_result
            eiendom_raw = _serialize_eiendom(kr.eiendom)
            bygninger_raw = [_serialize_bygning(b) for b in kr.bygninger]
            eiendom_data["eiendom"] = eiendom_raw
            eiendom_data["bygninger"] = bygninger_raw
            eiendom_data["byggesaker"] = [_serialize_byggesak(s) for s in kr.byggesaker]
            eiendom_data["kommune"] = {
                "kommunenummer": kr.kommune.kommunenummer if kr.kommune else knr,
                "kommunenavn": kr.kommune.kommunenavn if kr.kommune else knr,
            }

        if not isinstance(arealplaner_result, Exception):
            arealdata = _serialize_oppslag(arealplaner_result)
            eiendom_data["planrapport"] = arealdata.get("planrapport")

        try:
            eiendomsdata_adapter = get_eiendomsdata_adapter()
            historikk = await eiendomsdata_adapter.hent_historikk(
                kommunenummer=knr, gnr=gnr, bnr=bnr,
                bygninger=bygninger_raw or None, eiendom=eiendom_raw,
            )
            eiendom_data["verdiestimator"] = {
                "estimert_verdi": historikk.estimert_verdi,
                "konfidensintervall": list(historikk.estimat_konfidensintervall) if historikk.estimat_konfidensintervall else None,
                "estimat_metode": historikk.estimat_metode,
                "pris_per_kvm": historikk.pris_per_kvm,
                "kommune_median_pris": historikk.kommune_median_pris,
                "kommune_prisvekst_prosent": historikk.kommune_prisvekst_prosent,
            }
        except Exception:
            pass

        pdf_bytes = generer_eiendomsrapport(eiendom_data)
        adresse = (eiendom_data.get("eiendom") or {}).get("adresse") or f"gnr{gnr}_bnr{bnr}"
        safe_navn = "".join(c if c.isalnum() or c in "-_ " else "_" for c in adresse).strip()
        filename = f"ByggSjekk_{safe_navn}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"PDF-generator ikke tilgjengelig: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"PDF-generering feilet: {exc}")


# ---------------------------------------------------------------------------
# Gebyrberegning endepunkt
# ---------------------------------------------------------------------------


@router.post(
    "/gebyrberegning",
    summary="Beregn kommunale gebyrer for et byggetiltak",
    response_model=dict,
)
async def beregn_kommunale_gebyrer(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    tiltakstype: Annotated[
        str,
        Query(description="Tiltakstype: tilbygg|garasje|nybygg|bruksendring|riving|terrasse|fasadeendring|carport|uthus|tomannsbolig"),
    ] = "tilbygg",
    areal_m2: Annotated[int | None, Query(description="Planlagt bruksareal i m²")] = None,
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Beregner forventede kommunale gebyrer for et byggetiltak.

    For Nesodden (knr=3212) brukes faktiske gebyrregulativ-satser for 2026.
    For øvrige kommuner returneres estimater basert på typiske norske satser.

    Inkluderer alltid: grunngebyr, tilsynsgebyr, registreringsgebyr,
    situasjonskart og ferdigattest.
    """
    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        from services.regulations.gebyrberegning import beregn_gebyrer

        # Hent kommunenavn fra Kartverket (best-effort)
        kommunenavn = knr
        try:
            kartverket = get_kartverket_adapter()
            kr = await kartverket.full_oppslag(knr, gnr, bnr, 0, 0)
            if not isinstance(kr, Exception) and kr.kommune:
                kommunenavn = kr.kommune.kommunenavn or knr
        except Exception:
            pass

        resultat = beregn_gebyrer(
            kommunenummer=knr,
            kommunenavn=kommunenavn,
            tiltakstype=tiltakstype,
            areal_m2=areal_m2,
        )

        return {
            "kommunenummer": resultat.kommunenummer,
            "kommunenavn": resultat.kommunenavn,
            "tiltakstype": resultat.tiltakstype,
            "areal_m2": resultat.areal_m2,
            "total_gebyr": resultat.total_gebyr,
            "gebyrer": [
                {
                    "navn": g.navn,
                    "belop": g.belop,
                    "beskrivelse": g.beskrivelse,
                    "alltid_med": g.alltid_med,
                }
                for g in resultat.gebyrer
            ],
            "notat": resultat.notat,
            "kilde": resultat.kilde,
            "disclaimer": resultat.disclaimer,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gebyrberegning feilet: {exc}",
        )


# ---------------------------------------------------------------------------
# Innsynsbegjæring – automatisk e-post til kommunen
# ---------------------------------------------------------------------------


@router.post(
    "/innsyn-tegninger",
    summary="Send innsynsbegjæring for godkjente tegninger til kommunen",
    response_model=dict,
)
async def send_innsyn_tegninger(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    current_user=Depends(get_optional_user),
) -> dict:
    """
    Sender automatisk innsynsbegjæring til kommunen for godkjente tegninger.

    E-posten ber om innsyn jf. Grunnloven §100 og offentleglova §3 i:
    - Sist godkjente situasjonskart
    - Sist godkjente plantegninger
    - Sist godkjente fasadetegninger
    - Sist godkjente snitt-tegninger
    - Tilhørende byggesaksdokumenter

    Sendes fra hey@nops.no til kommunens postmottak.
    """
    try:
        from app.services.email import (
            send_innsynsbegjæring_tegninger,
            hent_kommune_epost,
        )
        from app.core.config import settings

        # Hent eiendomsdata for adresse og kommunenavn
        adresse = f"Gnr. {gnr}, Bnr. {bnr}"
        kommunenavn = knr
        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            kartverket = get_kartverket_adapter()
            kr = await kartverket.full_oppslag(knr, gnr, bnr, 0, 0)
            if not isinstance(kr, Exception):
                if kr.eiendom and kr.eiendom.adresse:
                    adresse = kr.eiendom.adresse
                    if kr.eiendom.postnummer and kr.eiendom.poststed:
                        adresse += f", {kr.eiendom.postnummer} {kr.eiendom.poststed}"
                if kr.kommune:
                    kommunenavn = kr.kommune.kommunenavn or knr
        except Exception:
            pass

        # Finn kommune-e-post
        kommune_epost = hent_kommune_epost(knr, kommunenavn)
        if not kommune_epost:
            return {
                "sendt": False,
                "grunn": f"Kunne ikke finne e-postadresse for kommune {knr} ({kommunenavn}). Kontakt kommunen direkte.",
                "kommune_epost": None,
            }

        # Bruker-info
        bruker_navn = "nops.no på vegne av eier"
        if current_user:
            bruker_navn = getattr(current_user, "full_name", None) or bruker_navn
        svar_epost = "hey@nops.no"

        # Send e-post
        sendt = await send_innsynsbegjæring_tegninger(
            kommune_epost=kommune_epost,
            kommunenavn=kommunenavn,
            knr=knr,
            gnr=gnr,
            bnr=bnr,
            adresse=adresse,
            bruker_navn=bruker_navn,
            svar_epost=svar_epost,
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_user=settings.SMTP_USER,
            smtp_password=settings.SMTP_PASSWORD,
        )

        return {
            "sendt": sendt,
            "kommune_epost": kommune_epost,
            "kommunenavn": kommunenavn,
            "adresse": adresse,
            "gnr": gnr,
            "bnr": bnr,
            "melding": (
                f"Innsynsbegjæring sendt til {kommune_epost} for {adresse} ({gnr}/{bnr}). "
                f"Kommunen svarer normalt innen 1–3 virkedager."
            ) if sendt else "Sending feilet. Prøv igjen senere.",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Innsynsbegjæring feilet: {exc}",
        )
