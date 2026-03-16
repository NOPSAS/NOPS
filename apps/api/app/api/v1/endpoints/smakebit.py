"""
ByggSjekk – Smakebit / Gratis eiendomsprofil.

Gir en gratis "smakebit" av alle NOPS-tjenester for enhver eiendom.
Nok til at kunden får verdi – men lite nok til at de vil kjøpe mer.

GET /smakebit/{knr}/{gnr}/{bnr} – Gratis eiendomsprofil med smakebit av alle tjenester
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

router = APIRouter()

for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


@router.get(
    "/{knr}/{gnr}/{bnr}",
    summary="Gratis eiendomsprofil – smakebit av alle NOPS-tjenester",
    response_model=dict,
)
async def smakebit(
    knr: Annotated[str, Path(description="Kommunenummer")],
    gnr: Annotated[int, Path(description="Gårdsnummer")],
    bnr: Annotated[int, Path(description="Bruksnummer")],
) -> dict:
    """
    Gratis eiendomsprofil som gir en smakebit av ALLE tjenester.
    Ingen auth nødvendig – åpen for alle.

    Viser nok til at kunden ser verdien, men begrenser detaljer
    slik at de vil oppgradere for full tilgang.

    Returnerer:
    - Grunndata (adresse, areal, byggeår, bygningstype)
    - Antall byggesaker (men ikke detaljer)
    - Reguleringsplan-sammendrag (men ikke bestemmelser)
    - DOK-treff (antall berørte, men ikke hvilke)
    - Verdiindikator (prisklasse, men ikke eksakt estimat)
    - Tilbygg-potensial (ja/nei, men ikke arealregnestykke)
    - Dispensasjonshistorikk (antall, men ikke innhold)
    - Ferdigattest-status (ja/nei)
    - CTA-er til betalte tjenester
    """
    try:
        resultat = {
            "eiendom": {"knr": knr, "gnr": gnr, "bnr": bnr},
            "grunndata": {},
            "byggesaker_smakebit": {},
            "reguleringsplan_smakebit": {},
            "dok_smakebit": {},
            "verdi_smakebit": {},
            "tilbygg_smakebit": {},
            "dispensasjon_smakebit": {},
            "ferdigattest_smakebit": {},
            "tjenester_cta": [],
        }

        # ── Hent alt parallelt ──────────────────────────────────
        tasks = {}

        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            tasks["kartverket"] = get_kartverket_adapter().full_oppslag(knr, gnr, bnr, 0, 0)
        except ImportError:
            pass

        try:
            from services.municipality_connectors.planslurpen import get_planslurpen_adapter
            tasks["planslurpen"] = get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, 0, 0)
        except ImportError:
            pass

        try:
            from services.municipality_connectors.arealplaner import (
                get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
                EiendomsoppslagResult,
            )
            if knr == "3212":
                tasks["arealplaner"] = get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, None, None)
            else:
                async def _ap():
                    dok = get_dok_adapter()
                    plan = get_arealplaner_adapter()
                    d, p = await asyncio.gather(
                        dok.analyse_eiendom(knr, gnr, bnr, None, None),
                        plan.hent_planrapport(knr, gnr, bnr, None, None),
                        return_exceptions=True,
                    )
                    r = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
                    if not isinstance(d, Exception):
                        r.dok_analyse = d
                    if not isinstance(p, Exception):
                        r.planrapport = p
                    return r
                tasks["arealplaner"] = _ap()
        except ImportError:
            pass

        try:
            from services.municipality_connectors.eiendomsdata import get_eiendomsdata_adapter
            tasks["verdi"] = get_eiendomsdata_adapter().hent_historikk(
                kommunenummer=knr, gnr=gnr, bnr=bnr
            )
        except ImportError:
            pass

        results = {}
        if tasks:
            gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for key, result in zip(tasks.keys(), gathered):
                if not isinstance(result, Exception):
                    results[key] = result

        # ── Grunndata (GRATIS – vises fullt) ────────────────────
        kr = results.get("kartverket")
        if kr:
            e = kr.eiendom
            resultat["grunndata"] = {
                "adresse": e.adresse if e else None,
                "postnummer": e.postnummer if e else None,
                "poststed": e.poststed if e else None,
                "kommunenavn": kr.kommune.kommunenavn if kr.kommune else knr,
                "tomteareal_m2": e.areal_m2 if e else None,
            }
            resultat["eiendom"]["adresse"] = e.adresse if e else f"Gnr. {gnr}, Bnr. {bnr}"
            resultat["eiendom"]["kommunenavn"] = kr.kommune.kommunenavn if kr.kommune else knr

            # Bygninger – vis type og byggeår, men SKJUL BRA
            if kr.bygninger:
                b0 = kr.bygninger[0]
                resultat["grunndata"]["bygningstype"] = b0.bygningstype
                resultat["grunndata"]["byggeaar"] = b0.byggeaar
                resultat["grunndata"]["antall_bygninger"] = len(kr.bygninger)
                resultat["grunndata"]["bruksareal_hint"] = "Oppgrader for å se bruksareal"

            # Byggesaker – vis ANTALL, ikke detaljer
            resultat["byggesaker_smakebit"] = {
                "antall_saker": len(kr.byggesaker) if kr.byggesaker else 0,
                "detaljer": "Oppgrader til Starter for å se byggesakshistorikk",
                "har_ferdigattest": any(
                    "ferdigattest" in (getattr(s, "status", "") or "").lower()
                    for s in (kr.byggesaker or [])
                ),
            }

            # Ferdigattest
            har_fa = resultat["byggesaker_smakebit"]["har_ferdigattest"]
            resultat["ferdigattest_smakebit"] = {
                "status": "Ferdigattest funnet" if har_fa else "Ingen ferdigattest registrert",
                "cta": "Gratis sjekk og hjelp med ferdigattest" if not har_fa else None,
                "lenke": "/ferdigattest",
            }

        # ── Reguleringsplan (SMAKEBIT – vis plannavn, skjul bestemmelser) ──
        ap = results.get("arealplaner")
        if ap:
            pr = getattr(ap, "planrapport", ap)
            if hasattr(pr, "gjeldende_planer") and pr.gjeldende_planer:
                resultat["reguleringsplan_smakebit"] = {
                    "antall_planer": len(pr.gjeldende_planer),
                    "plan_navn": pr.gjeldende_planer[0].plan_navn if pr.gjeldende_planer else None,
                    "plan_type": getattr(pr.gjeldende_planer[0], "plan_type", None) if pr.gjeldende_planer else None,
                    "bestemmelser": "Oppgrader for å se planbestemmelser og arealformål",
                }

            # Dispensasjoner – vis ANTALL
            if hasattr(pr, "dispensasjoner") and pr.dispensasjoner:
                resultat["dispensasjon_smakebit"] = {
                    "antall_dispensasjoner": len(pr.dispensasjoner),
                    "detaljer": "Oppgrader for å se dispensasjonshistorikk",
                    "hint": f"{len(pr.dispensasjoner)} dispensasjon(er) registrert – dette kan være relevant for din byggesøknad",
                    "lenke": "/dispensasjon",
                }
            else:
                resultat["dispensasjon_smakebit"] = {
                    "antall_dispensasjoner": 0,
                    "hint": "Ingen dispensasjoner registrert",
                }

            # DOK – vis ANTALL berørte
            da = getattr(ap, "dok_analyse", None)
            if da and hasattr(da, "berørte_datasett"):
                resultat["dok_smakebit"] = {
                    "antall_berørt": len(da.berørte_datasett),
                    "antall_ikke_berørt": getattr(da, "antall_ikke_berørt", 0),
                    "datasett_navn": "Oppgrader for å se hvilke datasett som er berørt",
                    "hint": f"{len(da.berørte_datasett)} kartdatasett berører eiendommen din" if da.berørte_datasett else "Ingen DOK-treff",
                }

        # ── Planslurpen (SMAKEBIT – vis at vi har data, skjul tall) ──
        ps = results.get("planslurpen")
        if ps and hasattr(ps, "antall_planer") and ps.antall_planer > 0:
            p0 = ps.planer[0]
            resultat["reguleringsplan_smakebit"]["har_hoydegrense"] = bool(p0.maks_hoyde)
            resultat["reguleringsplan_smakebit"]["har_utnyttelsesgrad"] = bool(p0.maks_utnyttelse)
            resultat["reguleringsplan_smakebit"]["har_bruksbegrensning"] = bool(p0.tillatt_bruk)

            # Tilbygg-hint basert på data
            if p0.maks_utnyttelse:
                resultat["tilbygg_smakebit"] = {
                    "potensial": "Mulig utbygging registrert",
                    "detaljer": "Kjør tilbygganalyse for å se arealregnestykke og maks m²",
                    "lenke": "/property",
                }
            else:
                resultat["tilbygg_smakebit"] = {
                    "potensial": "Utnyttelsesgrad ikke funnet i plan",
                    "detaljer": "Kontakt oss for manuell vurdering",
                }

        # ── Verdi (SMAKEBIT – prisklasse, ikke eksakt) ──────────
        verdi = results.get("verdi")
        if verdi and hasattr(verdi, "estimert_verdi") and verdi.estimert_verdi:
            ev = verdi.estimert_verdi
            if ev < 2_000_000:
                prisklasse = "Under 2 mill"
            elif ev < 4_000_000:
                prisklasse = "2–4 mill"
            elif ev < 6_000_000:
                prisklasse = "4–6 mill"
            elif ev < 8_000_000:
                prisklasse = "6–8 mill"
            elif ev < 10_000_000:
                prisklasse = "8–10 mill"
            else:
                prisklasse = "Over 10 mill"
            resultat["verdi_smakebit"] = {
                "prisklasse": prisklasse,
                "eksakt_estimat": "Oppgrader til Starter for eksakt verdiestimering",
                "prisvekst_hint": f"Prisvekst i kommunen: {verdi.kommune_prisvekst_prosent:.1f}%" if verdi.kommune_prisvekst_prosent else None,
            }

        # ── CTA-er til betalte tjenester ────────────────────────
        resultat["tjenester_cta"] = [
            {
                "tjeneste": "AI-risikoanalyse",
                "beskrivelse": "Full AI-analyse av avvik, dispensasjonsbehov og reguleringsplan",
                "pris": "Starter-plan (499 kr/mnd)",
                "lenke": "/property",
            },
            {
                "tjeneste": "Tilbygg-analyse",
                "beskrivelse": "Komplett arealregnestykke – se nøyaktig hvor mye du kan bygge",
                "pris": "Gratis grunnberegning",
                "lenke": "/property",
            },
            {
                "tjeneste": "Dispensasjonssøknad",
                "beskrivelse": "AI-generert dispensasjonssøknad med fordel/ulempe-vurdering",
                "pris": "Starter-plan",
                "lenke": "/dispensasjon",
            },
            {
                "tjeneste": "Tomtedeling",
                "beskrivelse": "Sjekk om eiendommen kan deles – med arealregnestykke",
                "pris": "Starter-plan",
                "lenke": "/tomtedeling",
            },
            {
                "tjeneste": "Investeringsanalyse",
                "beskrivelse": "Yield, ROI og cashflow-beregning",
                "pris": "Gratis",
                "lenke": "/investering",
            },
            {
                "tjeneste": "Godkjente tegninger",
                "beskrivelse": "Vi innhenter sist godkjente tegninger fra kommunen – gratis",
                "pris": "Gratis",
                "lenke": "/dokumenter",
            },
            {
                "tjeneste": "Komplett pakke",
                "beskrivelse": "Alt automatisk: matrikkel, byggesaker, AI-analyse, renders, PDF",
                "pris": "Fra 2 490 kr",
                "lenke": "/pakke",
            },
        ]

        resultat["se_eiendom_url"] = f"https://seeiendom.kartverket.no/?kommunenr={knr}&gnr={gnr}&bnr={bnr}"

        return resultat

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Smakebit feilet: {exc}")
