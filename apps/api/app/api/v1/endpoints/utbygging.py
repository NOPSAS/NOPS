"""
ByggSjekk – Tomteutviklingsanalyse (Archistar/Plot.ai-inspirert)

Analyserer utbyggingspotensial for en eiendom basert på:
- Kartverket matrikkeldata (areal, bygninger, byggeår)
- Reguleringsplan via Planslurpen (maks høyde, utnyttelse, tillatt bruk)
- Claude AI beregner antall mulige enheter, inntektspotensial og utviklingsscenarioer

POST /utbygging/analyser
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

# Legg til services-stien
_here = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.abspath(os.path.join(_here, "../../.."))
_project_root = os.path.abspath(os.path.join(_api_root, "../.."))
for _p in [_api_root, _project_root, os.path.join(_project_root, "services")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Request/Response-modeller
# ---------------------------------------------------------------------------

TILTAKSTYPER = {"enebolig", "leiligheter", "tomannsbolig", "næring"}


class UtbyggingRequest(BaseModel):
    knr: str = Field(..., description="Kommunenummer, f.eks. '3212' for Nesodden")
    gnr: int = Field(..., description="Gårdsnummer")
    bnr: int = Field(..., description="Bruksnummer")
    tiltakstype: str = Field(
        "leiligheter",
        description="Tiltakstype: enebolig | leiligheter | tomannsbolig | næring",
    )
    areal_per_enhet: int = Field(
        80,
        ge=20,
        le=500,
        description="Ønsket areal per boenhet i m² (default 80)",
    )


# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------


def _bygg_kartverket_kontekst(kartverket_data: dict) -> str:
    """Formater Kartverket-data til lesbar tekst for AI-prompten."""
    lines: list[str] = []

    eiendom = kartverket_data.get("eiendom") or {}
    if eiendom:
        areal = eiendom.get("areal_m2")
        adresse = eiendom.get("adresse", "Ukjent adresse")
        lines.append(f"Adresse: {adresse}")
        if areal:
            lines.append(f"Tomteareal: {areal} m²")

    bygninger = kartverket_data.get("bygninger") or []
    if bygninger:
        lines.append(f"Antall bygninger: {len(bygninger)}")
        total_bra = sum(b.get("bruksareal") or 0 for b in bygninger)
        if total_bra:
            lines.append(f"Totalt BRA eksisterende: {total_bra} m²")
        for i, b in enumerate(bygninger, 1):
            btype = b.get("bygningstype", "Ukjent type")
            aar = b.get("byggeaar")
            bra = b.get("bruksareal")
            deler = [f"Bygg {i}: {btype}"]
            if aar:
                deler.append(f"byggeår {aar}")
            if bra:
                deler.append(f"BRA {bra} m²")
            lines.append(", ".join(deler))
    else:
        lines.append("Ingen bygninger registrert på eiendommen")

    return "\n".join(lines) if lines else "Ingen eiendomsdata tilgjengelig"


def _bygg_planslurpen_kontekst(plan_data: dict) -> str:
    """Formater Planslurpen-data til lesbar tekst for AI-prompten."""
    lines: list[str] = []

    feil = plan_data.get("feilmelding")
    if feil:
        return f"Plandata ikke tilgjengelig: {feil}"

    planer = plan_data.get("planer") or []
    if not planer:
        return "Ingen reguleringsplan funnet for eiendommen"

    for plan in planer[:2]:  # Maks 2 planer for å holde prompten konsis
        navn = plan.get("plan_navn", "Ukjent plan")
        lines.append(f"Plan: {navn}")

        maks_hoyde = plan.get("maks_hoyde")
        if maks_hoyde:
            lines.append(f"Maks byggehøyde: {maks_hoyde}")

        maks_utnyttelse = plan.get("maks_utnyttelse")
        if maks_utnyttelse:
            lines.append(f"Maks utnyttelse: {maks_utnyttelse}")

        tillatt_bruk = plan.get("tillatt_bruk") or []
        if tillatt_bruk:
            lines.append(f"Tillatt bruk: {', '.join(tillatt_bruk[:5])}")

        bestemmelser = plan.get("bestemmelser") or []
        for b in bestemmelser[:5]:
            kategori = b.get("kategori", "")
            tekst = b.get("tekst", "")
            verdi = b.get("verdi")
            if kategori and tekst:
                entry = f"[{kategori}] {tekst[:200]}"
                if verdi:
                    entry += f" (verdi: {verdi})"
                lines.append(entry)

    return "\n".join(lines) if lines else "Ingen planbestemmelser tilgjengelig"


# ---------------------------------------------------------------------------
# Endepunkt
# ---------------------------------------------------------------------------


@router.post(
    "/analyser",
    summary="Analyser utbyggingspotensial for en eiendom",
    response_model=dict,
)
async def analyser_utbygging(
    req: UtbyggingRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Analyserer tomteutviklingspotensial for en norsk eiendom.

    Henter Kartverket matrikkeldata og Planslurpen reguleringsplan parallelt,
    og bruker Claude AI til å beregne utbyggingsscenarioer, inntektspotensial
    og gjennomførbarhetsvurdering.
    """
    if req.tiltakstype not in TILTAKSTYPER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ugyldig tiltakstype. Tillatte: {', '.join(sorted(TILTAKSTYPER))}",
        )

    # -----------------------------------------------------------------------
    # Hent data parallelt
    # -----------------------------------------------------------------------
    kartverket_data: dict = {}
    plan_data: dict = {}

    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        from services.municipality_connectors.planslurpen import get_planslurpen_adapter

        kartverket = get_kartverket_adapter()
        planslurpen = get_planslurpen_adapter()

        kv_resultat, ps_resultat = await asyncio.gather(
            kartverket.full_oppslag(req.knr, req.gnr, req.bnr),
            planslurpen.hent_planbestemmelser(req.knr, req.gnr, req.bnr),
            return_exceptions=True,
        )

        # Kartverket-resultat
        if isinstance(kv_resultat, Exception):
            kartverket_data = {"feilmelding": str(kv_resultat)}
        else:
            eiendom = kv_resultat.eiendom
            bygninger = kv_resultat.bygninger or []
            kartverket_data = {
                "eiendom": {
                    "adresse": getattr(eiendom, "adresse", "") if eiendom else "",
                    "areal_m2": getattr(eiendom, "areal_m2", None) if eiendom else None,
                    "kommunenummer": req.knr,
                    "gnr": req.gnr,
                    "bnr": req.bnr,
                }
                if eiendom
                else {},
                "bygninger": [
                    {
                        "bygningstype": getattr(b, "bygningstype", ""),
                        "byggeaar": getattr(b, "byggeaar", None),
                        "bruksareal": getattr(b, "bruksareal", None),
                    }
                    for b in bygninger
                ],
            }

        # Planslurpen-resultat
        if isinstance(ps_resultat, Exception):
            plan_data = {"feilmelding": str(ps_resultat)}
        else:
            planer = ps_resultat.planer or []
            plan_data = {
                "feilmelding": ps_resultat.feilmelding,
                "planer": [
                    {
                        "plan_navn": getattr(p, "plan_navn", ""),
                        "maks_hoyde": getattr(p, "maks_hoyde", None),
                        "maks_utnyttelse": getattr(p, "maks_utnyttelse", None),
                        "tillatt_bruk": getattr(p, "tillatt_bruk", []),
                        "bestemmelser": [
                            {
                                "kategori": getattr(b, "kategori", ""),
                                "tekst": getattr(b, "tekst", ""),
                                "verdi": getattr(b, "verdi", None),
                            }
                            for b in (getattr(p, "bestemmelser", []) or [])
                        ],
                    }
                    for p in planer
                ],
            }

    except ImportError:
        # Tjenestene er ikke tilgjengelige – bruk tomme data og la AI lage scenarioer
        kartverket_data = {}
        plan_data = {}

    # -----------------------------------------------------------------------
    # Bygg AI-prompt
    # -----------------------------------------------------------------------
    kartverket_tekst = _bygg_kartverket_kontekst(kartverket_data)
    planslurpen_tekst = _bygg_planslurpen_kontekst(plan_data)

    tiltakstype_beskrivelse = {
        "enebolig": "enebolig (frittliggende)",
        "leiligheter": "leilighetsbygg / flermannsbolig",
        "tomannsbolig": "tomannsbolig / kjedehus",
        "næring": "næringsbygg / kombinert bolig og næring",
    }.get(req.tiltakstype, req.tiltakstype)

    system_prompt = """Du er en norsk eiendomsutviklingsekspert med spesialkunnskap om plan- og bygningsloven,
TEK17, og kommunale reguleringsplaner. Du analyserer tomteutviklingspotensial for norske eiendommer.

Bruk realistiske norske markedspriser:
- Boligsalg: 50 000–100 000 kr/m² avhengig av beliggenhet (bruk 65 000 kr/m² som standard)
- Byggekostnader: 30 000–50 000 kr/m² BRA (bruk 35 000 kr/m² som standard for boliger)
- Næring: 40 000–80 000 kr/m² for salg, 40 000 kr/m² byggekostnad

Svar ALLTID med gyldig JSON uten markdown-formatering."""

    user_prompt = f"""Analyser utbyggingspotensial for denne norske eiendommen:

EIENDOM: {req.knr}/{req.gnr}/{req.bnr}
ØNSKET TILTAKSTYPE: {tiltakstype_beskrivelse}
ØNSKET AREAL PER ENHET: {req.areal_per_enhet} m²

KARTVERKET-DATA:
{kartverket_tekst}

REGULERINGSPLAN (Planslurpen):
{planslurpen_tekst}

Beregn utbyggingspotensialet og returner JSON i dette eksakte formatet:
{{
  "nåværende_utnyttelse": {{
    "bya_prosent": <float, beregnet BYA prosent basert på eksisterende bygg vs tomteareal>,
    "bra_m2": <int, totalt eksisterende BRA>,
    "antall_bygninger": <int>
  }},
  "maks_tillatt": {{
    "bya_prosent": <float, maks BYA fra reguleringsplan eller TEK17-standard 30% hvis ukjent>,
    "bra_m2": <int, beregnet maks tillatt BRA basert på tomteareal og utnyttelsesgrad>,
    "maks_hoyde_m": <float, maks byggehøyde fra reguleringsplan eller 9.0 m som standard>
  }},
  "uutnyttet_potensial": {{
    "ekstra_bra_m2": <int, differansen mellom maks tillatt og eksisterende BRA>,
    "potensial_prosent": <float, prosent av maks utnyttelse som er ubrukt>
  }},
  "scenarioer": [
    {{
      "navn": "Tilbygg eksisterende",
      "beskrivelse": "<konkret beskrivelse av hva som kan gjøres>",
      "antall_enheter": <int>,
      "estimert_bra_m2": <int>,
      "estimert_salgsverdi_kr": <int>,
      "estimert_byggekostnad_kr": <int>,
      "estimert_fortjeneste_kr": <int>,
      "gjennomforbarhet": "<Høy|Middels|Lav>",
      "reguleringsrisiko": "<Lav|Middels|Høy>"
    }},
    {{
      "navn": "Nybygg {tiltakstype_beskrivelse}",
      "beskrivelse": "<konkret beskrivelse>",
      "antall_enheter": <int>,
      "estimert_bra_m2": <int>,
      "estimert_salgsverdi_kr": <int>,
      "estimert_byggekostnad_kr": <int>,
      "estimert_fortjeneste_kr": <int>,
      "gjennomforbarhet": "<Høy|Middels|Lav>",
      "reguleringsrisiko": "<Lav|Middels|Høy>"
    }},
    {{
      "navn": "Maks utnyttelse",
      "beskrivelse": "<fullstendig utnyttelse av tomten innenfor reguleringsplan>",
      "antall_enheter": <int>,
      "estimert_bra_m2": <int>,
      "estimert_salgsverdi_kr": <int>,
      "estimert_byggekostnad_kr": <int>,
      "estimert_fortjeneste_kr": <int>,
      "gjennomforbarhet": "<Høy|Middels|Lav>",
      "reguleringsrisiko": "<Lav|Middels|Høy>"
    }}
  ],
  "reguleringsplan_analyse": "<2-4 setninger om hva reguleringsplanen tillater og begrenser for denne eiendommen>",
  "anbefalinger": [
    "<konkret anbefaling 1>",
    "<konkret anbefaling 2>",
    "<konkret anbefaling 3>"
  ],
  "disclaimer": "Analysen er basert på tilgjengelige offentlige data og er kun veiledende. Kontakt kommunen og en fagkyndig rådgiver før du foretar investeringsbeslutninger. Priser og reguleringsbestemmelser kan endres."
}}"""

    # -----------------------------------------------------------------------
    # Kall Claude AI
    # -----------------------------------------------------------------------
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI-tjenesten er ikke konfigurert (mangler ANTHROPIC_API_KEY)",
            )

        client = anthropic.AsyncAnthropic(api_key=api_key)

        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        tekst = response.content[0].text.strip()

        # Strip markdown code fences hvis til stede
        if tekst.startswith("```"):
            tekst = tekst.split("```", 2)[1]
            if tekst.startswith("json"):
                tekst = tekst[4:]
            tekst = tekst.rsplit("```", 1)[0].strip()

        analyse = json.loads(tekst)

        return {
            "eiendom": {
                "knr": req.knr,
                "gnr": req.gnr,
                "bnr": req.bnr,
                "tiltakstype": req.tiltakstype,
                "areal_per_enhet": req.areal_per_enhet,
            },
            "analyse": analyse,
            "datakilder": {
                "kartverket": bool(kartverket_data.get("eiendom")),
                "planslurpen": bool(plan_data.get("planer")),
            },
        }

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI-modulen er ikke tilgjengelig",
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI-svar kunne ikke tolkes som JSON: {exc}",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Utbyggingsanalyse feilet: {exc}",
        )
