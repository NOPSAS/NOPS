"""
ByggSjekk – Bestemmelser-oppsummering.

Henter og oppsummerer reguleringsbestemmelser og kommuneplanbestemmelser
for en eiendom. Brukes som grunnlag for alle NOPS-tjenester.

GET /bestemmelser/oppsummering – AI-oppsummert oversikt over hva som gjelder
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_optional_user

router = APIRouter()

for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


@router.get(
    "/oppsummering",
    summary="Oppsummering av regulerings- og kommuneplanbestemmelser",
    response_model=dict,
)
async def bestemmelser_oppsummering(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    current_user=Depends(get_optional_user),
) -> dict:
    """
    Henter og oppsummerer alle gjeldende bestemmelser for en eiendom:

    1. Reguleringsplan (arealformål, bestemmelser, planstatus)
    2. Kommuneplan (overordnede bestemmelser)
    3. Planslurpen (AI-strukturerte krav: høyde, utnyttelse, bruk)
    4. DOK-analyse (berørte kartdatasett)
    5. Dispensasjonshistorikk

    Returnerer en strukturert oversikt som brukes av alle NOPS-tjenester
    (tilbygg, tomtedeling, dispensasjon, etc.)
    """
    try:
        # ── Hent alt parallelt ──────────────────────────────────
        eiendom_info = {"knr": knr, "gnr": gnr, "bnr": bnr}
        adresse = f"Gnr. {gnr}, Bnr. {bnr}"
        kommunenavn = knr
        tomteareal = None

        tasks = {}

        # Kartverket
        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            tasks["kartverket"] = get_kartverket_adapter().full_oppslag(knr, gnr, bnr, 0, 0)
        except ImportError:
            pass

        # Planslurpen
        try:
            from services.municipality_connectors.planslurpen import get_planslurpen_adapter
            tasks["planslurpen"] = get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, 0, 0)
        except ImportError:
            pass

        # Arealplaner/DOK
        try:
            from services.municipality_connectors.arealplaner import (
                get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
                EiendomsoppslagResult,
            )
            if knr == "3212":
                tasks["arealplaner"] = get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, None, None)
            else:
                async def _arealplaner():
                    dok = get_dok_adapter()
                    plan = get_arealplaner_adapter()
                    dok_r, plan_r = await asyncio.gather(
                        dok.analyse_eiendom(knr, gnr, bnr, None, None),
                        plan.hent_planrapport(knr, gnr, bnr, None, None),
                        return_exceptions=True,
                    )
                    r = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
                    if not isinstance(dok_r, Exception):
                        r.dok_analyse = dok_r
                    if not isinstance(plan_r, Exception):
                        r.planrapport = plan_r
                    return r
                tasks["arealplaner"] = _arealplaner()
        except ImportError:
            pass

        results = {}
        if tasks:
            gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for key, result in zip(tasks.keys(), gathered):
                if not isinstance(result, Exception):
                    results[key] = result

        # ── Ekstraher data ──────────────────────────────────────
        # Kartverket
        kr = results.get("kartverket")
        if kr:
            if kr.eiendom:
                adresse = kr.eiendom.adresse or adresse
                tomteareal = kr.eiendom.areal_m2
            if kr.kommune:
                kommunenavn = kr.kommune.kommunenavn or knr

        eiendom_info.update({
            "adresse": adresse,
            "kommunenavn": kommunenavn,
            "tomteareal_m2": tomteareal,
        })

        # Planslurpen
        planbestemmelser = []
        ps = results.get("planslurpen")
        if ps and hasattr(ps, "antall_planer") and ps.antall_planer > 0:
            for p in ps.planer[:5]:
                planbestemmelser.append({
                    "plan_navn": p.plan_navn,
                    "maks_hoyde": p.maks_hoyde,
                    "maks_utnyttelse": p.maks_utnyttelse,
                    "tillatt_bruk": p.tillatt_bruk,
                })

        # Arealplaner
        gjeldende_planer = []
        dispensasjoner = []
        dok_datasett = []

        ap = results.get("arealplaner")
        if ap:
            pr = getattr(ap, "planrapport", ap)
            if hasattr(pr, "gjeldende_planer") and pr.gjeldende_planer:
                for p in pr.gjeldende_planer[:5]:
                    gjeldende_planer.append({
                        "plan_navn": getattr(p, "plan_navn", ""),
                        "plan_type": getattr(p, "plan_type", ""),
                        "arealformaal": getattr(p, "arealformål", ""),
                        "status": getattr(p, "status", ""),
                    })
            if hasattr(pr, "dispensasjoner") and pr.dispensasjoner:
                for d in pr.dispensasjoner[:10]:
                    dispensasjoner.append({
                        "beskrivelse": getattr(d, "beskrivelse", getattr(d, "saks_type", "")),
                        "status": getattr(d, "status", ""),
                    })

            da = getattr(ap, "dok_analyse", None)
            if da and hasattr(da, "berørte_datasett"):
                for ds in da.berørte_datasett[:10]:
                    dok_datasett.append({
                        "navn": getattr(ds, "navn", ""),
                        "tema": getattr(ds, "tema", ""),
                    })

        # ── AI-oppsummering ─────────────────────────────────────
        ai_oppsummering = None
        try:
            import anthropic

            kontekst = f"""Eiendom: {adresse}, {kommunenavn} ({knr}), Gnr {gnr}/Bnr {bnr}
