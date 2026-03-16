"""
ByggSjekk – Investeringsanalyse.

POST /investering/analyser
Beregner yield, ROI, cashflow og break-even for en norsk eiendom ved hjelp av
Anthropic Claude. Henter best-effort kommunenavn fra Kartverket.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


def _hent_kommunenavn(knr: str) -> str:
    """Prøver å hente kommunenavn fra Kartverket. Returnerer knr ved feil."""
    try:
        import httpx
        url = f"https://api.kartverket.no/kommuneinfo/v1/kommuner/{knr}"
        with httpx.Client(timeout=5) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("kommunenavnNorsk") or data.get("kommunenavn") or knr
    except Exception:
        pass
    return knr


@router.post("/analyser", summary="Investeringsanalyse for norsk eiendom")
async def analyser_investering(
    knr: str = Query(..., description="Kommunenummer, f.eks. 0301"),
    gnr: str = Query(..., description="Gårdsnummer"),
    bnr: str = Query(..., description="Bruksnummer"),
    kjøpspris: int = Query(..., description="Kjøpspris i kroner"),
    egenkapital_prosent: float = Query(25.0, description="Egenkapital i prosent (10–40)"),
    rentenivaa: float = Query(5.5, description="Rentenivå i prosent"),
    renovering_kr: int = Query(0, description="Estimert renovering i kroner"),
    leie_per_mnd: Optional[int] = Query(None, description="Kjent/estimert månedlig leieinntekt"),
    investeringshorisont_aar: int = Query(10, description="Investeringshorisont i år (5–20)"),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Genererer komplett investeringsanalyse for en norsk eiendom.

    Returnerer finansiering, leieinntekter, prisvekst, cashflow, risikovurdering
    og anbefalinger basert på eiendomsdata og markedskunnskap.
    """
    kommunenavn = _hent_kommunenavn(knr)
    total_investering = kjøpspris + renovering_kr
    egenkapital = int(total_investering * egenkapital_prosent / 100)
    laan = total_investering - egenkapital

    leie_kontekst = (
        f"Kjent månedlig leieinntekt: {leie_per_mnd} kr."
        if leie_per_mnd
        else "Månedlig leieinntekt er ukjent – estimer basert på lokalt marked."
    )

    prompt = f"""Du er en norsk eiendomsinvesterings-ekspert. Lag en komplett investeringsanalyse.

Eiendom: {knr}-{gnr}/{bnr}, Kommune: {kommunenavn}
Kjøpspris: {kjøpspris:,} kr
Renovering: {renovering_kr:,} kr
Total investering: {total_investering:,} kr
Egenkapital: {egenkapital_prosent}% = {egenkapital:,} kr
Lån: {laan:,} kr
Rentenivå: {rentenivaa}%
{leie_kontekst}
Investeringshorisont: {investeringshorisont_aar} år

Beregn og estimer realistiske norske markedsverdier. Bruk annuitetslån med 25 års nedbetalingstid.
Svar BARE med gyldig JSON:
{{
  "finansiering": {{
    "kjøpspris": {kjøpspris},
    "egenkapital": {egenkapital},
    "lån": {laan},
    "månedlig_renter": <int: månedlig rentekostnad kr>,
    "månedlig_avdrag": <int: månedlig avdrag kr>,
    "total_månedskostnad": <int: totale månedlige kostnader inkl. fellesgjeld, forsikring, vedlikehold kr>
  }},
  "leieinntekter": {{
    "estimert_leie_per_mnd": <int: realistisk månedlig leie for dette markedet kr>,
    "årlig_leieinntekt": <int kr>,
    "yield_prosent": <float: brutto yield>,
    "netto_yield_prosent": <float: netto yield etter kostnader>
  }},
  "prisvekst": {{
    "estimert_vekst_per_aar": <float: forventet årlig prisvekst %>,
    "verdi_om_5_aar": <int kr>,
    "verdi_om_10_aar": <int kr>,
    "total_avkastning_10_aar_kr": <int: total avkastning inkl. leieinntekter og prisvekst minus kostnader>,
    "total_avkastning_10_aar_prosent": <float: total avkastning på investert egenkapital %>
  }},
  "cashflow": {{
    "månedlig_positiv_cashflow": <int: leieinntekt minus alle kostnader, kan være negativ>,
    "break_even_mnd": <int: måneder til investert kapital er tjent inn>,
    "anbefaling": <"Kjøp" | "Avvent" | "Selg">
  }},
  "risiko_vurdering": "<norsk tekst om risikofaktorer, rente-risiko, markedsrisiko, spesifikt for {kommunenavn}>",
  "nøkkeltall_markedet": "<norsk tekst om lokal markedsutvikling i {kommunenavn}, befolkningsvekst, pristrend>",
  "anbefalinger": [
    "<konkret anbefaling 1>",
    "<konkret anbefaling 2>",
    "<konkret anbefaling 3>"
  ],
  "disclaimer": "Analysen er basert på estimater og historiske data. Den er ikke finansiell rådgivning. Konsulter en finansiell rådgiver før investeringsbeslutninger."
}}"""

    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY ikke konfigurert")

        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()

        analyse = json.loads(text)

        return {
            "eiendom": {
                "knr": knr,
                "gnr": gnr,
                "bnr": bnr,
                "kommunenavn": kommunenavn,
                "kjøpspris": kjøpspris,
                "renovering_kr": renovering_kr,
                "total_investering": total_investering,
            },
            **analyse,
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="Anthropic-modulen er ikke installert")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI-svar kunne ikke tolkes: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Investeringsanalyse feilet: {exc}")
