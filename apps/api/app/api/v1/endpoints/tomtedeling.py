"""
ByggSjekk – Tomtedelingsanalyse.

Sjekker om en eiendom kan deles basert på:
1. Reguleringsplan/kommuneplan (tillater deling?)
2. Arealformål (bolig, vei, natur, friområde etc.)
3. Minste tomtestørrelse i planbestemmelsene
4. Faktisk tilgjengelig areal for bolig
5. Dispensasjonshistorikk i planen
6. AI-vurdering av muligheter

POST /tomtedeling/analyser
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_optional_user, require_ai_access

router = APIRouter()

for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


@router.post(
    "/analyser",
    summary="Tomtedelingsanalyse – kan eiendommen deles?",
    response_model=dict,
)
async def analyser_tomtedeling(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    ønsket_antall_tomter: Annotated[int, Query()] = 2,
    tilleggsinformasjon: Annotated[str, Query()] = "",
    current_user=Depends(require_ai_access),
) -> dict:
    """
    Komplett tomtedelingsanalyse:

    1. Henter matrikkeldata (tomteareal, bygninger)
    2. Henter planrapport (reguleringsplan, kommuneplan, bestemmelser)
    3. Henter planbestemmelser via Planslurpen (minste tomtestørrelse, arealformål)
    4. Sjekker dispensasjonshistorikk
    5. Beregner arealregnestykke (tilgjengelig boligareal vs krav)
    6. AI-vurdering av delingsmulighet
    """
    try:
        import anthropic

        # ── Hent data parallelt ─────────────────────────────────
        kartverket_data = None
        planrapport_data = None
        planbestemmelser_data = None

        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            kartverket = get_kartverket_adapter()
            kartverket_data = await kartverket.full_oppslag(knr, gnr, bnr, 0, 0)
            if isinstance(kartverket_data, Exception):
                kartverket_data = None
        except Exception:
            pass

        try:
            from services.municipality_connectors.arealplaner import (
                get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
                EiendomsoppslagResult,
            )
            if knr == "3212":
                planrapport_data = await get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, None, None)
            else:
                plan = get_arealplaner_adapter()
                planrapport_data = await plan.hent_planrapport(knr, gnr, bnr, None, None)
            if isinstance(planrapport_data, Exception):
                planrapport_data = None
        except Exception:
            pass

        try:
            from services.municipality_connectors.planslurpen import get_planslurpen_adapter
            planbestemmelser_data = await get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, 0, 0)
            if isinstance(planbestemmelser_data, Exception):
                planbestemmelser_data = None
        except Exception:
            pass

        # ── Ekstraher nøkkeldata ────────────────────────────────
        tomteareal = None
        adresse = f"Gnr. {gnr}, Bnr. {bnr}"
        kommunenavn = knr
        bygninger_tekst = "Ingen bygningsdata."

        if kartverket_data:
            if kartverket_data.eiendom:
                tomteareal = kartverket_data.eiendom.areal_m2
                adresse = kartverket_data.eiendom.adresse or adresse
            if kartverket_data.kommune:
                kommunenavn = kartverket_data.kommune.kommunenavn or knr
            if kartverket_data.bygninger:
                bygninger_tekst = "\n".join(
                    f"- {b.bygningstype or 'Ukjent'}, BRA={b.bruksareal or '?'} m², Byggeår={b.byggeaar or '?'}"
                    for b in kartverket_data.bygninger[:5]
                )

        # Planrapport-tekst
        plan_tekst = "Ingen planrapport tilgjengelig."
        dispensasjoner_tekst = "Ingen registrerte dispensasjoner."
        gjeldende_planer = []

        if planrapport_data:
            pr = getattr(planrapport_data, "planrapport", planrapport_data)
            if hasattr(pr, "gjeldende_planer") and pr.gjeldende_planer:
                gjeldende_planer = pr.gjeldende_planer
                plan_tekst = "\n".join(
                    f"- {p.plan_navn}: Formål={getattr(p, 'arealformål', '?')}, Status={getattr(p, 'status', '?')}"
                    for p in gjeldende_planer[:5]
                )
            if hasattr(pr, "dispensasjoner") and pr.dispensasjoner:
                dispensasjoner_tekst = "\n".join(
                    f"- {getattr(d, 'beskrivelse', getattr(d, 'saks_type', 'Ukjent'))}: Status={getattr(d, 'status', '?')}"
                    for d in pr.dispensasjoner[:10]
                )

        # Planbestemmelser
        maks_utnyttelse = None
        maks_hoyde = None
        tillatt_bruk = None
        plan_bestemmelser_tekst = "Ingen planbestemmelser fra Planslurpen."

        if planbestemmelser_data and planbestemmelser_data.antall_planer > 0:
            planer_info = []
            for p in planbestemmelser_data.planer[:3]:
                if p.maks_utnyttelse:
                    maks_utnyttelse = p.maks_utnyttelse
                if p.maks_hoyde:
                    maks_hoyde = p.maks_hoyde
                if p.tillatt_bruk:
                    tillatt_bruk = p.tillatt_bruk
                planer_info.append(
                    f"Plan: {p.plan_navn} | Maks utnyttelse: {p.maks_utnyttelse or 'ukjent'} | "
                    f"Maks høyde: {p.maks_hoyde or 'ukjent'} | Tillatt bruk: {p.tillatt_bruk or 'ukjent'}"
                )
            plan_bestemmelser_tekst = "\n".join(planer_info)

        # ── AI-analyse ──────────────────────────────────────────
        user_prompt = f"""Analyser om denne eiendommen kan deles (fradeling/tomtedeling) i {ønsket_antall_tomter} tomter.

