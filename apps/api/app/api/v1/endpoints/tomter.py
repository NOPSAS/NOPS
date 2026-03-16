"""
ByggSjekk – Tomteutvikling.

POST /tomter/mulighetsstudie   – AI-basert mulighetsstudie for en tomt
POST /tomter/kostnadskalkulator – Deterministisk kostnadsberegning
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user, require_ai_access
from app.models.user import User

router = APIRouter()

# Legg til services-stien (fungerer bade lokalt og i Docker)
for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences from AI response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()
    return text


def _default_kommunale_gebyrer(kommunenummer: str, hustype: str, bra_m2: int) -> int:
    """Prøv gebyrberegning-service, ellers returner default."""
    try:
        from regulations.gebyrberegning import beregn_gebyrer
        result = beregn_gebyrer(kommunenummer, hustype, bra_m2)
        if isinstance(result, dict) and "total" in result:
            return int(result["total"])
    except Exception:
        pass
    return 35_000


# ---------------------------------------------------------------------------
# Endpoint 1: Mulighetsstudie (AI)
# ---------------------------------------------------------------------------

@router.post("/mulighetsstudie", summary="AI-basert mulighetsstudie for tomt")
async def mulighetsstudie(
    knr: str = Query(..., description="Kommunenummer, f.eks. 0301"),
    gnr: int = Query(..., description="Gardsnummer"),
    bnr: int = Query(..., description="Bruksnummer"),
    tomtepris_kr: int = Query(0, description="Tomtepris i kr (0 = ikke oppgitt)"),
    hustype: str = Query(
        "enebolig",
        description="Hustype",
        pattern="^(enebolig|tomannsbolig|hytte|rekkehus|leiligheter)$",
    ),
    antall_enheter: int = Query(1, description="Antall enheter"),
    finn_url: str = Query("", description="Lenke til Finn.no-annonse"),
    _ai: None = Depends(require_ai_access),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Henter eiendomsdata og reguleringsplan, og genererer en komplett
    mulighetsstudie med AI (husmodeller, kostnader, presentasjonstekst).
    """

    # ------------------------------------------------------------------
    # 1. Hent data parallelt fra kartverket og planslurpen
    # ------------------------------------------------------------------
    try:
        from municipality_connectors.kartverket import KartverketClient
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Kartverket-modul er ikke tilgjengelig",
        )

    try:
        from municipality_connectors.planslurpen import PlanslurpenClient
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Planslurpen-modul er ikke tilgjengelig",
        )

    kart_client = KartverketClient()
    plan_client = PlanslurpenClient()

    try:
        eiendom_data, plan_data = await asyncio.gather(
            kart_client.full_oppslag(knr, gnr, bnr, 0, 0),
            plan_client.hent_planbestemmelser(knr, gnr, bnr, 0, 0),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Feil ved henting av eiendomsdata: {exc}",
        )

    # ------------------------------------------------------------------
    # 2. Bygg AI-prompt
    # ------------------------------------------------------------------
    tomtepris_tekst = (
        f"{tomtepris_kr:,} kr" if tomtepris_kr > 0 else "Ikke oppgitt"
    )
    finn_tekst = f"\nFinn.no-annonse: {finn_url}" if finn_url else ""

    hustype_leverandorer = {
        "enebolig": "Nordbohus, Norgeshus, Alvsbyhus, BoligPartner, Mesterhus, Huscompagniet",
        "tomannsbolig": "Nordbohus, Norgeshus, BoligPartner, Mesterhus, Huscompagniet",
        "hytte": "Nordbohus hytter, Saltdalshytta, Hedda Hytter, Rindalshytter",
        "rekkehus": "Nordbohus, BoligPartner, Mesterhus, Huscompagniet",
        "leiligheter": "BoligPartner, Mesterhus, Huscompagniet",
    }
    relevante_leverandorer = hustype_leverandorer.get(hustype, hustype_leverandorer["enebolig"])

    prompt = f"""Du er en norsk eiendomsekspert og tomteutvikler. Lag en komplett mulighetsstudie for denne tomten.

Eiendom: {knr}-{gnr}/{bnr}
Tomtepris: {tomtepris_tekst}
Hustype onsket: {hustype}
Antall enheter: {antall_enheter}{finn_tekst}

EIENDOMSDATA FRA KARTVERKET:
{json.dumps(eiendom_data, ensure_ascii=False, indent=2, default=str)}

REGULERINGSPLAN:
{json.dumps(plan_data, ensure_ascii=False, indent=2, default=str)}

INSTRUKSJONER:
- Bruk realistiske norske ferdighusmodeller og priser fra: {relevante_leverandorer}
- Kostnadestimater skal baseres pa norske 2024/2025-priser
- Dokumentavgift = 2.5% av tomtepris
- Tinglysingsgebyr = 585 kr
- Kommunale gebyrer: typisk 25 000-50 000 kr
- Grunnarbeid: typisk 300 000-800 000 kr avhengig av tomt
- VA-tilknytning: typisk 80 000-200 000 kr
- Elektro: typisk 50 000-150 000 kr
- Foreslag minimum 2-3 byggemuligheter/husmodeller som passer tomten
- Tomtepris 0 betyr at den ikke er kjent; estimer da basert pa beliggenhet
- Skriv pa norsk

Svar BARE med gyldig JSON (ingen forklaring utenfor JSON):
{{
  "tomte_analyse": {{
    "tomteareal_m2": <int>,
    "maks_bya_prosent": <float>,
    "maks_bya_m2": <int>,
    "maks_hoyde_m": <float>,
    "tomtetype": "<Flat|Skra|Bratt>",
    "solforhold": "<God|Middels|Begrenset>",
    "vurdering": "<tekst om tomtens potensial>"
  }},
  "byggemuligheter": [
    {{
      "navn": "<Alternativ 1: ...>",
      "husmodell": "<realistisk modellnavn>",
      "leverandor": "<leverandornavn>",
      "type": "{hustype}",
      "bra_m2": <int>,
      "etasjer": <int>,
      "soverom": <int>,
      "beskrivelse": "<kort beskrivelse>",
      "plassering_tips": "<hvordan huset bor plasseres>",
      "passer_tomten": <true|false>
    }}
  ],
  "kostnadsestimat": {{
    "tomtekjop": <int>,
    "dokumentavgift_2_5_prosent": <int>,
    "tinglysing": 585,
    "kommunale_gebyrer": <int>,
    "ferdighus_pris": <int>,
    "grunnarbeid_og_fundament": <int>,
    "vann_og_avlop": <int>,
    "elektro": <int>,
    "opparbeidelse_tomt": <int>,
    "tilknytningsavgifter": <int>,
    "prosjektering_og_byggesoknad": <int>,
    "uforutsett_10_prosent": <int>,
    "total_prosjektkostnad": <int>
  }},
  "ferdighusleverandorer": [
    {{
      "navn": "<leverandornavn>",
      "nettside": "<nettside>",
      "prisklasse": "<Lav|Middels|Middels-hoy|Hoy>",
      "spesialitet": "<kort beskrivelse>"
    }}
  ],
  "presentasjonstekst": {{
    "overskrift": "<Moderne eneboligtomt i [sted]>",
    "ingress": "<2-3 setninger som selger tomten>",
    "hoveddel": "<4-6 setninger om muligheter og beliggenhet>",
    "cta": "<kort tekst som oppfordrer til handling>"
  }},
  "reguleringsplan_sammendrag": "<kort om hva reguleringsplanen tillater>",
  "anbefalinger": ["<anbefaling 1>", "<anbefaling 2>", "<anbefaling 3>"],
  "disclaimer": "Dette er et estimat basert pa AI-analyse av offentlige data. Faktiske kostnader og muligheter kan avvike. Kontakt en lokal megler eller entreprenor for endelig vurdering."
}}"""

    # ------------------------------------------------------------------
    # 3. Kall Anthropic Claude
    # ------------------------------------------------------------------
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY ikke konfigurert",
            )

        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        text = _strip_json_fences(response.content[0].text)
        studie = json.loads(text)

        return {
            "eiendom": {
                "knr": knr,
                "gnr": gnr,
                "bnr": bnr,
                "tomtepris_kr": tomtepris_kr,
                "hustype": hustype,
                "antall_enheter": antall_enheter,
                "finn_url": finn_url,
            },
            **studie,
        }

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Anthropic-modulen er ikke installert",
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI-svar kunne ikke tolkes som JSON: {exc}",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Mulighetsstudie feilet: {exc}",
        )


