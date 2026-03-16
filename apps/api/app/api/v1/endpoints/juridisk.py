"""
ByggSjekk – Juridisk AI-assistent for byggesak.

Inspirert av Rettsdata.no / Legora / Harvey.
Spesialisert på plan- og bygningsloven med tilgang til:
- PBL (Plan- og bygningsloven)
- TEK17 (Byggteknisk forskrift)
- SAK10 (Byggesaksforskriften)
- EMGL (Eiendomsmeglingsloven)
- Byggforsk-veiledere
- Kommunal praksis

POST /juridisk/spor – Still et juridisk spørsmål om byggesak
POST /juridisk/vurder-tiltak – Juridisk vurdering av et planlagt tiltak
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

# Legg til services-stien (fungerer bade lokalt og i Docker)
for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _hent_regelverk_kontekst() -> str:
    """Henter full regelverkkontekst fra regelverk-modulen."""
    try:
        from services.regulations.regelverk import bygg_regelverk_kontekst
        return bygg_regelverk_kontekst()
    except ImportError:
        return ""


@router.post(
    "/spor",
    summary="Juridisk AI-assistent – spørsmål om byggesak og eiendom",
    response_model=dict,
)
async def juridisk_sporsmal(
    sporsmal: Annotated[str, Query(description="Ditt juridiske spørsmål om byggesak, eiendom eller plan- og bygningsloven")],
    knr: Annotated[str | None, Query()] = None,
    gnr: Annotated[int | None, Query()] = None,
    bnr: Annotated[int | None, Query()] = None,
    current_user: User = Depends(require_ai_access),
) -> dict:
    """
    Juridisk AI-assistent spesialisert på norsk byggesaksrett.

    Refererer til PBL, TEK17, SAK10, EMGL og Byggforsk-veiledere.
    Gir svar med eksakte paragrafhenvisninger.

    VIKTIG: Beslutningsstøtte – ikke juridisk rådgivning.
    """
    regelverk = _hent_regelverk_kontekst()

    eiendom_kontekst = ""
    if knr and gnr and bnr:
        eiendom_kontekst = f"\nEiendom: Gnr. {gnr}, Bnr. {bnr}, Kommune {knr}"
        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            adapter = get_kartverket_adapter()
            kr = await adapter.full_oppslag(knr, gnr, bnr, 0, 0)
            if not isinstance(kr, Exception) and kr.eiendom:
                eiendom_kontekst += f"\nAdresse: {kr.eiendom.adresse}"
                if kr.kommune:
                    eiendom_kontekst += f"\nKommune: {kr.kommune.kommunenavn}"
        except Exception:
            pass

    system_prompt = """Du er en norsk juridisk AI-assistent spesialisert på plan- og bygningsloven (PBL),
byggesaksforskriften (SAK10), byggteknisk forskrift (TEK17) og eiendomsmegling (EMGL).

Du har tilgang til følgende regelverk og veiledere:

""" + regelverk + """

REGLER:
1. Svar ALLTID på norsk
2. Referer til EKSAKTE paragrafer (f.eks. "PBL §20-1 bokstav a")
3. Forklar paragrafen i kontekst
4. Gi praktiske anbefalinger
5. Avslutt ALLTID med disclaimer om at dette er beslutningsstøtte
6. Hvis du er usikker, si det tydelig
7. Henvis til relevante instanser (kommune, fylkesmann, domstol) ved behov"""

    user_prompt = f"""Spørsmål: {sporsmal}
{eiendom_kontekst}

