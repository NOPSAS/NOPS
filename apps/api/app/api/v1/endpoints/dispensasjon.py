"""
ByggSjekk – Dispensasjonssøknad og Ferdigattest-sjekk.

POST /dispensasjon/generer         – Genererer komplett dispensasjonssøknad med AI
POST /dispensasjon/ferdigattest-sjekk – Sjekker ferdigattest-status for eiendom
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_optional_user, require_ai_access
from app.models.user import User

router = APIRouter()

_here = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.abspath(os.path.join(_here, "../../.."))
_project_root = os.path.abspath(os.path.join(_api_root, "../.."))
for _p in [_api_root, _project_root, os.path.join(_project_root, "services")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Dispensasjonssøknad
# ---------------------------------------------------------------------------


@router.post(
    "/generer",
    summary="Generer en komplett dispensasjonssøknad med AI",
    response_model=dict,
)
async def generer_dispensasjon(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    tiltaksbeskrivelse: Annotated[str, Query(description="Hva man vil bygge")],
    dispensasjon_fra: Annotated[str, Query(description="Hva man søker dispensasjon fra, f.eks. avstand til nabogrense, BYA-grense, reguleringsformål")],
    begrunnelse: Annotated[str, Query(description="Hvorfor dispensasjon bør innvilges")],
    current_user: User = Depends(require_ai_access),
) -> dict:
    """
    Genererer en komplett dispensasjonssøknad etter PBL §19-2 med AI.
    Henter eiendomsdata og plandata parallelt for kontekst.

    VIKTIG: Beslutningsstøtte – ikke juridisk rådgivning.
    """
    # Hent eiendoms- og plandata parallelt
    eiendom_info = f"Gnr. {gnr}, Bnr. {bnr}, Kommune {knr}"
    plan_info = "Ingen plandata tilgjengelig."

    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        from services.municipality_connectors.planslurpen import get_planslurpen_adapter

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

    # Hent regelverkkontekst
    regelverk = ""
    try:
        from services.regulations.regelverk import bygg_regelverk_kontekst
        regelverk = bygg_regelverk_kontekst()
    except ImportError:
        pass

    system_prompt = """Du er en norsk byggesaksekspert som skriver dispensasjonssøknader etter PBL §19-2.
Du skal vurdere om fordelene er klart større enn ulempene.
Skriv profesjonelt og juridisk korrekt.
Dette er beslutningsstøtte.

""" + regelverk

    user_prompt = f"""Generer en komplett dispensasjonssøknad basert på følgende:

## Eiendom
{eiendom_info}

## Reguleringsplan
{plan_info}

## Tiltak
{tiltaksbeskrivelse}

## Dispensasjon fra
{dispensasjon_fra}

## Begrunnelse fra søker
{begrunnelse}

