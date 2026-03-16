"""
ByggSjekk – Adresseoppslag og eiendomssøk.

Bruker Geonorge og Kartverket sine åpne API-er til å:
- Søke opp eiendommer etter adresse (fritekstsøk)
- Slå opp koordinater fra adresse
- Finne gnr/bnr fra adresse
- Søke etter stedsnavn

Endepunkter:
  GET /search/address  – adresseoppslag og gnr/bnr fra Geonorge
  GET /search/suggest  – adresseforslag for autocomplete
"""

from __future__ import annotations

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_optional_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Geonorge adresse-API (åpent, ingen token nødvendig)
ADRESSE_API = "https://ws.geonorge.no/adresser/v1"
TIMEOUT = httpx.Timeout(10.0)


@router.get(
    "/suggest",
    summary="Adresseforslag for autocomplete",
    response_model=list[dict],
)
async def address_suggest(
    q: Annotated[str, Query(description="Adressetekst, min 3 tegn")],
    size: Annotated[int, Query(ge=1, le=20)] = 8,
    current_user = Depends(get_optional_user),
) -> list[dict]:
    """
    Returnerer adresseforslag for autocomplete-søk.
    Bruker Geonorge adresse-API (åpent API, ingen nøkkel nødvendig).
    """
    if len(q.strip()) < 3:
        return []

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"{ADRESSE_API}/sok",
                params={
                    "sok": q,
                    "treffPerSide": size,
                    "side": 0,
                    "fuzzy": "true",
                },
            )
            r.raise_for_status()
            data = r.json()

        adresser = data.get("adresser", [])
        return [
            {
                "adressetekst": a.get("adressetekst", ""),
                "adressenavn": a.get("adressenavn", ""),
                "husnummer": a.get("husnummer"),
                "bokstav": a.get("bokstav"),
                "postnummer": a.get("postnummer", ""),
                "poststed": a.get("poststed", ""),
                "kommunenummer": a.get("kommunenummer", ""),
                "kommunenavn": a.get("kommunenavn", ""),
                "gnr": a.get("gardsnummer"),
                "bnr": a.get("bruksnummer"),
                "fnr": a.get("festenummer"),
                "snr": a.get("seksjonsnummer"),
                "lat": (a.get("representasjonspunkt") or {}).get("lat"),
                "lon": (a.get("representasjonspunkt") or {}).get("lon"),
            }
            for a in adresser
        ]

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Geonorge adresse-API feil: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Adresseoppslag feilet: {e}",
        )


@router.get(
    "/address",
    summary="Finn gnr/bnr og koordinater fra adresse",
    response_model=dict,
)
async def address_lookup(
    adresse: Annotated[str, Query(description="Gateadresse, f.eks. 'Storgata 1, Oslo'")],
    current_user = Depends(get_optional_user),
) -> dict:
    """
    Slår opp en adresse og returnerer gnr/bnr, kommunenummer og koordinater.
    Bruker Geonorge adresse-API.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"{ADRESSE_API}/sok",
                params={
                    "sok": adresse,
                    "treffPerSide": 1,
                    "side": 0,
                },
            )
            r.raise_for_status()
            data = r.json()

        adresser = data.get("adresser", [])
        if not adresser:
            return {
                "funnet": False,
                "adresse": adresse,
                "feilmelding": "Adressen ble ikke funnet",
            }

        a = adresser[0]
        punkt = a.get("representasjonspunkt") or {}
        return {
            "funnet": True,
            "adressetekst": a.get("adressetekst", ""),
            "postnummer": a.get("postnummer", ""),
            "poststed": a.get("poststed", ""),
            "kommunenummer": a.get("kommunenummer", ""),
            "kommunenavn": a.get("kommunenavn", ""),
            "gnr": a.get("gardsnummer"),
            "bnr": a.get("bruksnummer"),
            "fnr": a.get("festenummer"),
            "snr": a.get("seksjonsnummer"),
            "lat": punkt.get("lat"),
            "lon": punkt.get("lon"),
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Geonorge adresse-API feil: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Adresseoppslag feilet: {e}",
        )