Tomteareal: {f'{tomteareal:.0f} m²' if tomteareal else 'ukjent'}

Gjeldende planer:
{json.dumps(gjeldende_planer, indent=2, ensure_ascii=False) if gjeldende_planer else 'Ingen'}

Planbestemmelser (Planslurpen):
{json.dumps(planbestemmelser, indent=2, ensure_ascii=False) if planbestemmelser else 'Ingen'}

Dispensasjoner:
{json.dumps(dispensasjoner, indent=2, ensure_ascii=False) if dispensasjoner else 'Ingen'}

DOK-berørte datasett:
{json.dumps(dok_datasett, indent=2, ensure_ascii=False) if dok_datasett else 'Ingen'}"""

            client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": f"""Gi en kort, praktisk oppsummering av hva som gjelder for denne eiendommen.
Skriv for en huseier som ikke er fagperson.

{kontekst}

Svar BARE med gyldig JSON:
{{
  "oppsummering": "2-4 setninger om hva som gjelder for eiendommen",
  "hva_kan_bygges": "Kort beskrivelse av hva man kan bygge/endre",
  "begrensninger": ["Begrensning 1", "Begrensning 2"],
  "muligheter": ["Mulighet 1", "Mulighet 2"],
  "viktige_bestemmelser": [
    {{"bestemmelse": "Maks BYA 20%", "kilde": "Reguleringsplan", "betydning": "Hva dette betyr i praksis"}},
    {{"bestemmelse": "Maks gesimshøyde 8m", "kilde": "Kommuneplan", "betydning": "..."}}
  ],
  "dok_varsler": ["Viktig DOK-varsel 1"],
  "dispensasjoner_gitt": {len(dispensasjoner)},
  "dispensasjoner_relevans": "Kort om hva dispensasjonene betyr for fremtidige søknader"
}}""",
                }],
            )
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.rsplit("```", 1)[0].strip()
            ai_oppsummering = json.loads(text)
        except Exception:
            pass

        return {
            "eiendom": eiendom_info,
            "gjeldende_planer": gjeldende_planer,
            "planbestemmelser": planbestemmelser,
            "dispensasjoner": dispensasjoner,
            "dok_berørte_datasett": dok_datasett,
            "ai_oppsummering": ai_oppsummering,
            "se_eiendom_url": f"https://seeiendom.kartverket.no/?kommunenr={knr}&gnr={gnr}&bnr={bnr}",
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bestemmelsesoppslag feilet: {exc}")