Svar BARE med gyldig JSON:
{{
  "dispensasjon_tekst": "Komplett dispensasjonssøknad-tekst med lovhenvisninger, klar til innsending. Inkluder overskrift, innledning, beskrivelse av tiltaket, lovhjemmel, fordel/ulempe-vurdering, og konklusjon.",
  "vurdering_fordeler_ulemper": "Detaljert PBL §19-2 fordel/ulempe-vurdering med konkrete argumenter",
  "sannsynlighet": "Høy/Middels/Lav",
  "sannsynlighet_begrunnelse": "Konkret begrunnelse for sannsynlighetsvurderingen",
  "paragraf_referanser": ["PBL §19-2", "..."],
  "nodvendige_vedlegg": ["Situasjonsplan", "Fasadetegninger", "Nabovarsel", "..."],
  "tips": ["Konkret tips 1", "Konkret tips 2", "..."]
}}"""

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
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
            "eiendom": {"knr": knr, "gnr": gnr, "bnr": bnr, "info": eiendom_info},
            "tiltak": tiltaksbeskrivelse,
            "dispensasjon_fra": dispensasjon_fra,
            **result,
            "disclaimer": (
                "Denne dispensasjonssøknaden er AI-generert beslutningsstøtte og erstatter ikke "
                "juridisk rådgivning fra advokat eller kvalifisert fagperson. "
                "Verifiser alltid mot gjeldende lovtekst på lovdata.no før innsending."
            ),
        }
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Kunne ikke tolke AI-svar: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dispensasjonsgenerering feilet: {exc}")


# ---------------------------------------------------------------------------
# Ferdigattest-sjekk
# ---------------------------------------------------------------------------


@router.post(
    "/ferdigattest-sjekk",
    summary="Sjekk om en eiendom har ferdigattest",
    response_model=dict,
)
async def ferdigattest_sjekk(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    current_user=Depends(get_optional_user),
) -> dict:
    """
    Sjekker om en eiendom har ferdigattest og hva som eventuelt trengs.
    Gratis tjeneste – krever ikke innlogging.
    """
    byggesaker_data: list[dict] = []
    mangler_ferdigattest: list[dict] = []
    har_ferdigattest = True
    eiendom_info = f"Gnr. {gnr}, Bnr. {bnr}, Kommune {knr}"

    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter

        adapter = get_kartverket_adapter()

        # Hent eiendomsdata og byggesaker parallelt
        kr_task = adapter.full_oppslag(knr, gnr, bnr, 0, 0)
        bygg_task = adapter.ebygg.hent_byggesaker(knr, gnr, bnr)
        kr, byggesaker = await asyncio.gather(kr_task, bygg_task, return_exceptions=True)

        if not isinstance(kr, Exception):
            if kr.eiendom:
                eiendom_info = f"{kr.eiendom.adresse}, {kr.kommune.kommunenavn if kr.kommune else knr}"

        if not isinstance(byggesaker, Exception) and byggesaker:
            for sak in byggesaker:
                sak_dict = {
                    "saksnummer": sak.saksnummer,
                    "sakstype": sak.sakstype,
                    "tittel": sak.tittel,
                    "status": sak.status,
                    "vedtaksdato": sak.vedtaksdato,
                    "innsendtdato": sak.innsendtdato,
                    "tiltakstype": sak.tiltakstype,
                }
                byggesaker_data.append(sak_dict)

                # Sjekk om saken mangler ferdigattest
                status_lower = (sak.status or "").lower()
                if any(kw in status_lower for kw in [
                    "igangsettingstillatelse", "rammetillatelse", "godkjent",
                    "ett-trinn", "tillatelse", "ig",
                ]) and not any(kw in status_lower for kw in [
                    "ferdigattest", "ferdig", "avsluttet", "midlertidig brukstillatelse"
                ]):
                    mangler_ferdigattest.append(sak_dict)
                    har_ferdigattest = False

        # Hvis ingen byggesaker funnet, sjekk bygningsstatus
        if not isinstance(kr, Exception) and kr.bygninger and not byggesaker_data:
            for bygg in kr.bygninger:
                bs = (bygg.bygningstatus or "").lower()
                if bs and "ferdigattest" not in bs and "godkjent" not in bs:
                    har_ferdigattest = False

    except Exception:
        pass

    # Generer anbefaling og neste steg
    if har_ferdigattest and byggesaker_data:
        anbefaling = "Eiendommen ser ut til å ha ferdigattest for alle registrerte byggesaker. Ingen umiddelbar handling nødvendig."
        neste_steg = [
            "Bekreft ferdigattest-status hos kommunen for fullstendig dokumentasjon",
            "Be om kopi av ferdigattest fra kommunens arkiv ved behov",
        ]
        estimert_kostnad = "0 kr (verifisering hos kommunen er gratis)"
    elif not byggesaker_data:
        anbefaling = "Vi fant ingen byggesaker registrert på eiendommen. Dette kan bety at bygget er eldre enn digital registrering, eller at saker er arkivert lokalt."
        neste_steg = [
            "Kontakt kommunens byggesaksavdeling for manuelt oppslag",
            "Sjekk om bygget er oppført før 1998 (da er det ofte ikke digitalt registrert)",
            "Be om innsyn i kommunens byggesaksarkiv",
        ]
        estimert_kostnad = "0 - 3 000 kr (avhengig av kommunens gebyrer)"
        har_ferdigattest = False
    else:
        anbefaling = (
            f"Det er funnet {len(mangler_ferdigattest)} byggesak(er) som kan mangle ferdigattest. "
            "Vi anbefaler å kontakte kommunen for å avklare status og hva som eventuelt trengs."
        )
        neste_steg = [
            "Kontakt kommunens byggesaksavdeling for å verifisere status",
            "Samle nødvendig dokumentasjon: sluttrapport fra kontrollerende, samsvarserklæringer, oppdaterte tegninger",
            "Engasjer ansvarlig søker (arkitekt/rådgiver) til å sende inn søknad om ferdigattest",
            "Bestill eventuell sluttkontroll fra uavhengig kontrollør",
            "Send inn søknad om ferdigattest til kommunen",
        ]
        estimert_kostnad = "5 000 - 15 000 kr (avhengig av omfang og kommune)"

    return {
        "eiendom": {"knr": knr, "gnr": gnr, "bnr": bnr, "info": eiendom_info},
        "har_ferdigattest": har_ferdigattest,
        "byggesaker": byggesaker_data,
        "mangler_ferdigattest": mangler_ferdigattest,
        "anbefaling": anbefaling,
        "estimert_kostnad": estimert_kostnad,
        "neste_steg": neste_steg,
    }