Svar BARE med gyldig JSON:
{{
  "svar": "Komplett norsk svar med paragrafhenvisninger (markdown-formatert)",
  "paragraf_referanser": [
    {{
      "lov": "PBL/TEK17/SAK10/EMGL",
      "paragraf": "§20-1",
      "tittel": "Tiltak som krever søknad og tillatelse",
      "relevans": "Kort forklaring av hvorfor denne er relevant"
    }}
  ],
  "anbefalinger": [
    "Konkret anbefaling 1",
    "Konkret anbefaling 2"
  ],
  "relevante_instanser": ["Kommune", "Statsforvalter"],
  "risikovurdering": "LAV/MIDDELS/HØY",
  "videre_lesning": [
    {{
      "tittel": "Kilde eller ressurs",
      "url": "https://lovdata.no/..."
    }}
  ]
}}"""

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
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
            "sporsmal": sporsmal,
            **result,
            "disclaimer": (
                "Denne juridiske vurderingen er AI-generert beslutningsstøtte og erstatter ikke "
                "juridisk rådgivning fra advokat eller kvalifisert fagperson. "
                "Verifiser alltid mot gjeldende lovtekst på lovdata.no."
            ),
        }
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Kunne ikke tolke AI-svar: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Juridisk analyse feilet: {exc}")


@router.post(
    "/vurder-tiltak",
    summary="Juridisk vurdering av et planlagt byggetiltak",
    response_model=dict,
)
async def vurder_tiltak(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    tiltaksbeskrivelse: Annotated[str, Query(description="Beskriv tiltaket du planlegger")],
    tiltakstype: Annotated[str, Query()] = "tilbygg",
    current_user: User = Depends(require_ai_access),
) -> dict:
    """
    Komplett juridisk vurdering av et planlagt tiltak:
    - Søknadsplikt (PBL §20-1 vs §20-5)
    - Dispensasjonsbehov
    - Nabovarslingskrav
    - TEK17-krav
    - Ansvarsretter (SAK10)
    - Tidsfrister
    """
    regelverk = _hent_regelverk_kontekst()

    # Hent eiendoms- og plandata
    eiendom_info = f"Gnr. {gnr}, Bnr. {bnr}, Kommune {knr}"
    plan_info = "Ingen plandata tilgjengelig."

    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        from services.municipality_connectors.planslurpen import get_planslurpen_adapter
        import asyncio

        kr_task = get_kartverket_adapter().full_oppslag(knr, gnr, bnr, 0, 0)
        ps_task = get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, 0, 0)
        kr, ps = await asyncio.gather(kr_task, ps_task, return_exceptions=True)

        if not isinstance(kr, Exception):
            if kr.eiendom:
                eiendom_info = f"{kr.eiendom.adresse}, {kr.kommune.kommunenavn if kr.kommune else knr}"
            if kr.bygninger:
                eiendom_info += f"\nEksisterende bygning: {kr.bygninger[0].bygningstype}, BRA={kr.bygninger[0].bruksareal} m²"

        if not isinstance(ps, Exception) and ps.antall_planer > 0:
            plan_info = "\n".join(
                f"- {p.plan_navn}: Maks høyde={p.maks_hoyde or '?'}, Maks utnyttelse={p.maks_utnyttelse or '?'}, Bruk={p.tillatt_bruk or '?'}"
                for p in ps.planer[:3]
            )
    except Exception:
        pass

    user_prompt = f"""Gjør en komplett juridisk vurdering av dette byggetiltaket:

## Eiendom
{eiendom_info}

## Planlagt tiltak
- Tiltakstype: {tiltakstype}
- Beskrivelse: {tiltaksbeskrivelse}

## Reguleringsplan
{plan_info}

{regelverk}

Svar BARE med gyldig JSON:
{{
  "soknadsplikt": {{
    "vurdering": "Søknadspliktig/Søknadsfritt/Usikkert",
    "hjemmel": "PBL §20-1 bokstav X / §20-5 / SAK10 §4-1",
    "begrunnelse": "Detaljert begrunnelse med paragrafhenvisninger"
  }},
  "dispensasjon": {{
    "behov": true,
    "fra_hva": "Hva man evt. trenger dispensasjon fra",
    "vurdering": "Sannsynlighet for å få innvilget",
    "hjemmel": "PBL §19-2"
  }},
  "nabovarsel": {{
    "krav": true,
    "begrunnelse": "Hvorfor nabovarsel kreves/ikke kreves",
    "frist_dager": 14,
    "hjemmel": "SAK10 §6-2"
  }},
  "tek17_krav": [
    {{
      "krav": "TEK17-krav som gjelder",
      "paragraf": "TEK17 §12-2",
      "oppfylt": "Ja/Nei/Ukjent",
      "kommentar": "Detaljer"
    }}
  ],
  "ansvarsretter": [
    {{
      "funksjon": "SØK/PRO/UTF",
      "beskrivelse": "Ansvarlig søker/prosjekterende/utførende",
      "krav": "Når denne ansvarsretten kreves"
    }}
  ],
  "tidsfrister": [
    {{
      "frist": "3 uker",
      "beskrivelse": "Kommunens behandlingsfrist for søknaden",
      "hjemmel": "PBL §21-7"
    }}
  ],
  "kostnader_juridisk": [
    {{
      "post": "Kommunale gebyrer",
      "estimat": "15 000 - 40 000 kr",
      "notat": ""
    }}
  ],
  "samlet_vurdering": "Komplett sammendrag av den juridiske situasjonen (3-5 setninger)",
  "anbefalinger": ["Anbefaling 1", "Anbefaling 2", "Anbefaling 3"],
  "risiko": "LAV/MIDDELS/HØY"
}}"""

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3500,
            system=(
                "Du er en norsk juridisk ekspert på plan- og bygningsloven. "
                "Gi presise vurderinger med eksakte paragrafhenvisninger. "
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
        result = json.loads(text)

        return {
            "eiendom": {"knr": knr, "gnr": gnr, "bnr": bnr, "info": eiendom_info},
            "tiltak": {"type": tiltakstype, "beskrivelse": tiltaksbeskrivelse},
            **result,
            "disclaimer": (
                "Denne juridiske vurderingen er AI-generert beslutningsstøtte. "
                "Den erstatter ikke juridisk rådgivning fra advokat. "
                "Kontakt kommunen eller en kvalifisert fagperson for endelig avklaring."
            ),
        }
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Kunne ikke tolke AI-svar: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Juridisk vurdering feilet: {exc}")