## Eiendom
- Adresse: {adresse}
- Kommune: {kommunenavn} (kommunenr: {knr})
- Gnr/Bnr: {gnr}/{bnr}
- Tomteareal: {f'{tomteareal:.0f} m²' if tomteareal else 'ukjent'}

## Eksisterende bebyggelse
{bygninger_tekst}

## Gjeldende reguleringsplan/kommuneplan
{plan_tekst}

## Planbestemmelser (fra Planslurpen)
{plan_bestemmelser_tekst}

## Dispensasjonshistorikk
{dispensasjoner_tekst}

## Brukerens tilleggsinfo
{tilleggsinformasjon or 'Ingen'}

Gjør en komplett vurdering og svar BARE med gyldig JSON:
{{
  "kan_deles": true,
  "konklusjon": "Kort konklusjon (2-3 setninger)",
  "arealregnestykke": {{
    "total_tomteareal_m2": {tomteareal or 0},
    "areal_avsatt_vei_m2": 0,
    "areal_avsatt_natur_friomrade_m2": 0,
    "areal_avsatt_annet_m2": 0,
    "netto_boligareal_m2": 0,
    "minste_tomtestorrelse_m2": 0,
    "minste_tomtestorrelse_kilde": "Reguleringsplan/Kommuneplan/TEK17",
    "antall_mulige_tomter": 0,
    "restareal_m2": 0
  }},
  "reguleringsplan_vurdering": {{
    "tillater_deling": true,
    "begrunnelse": "Detaljert vurdering av om planen tillater deling",
    "relevante_bestemmelser": ["Bestemmelse 1", "Bestemmelse 2"],
    "arealformaal_paa_tomten": ["Boligbebyggelse", "Vei", "Friområde"]
  }},
  "dispensasjon_vurdering": {{
    "trenger_dispensasjon": false,
    "dispensasjon_fra": ["Hva man evt trenger dispensasjon fra"],
    "tidligere_dispensasjoner_i_planen": 0,
    "dispensasjoner_for_tomtestorrelse": false,
    "sannsynlighet_innvilget": "Høy/Middels/Lav",
    "begrunnelse": "Hvorfor dispensasjon evt kan/ikke kan innvilges"
  }},
  "krav_og_vilkaar": [
    {{
      "krav": "Kravbeskrivelse",
      "oppfylt": true,
      "kommentar": "Detaljer"
    }}
  ],
  "neste_steg": [
    "Steg 1: Bestill situasjonskart med inntegning av ny tomtegrense",
    "Steg 2: ...",
    "Steg 3: ..."
  ],
  "estimerte_kostnader": {{
    "kommunale_gebyrer_deling": "10 000 – 30 000 kr",
    "oppmaling": "15 000 – 40 000 kr",
    "evt_dispensasjon": "5 000 – 15 000 kr",
    "total_estimat": "30 000 – 85 000 kr"
  }},
  "dokumenter_vi_leverer": [
    "Reguleringsplan (PDF)",
    "Dispensasjonsvedtak (om funnet)",
    "Sist godkjente tegninger (innhentes fra kommunen)",
    "Planbestemmelser",
    "Arealregnestykke"
  ],
  "risiko": "LAV/MIDDELS/HØY",
  "anbefalinger": ["Anbefaling 1", "Anbefaling 2"]
}}

Viktig:
- Estimer arealer avsatt til vei, natur etc basert på typisk norsk reguleringsplan
- Bruk realistisk minste tomtestørrelse for kommunen (typisk 600-1000 m² i småhusområder)
- Vurder PBL §26-1 (krav om opparbeidelse av vei) og §28-7 (deling)
- Sjekk om dispensasjoner er gitt i denne planen – det styrker sjansen for ny dispensasjon"""

        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=(
                "Du er en norsk eiendomsekspert spesialisert på tomtedeling og fradeling. "
                "Du har dyp kunnskap om PBL, kommunale reguleringsplaner og delingsprosessen. "
                "Gi presise arealberegninger og realistiske vurderinger. "
                "Dette er beslutningsstøtte – ikke juridisk rådgivning."
            ),
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        analyse = json.loads(text)

        # ── Trigger automatisk innsynsbegjæring ─────────────────
        innsyn_sendt = False
        try:
            from app.services.email import send_innsynsbegjæring_tegninger, hent_kommune_epost
            from app.core.config import settings

            kommune_epost = hent_kommune_epost(knr, kommunenavn)
            if kommune_epost:
                bruker_navn = "nops.no"
                if current_user:
                    bruker_navn = getattr(current_user, "full_name", None) or bruker_navn

                innsyn_sendt = await send_innsynsbegjæring_tegninger(
                    kommune_epost=kommune_epost,
                    kommunenavn=kommunenavn,
                    knr=knr, gnr=gnr, bnr=bnr,
                    adresse=adresse,
                    bruker_navn=bruker_navn,
                    svar_epost="hey@nops.no",
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=settings.SMTP_PORT,
                    smtp_user=settings.SMTP_USER,
                    smtp_password=settings.SMTP_PASSWORD,
                )
        except Exception:
            pass

        return {
            "eiendom": {
                "knr": knr, "gnr": gnr, "bnr": bnr,
                "adresse": adresse, "kommunenavn": kommunenavn,
                "tomteareal_m2": tomteareal,
            },
            "ønsket_antall_tomter": ønsket_antall_tomter,
            **analyse,
            "innsynsbegjæring_sendt": innsyn_sendt,
            "disclaimer": (
                "Denne analysen er AI-generert beslutningsstøtte basert på offentlige data. "
                "Arealberegningene er estimater. Endelig vurdering må gjøres av kommunen ved søknad. "
                "Konsulter kvalifisert fagperson for bindende rådgivning."
            ),
        }

    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI-svar feilet: {exc}")
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Modul ikke tilgjengelig: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tomtedelingsanalyse feilet: {exc}")