# ---------------------------------------------------------------------------
# Endpoint 2: Kostnadskalkulator (deterministisk)
# ---------------------------------------------------------------------------

@router.post("/kostnadskalkulator", summary="Deterministisk kostnadsberegning for tomt + hus")
async def kostnadskalkulator(
    tomtepris: int = Query(..., description="Tomtepris i kroner"),
    huspris: int = Query(..., description="Huspris (ferdighus/hytte) i kroner"),
    hustype: str = Query(
        "enebolig",
        description="Hustype",
        pattern="^(enebolig|tomannsbolig|hytte|rekkehus|leiligheter)$",
    ),
    bra_m2: int = Query(150, description="Bruksareal i m2"),
    kommunenummer: str = Query("", description="Kommunenummer for gebyrberegning"),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Ren deterministisk kostnadsberegning uten AI.
    Returnerer poster, total og pris per m2.
    """

    dokumentavgift = int(tomtepris * 0.025)
    tinglysing = 585
    kommunale_gebyrer = _default_kommunale_gebyrer(kommunenummer, hustype, bra_m2)
    grunnarbeid = int(bra_m2 * 3500)
    va_tilknytning = 150_000
    elektro = 100_000
    opparbeidelse = 250_000
    prosjektering = 120_000

    # Sum av alle poster utenom tomtekjop for uforutsett-beregning
    byggekostnader_sum = (
        dokumentavgift
        + tinglysing
        + kommunale_gebyrer
        + huspris
        + grunnarbeid
        + va_tilknytning
        + elektro
        + opparbeidelse
        + prosjektering
    )
    uforutsett = int(byggekostnader_sum * 0.10)

    total = tomtepris + byggekostnader_sum + uforutsett

    pris_per_m2 = int(total / bra_m2) if bra_m2 > 0 else 0

    poster = [
        {"navn": "Tomtekjop", "belop": tomtepris, "notat": ""},
        {"navn": "Dokumentavgift (2,5%)", "belop": dokumentavgift, "notat": "Av tomtepris"},
        {"navn": "Tinglysing", "belop": tinglysing, "notat": "Fast sats 2026"},
        {"navn": "Ferdighus/hytte", "belop": huspris, "notat": ""},
        {"navn": "Kommunale gebyrer", "belop": kommunale_gebyrer, "notat": "Estimert"},
        {"navn": "Grunnarbeid og fundament", "belop": grunnarbeid, "notat": ""},
        {"navn": "VA-tilknytning", "belop": va_tilknytning, "notat": ""},
        {"navn": "Elektro-installasjon", "belop": elektro, "notat": ""},
        {"navn": "Opparbeidelse tomt", "belop": opparbeidelse, "notat": ""},
        {"navn": "Prosjektering og byggesoknad", "belop": prosjektering, "notat": ""},
        {"navn": "Uforutsett (10%)", "belop": uforutsett, "notat": ""},
    ]

    return {
        "poster": poster,
        "total": total,
        "pris_per_m2_bolig": pris_per_m2,
        "notat": "Estimat basert pa typiske norske priser 2025/2026",
    }
