"""
ByggSjekk – Naboklage / Merknad pa nabovarsel med AI.

POST /naboklage/generer – Genererer merknad/klage pa nabovarsel med AI.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user, require_ai_access
from app.models.user import User

router = APIRouter()

_here = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.abspath(os.path.join(_here, "../../.."))
_project_root = os.path.abspath(os.path.join(_api_root, "../.."))
for _p in [_api_root, _project_root, os.path.join(_project_root, "services")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


@router.post(
    "/generer",
    summary="Generer merknad/klage pa nabovarsel med AI",
    response_model=dict,
)
async def generer_naboklage(
    knr: Annotated[str, Query(description="Kommunenummer (din eiendom)")],
    gnr: Annotated[int, Query(description="Gardsnummer (din eiendom)")],
    bnr: Annotated[int, Query(description="Bruksnummer (din eiendom)")],
    nabo_knr: Annotated[str, Query(description="Kommunenummer (naboens eiendom, den som bygger)")],
    nabo_gnr: Annotated[int, Query(description="Gardsnummer (naboens eiendom)")],
    nabo_bnr: Annotated[int, Query(description="Bruksnummer (naboens eiendom)")],
    tiltaksbeskrivelse: Annotated[str, Query(description="Hva naboen planlegger a bygge")],
    klagegrunn: Annotated[str, Query(description="Hovedgrunn for klagen: utsikt, skygge, privatlivets fred, avstand, trafikk, stoy, annet")],
    tilleggsinformasjon: Annotated[str | None, Query(description="Valgfri utdypning")] = None,
    current_user: User = Depends(require_ai_access),
) -> dict:
    """
    Genererer en profesjonell og juridisk holdbar merknad pa nabovarsel.

    Bruker AI til a analysere situasjonen og produsere en komplett
    merknadstekst med paragrafhenvisninger.

    VIKTIG: Beslutningsstotte – ikke juridisk radgivning.
    """
    # Hent regelverk om tilgjengelig
    regelverk = ""
    try:
        from services.regulations.regelverk import bygg_regelverk_kontekst
        regelverk = bygg_regelverk_kontekst()
    except ImportError:
        pass

    system_prompt = """Du er en norsk byggesaksekspert som hjelper naboer med a skrive saklige og juridisk holdbare merknader pa nabovarsel etter SAK10 §6-3. Merknaden skal vaere balansert, profesjonell og referere til konkrete lovhjemler. Dette er beslutningsstotte.

""" + regelverk

    tillegg_tekst = f"\nTilleggsinformasjon fra klageren: {tilleggsinformasjon}" if tilleggsinformasjon else ""

    user_prompt = f"""Generer en komplett merknad pa nabovarsel basert pa folgende:

## Klagers eiendom
Kommunenr: {knr}, Gnr: {gnr}, Bnr: {bnr}

## Naboens eiendom (den som bygger)
Kommunenr: {nabo_knr}, Gnr: {nabo_gnr}, Bnr: {nabo_bnr}

## Hva naboen planlegger
{tiltaksbeskrivelse}

## Klagegrunn
{klagegrunn}
{tillegg_tekst}

Svar BARE med gyldig JSON:
{{
  "merknad_tekst": "Komplett merknad-tekst klar til a sende. Formell og profesjonell. Med referanser til lovverk.",
  "juridisk_grunnlag": "Vurdering av det juridiske grunnlaget for merknaden",
  "styrke": "Sterk/Middels/Svak",
  "styrke_begrunnelse": "Hvorfor merknaden vurderes som sterk/middels/svak",
  "paragraf_referanser": ["PBL §29-4", "SAK10 §6-3"],
  "tips_for_naboen": ["Tips 1", "Tips 2"],
  "frist_info": "Merknader ma sendes innen 14 dager etter mottak av nabovarsel (SAK10 §6-3)"
}}"""

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        result = json.loads(text)

        return {
            "klager_eiendom": {"knr": knr, "gnr": gnr, "bnr": bnr},
            "nabo_eiendom": {"knr": nabo_knr, "gnr": nabo_gnr, "bnr": nabo_bnr},
            "klagegrunn": klagegrunn,
            **result,
            "disclaimer": (
                "Denne merknaden er AI-generert beslutningsstotte og erstatter ikke "
                "juridisk radgivning fra advokat eller kvalifisert fagperson. "
                "Verifiser alltid mot gjeldende lovtekst pa lovdata.no."
            ),
        }
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Kunne ikke tolke AI-svar: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Naboklage-generering feilet: {exc}")
