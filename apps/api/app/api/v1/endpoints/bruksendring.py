"""
ByggSjekk – Bruksendring-analyse.

Sjekker om planlagt bruksendring er søknadspliktig og hva som kreves.
Typiske bruksendringer:
- Kjeller → boareal (soverom, stue)
- Loft → oppholdsrom
- Garasje → hybel/kontor
- Bod → soverom
- Næring → bolig (eller omvendt)

POST /bruksendring/analyser
"""
from __future__ import annotations

import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_optional_user, require_ai_access

router = APIRouter()

for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# TEK17-krav for rom til varig opphold
TEK17_KRAV_OPPHOLDSROM = {
    "romhoyde_min_m": 2.4,
    "romhoyde_unntak_m": 2.2,  # Ved bruksendring tilleggsdel→hoveddel (TEK17 §12-7(3))
    "dagslys_min_prosent": 10,  # Min 10% av gulvareal som vindusareal
    "ventilasjon_min_ls_m2": 0.7,  # Min 0,7 l/s per m² tilluft
    "lyd_mellom_boenheter_rw": 55,  # R'w ≥ 55 dB luftlyd
    "lyd_trinnlyd_lnw": 53,  # L'nw ≤ 53 dB trinnlyd
    "radon_maks_bq": 200,  # Maks 200 Bq/m³
    "romning_vindu_min_m2": 0.5,  # Min 0,5 m² åpningsareal for rømningsvindu
}


@router.post(
    "/analyser",
    summary="Bruksendring-analyse – er det søknadspliktig og hva kreves?",
    response_model=dict,
)
async def analyser_bruksendring(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    fra_bruk: Annotated[str, Query(description="Nåværende bruk: kjeller|loft|garasje|bod|næring|tilleggsdel")] = "kjeller",
    til_bruk: Annotated[str, Query(description="Ønsket bruk: soverom|stue|hybel|kontor|bolig|oppholdsrom")] = "soverom",
    areal_m2: Annotated[int | None, Query()] = None,
    under_terreng: Annotated[bool, Query(description="Er rommet under terreng?")] = False,
    beskrivelse: Annotated[str, Query()] = "",
    current_user=Depends(get_optional_user),
) -> dict:
    """
    Komplett bruksendring-analyse:

    1. Sjekker om endringen er søknadspliktig (PBL §20-1 d)
    2. Vurderer TEK17-krav: romhøyde, dagslys, ventilasjon, lyd, radon, rømning
    3. Identifiserer typiske utfordringer basert på romtype
    4. Estimerer kostnader for nødvendige tiltak
    5. Kobler mot avvikstjenesten (funnet i Finn-analyse etc.)
    """
    try:
        import anthropic

        # Hent eiendomsdata
        adresse = f"Gnr. {gnr}, Bnr. {bnr}"
        kommunenavn = knr
        bygninger = []

        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            kr = await get_kartverket_adapter().full_oppslag(knr, gnr, bnr, 0, 0)
            if not isinstance(kr, Exception):
                if kr.eiendom:
                    adresse = kr.eiendom.adresse or adresse
                if kr.kommune:
                    kommunenavn = kr.kommune.kommunenavn or knr
                for b in (kr.bygninger or []):
                    bygninger.append({
                        "type": b.bygningstype,
                        "bra": b.bruksareal,
                        "byggeaar": b.byggeaar,
                    })
        except Exception:
            pass

        byg_tekst = "\n".join(
            f"- {b['type'] or 'Ukjent'}: BRA={b['bra'] or '?'} m², Byggeår={b['byggeaar'] or '?'}"
            for b in bygninger
        ) if bygninger else "Ingen bygningsdata."

        user_prompt = f"""Analyser denne bruksendringen:

## Eiendom
- Adresse: {adresse}, {kommunenavn} ({knr}), Gnr/Bnr: {gnr}/{bnr}

## Eksisterende bygninger
{byg_tekst}

## Bruksendring
- Fra: {fra_bruk}
- Til: {til_bruk}
- Areal: {f'{areal_m2} m²' if areal_m2 else 'ikke oppgitt'}
- Under terreng: {'Ja' if under_terreng else 'Nei'}
- Beskrivelse: {beskrivelse or 'Ikke oppgitt'}

## TEK17-krav for rom til varig opphold
{json.dumps(TEK17_KRAV_OPPHOLDSROM, indent=2)}

Svar BARE med gyldig JSON:
{{
  "soknadsplikt": {{
    "er_soknadsplikt": true,
    "type": "Søknadspliktig med ansvarsrett / Søknadspliktig uten ansvarsrett / Ikke søknadspliktig",
    "hjemmel": "PBL §20-1 d",
    "begrunnelse": "Detaljert forklaring"
  }},
  "tek17_sjekkliste": [
    {{
      "krav": "Romhøyde min 2,4m (2,2m ved bruksendring tilleggsdel→hoveddel)",
      "paragraf": "TEK17 §12-7",
      "sannsynlig_oppfylt": true,
      "kommentar": "Kjeller fra 70-tallet har ofte 2,1-2,3m – kan være for lavt",
      "tiltak_hvis_ikke": "Senke gulv eller heve tak (kostbart)"
    }}
  ],
  "typiske_utfordringer": [
    {{
      "utfordring": "For lav romhøyde i kjeller",
      "alvorlighet": "Kritisk/Viktig/Moderat",
      "losning": "Senke gulv (50 000-150 000 kr) eller søke dispensasjon",
      "kostnad_estimat": "50 000 - 150 000 kr"
    }}
  ],
  "rom_under_terreng_krav": {{
    "gjelder": {str(under_terreng).lower()},
    "ekstra_krav": ["Fuktbeskyttelse og drenering", "Radonsperre", "Mekanisk ventilasjon", "Lysgraver for dagslys"]
  }},
  "avvik_risiko": {{
    "typiske_avvik_ved_denne_bruksendringen": [
      "Beskrivelse av vanlig avvik"
    ],
    "konsekvens_hvis_ulovlig": "Kommunen kan kreve tilbakeføring, dagbøter, påvirker salgsverdi"
  }},
  "kostnadsestimat": {{
    "enkel_bruksendring": "30 000 - 80 000 kr",
    "med_bygningsarbeid": "100 000 - 400 000 kr",
    "kommunale_gebyrer": "7 000 - 15 000 kr",
    "arkitekt_tegninger": "20 000 - 50 000 kr"
  }},
  "dokumenter_som_trengs": [
    "Søknadsskjema", "Plantegninger (eksisterende og ny)", "Snitt-tegninger", "Nabovarsel"
  ],
  "anbefalinger": ["Anbefaling 1", "Anbefaling 2"],
  "neste_steg": ["Steg 1: Mål romhøyde", "Steg 2: Sjekk dagslys", "Steg 3: ..."],
  "nops_tjenester": [
    {{"tjeneste": "Avviksdeteksjon", "relevans": "Sjekk om bruksendringen allerede er gjort ulovlig", "lenke": "/property"}},
    {{"tjeneste": "Tegninger", "relevans": "Vi tegner nye plantegninger for bruksendringssøknaden", "lenke": "/dokumenter"}},
    {{"tjeneste": "Dispensasjon", "relevans": "Søk dispensasjon fra TEK17-krav som ikke oppfylles", "lenke": "/dispensasjon"}}
  ]
}}"""

        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=(
                "Du er en norsk byggesaksekspert spesialisert på bruksendringer. "
                "Du kjenner TEK17-krav for rom til varig opphold (§12-7), brannkrav (kap 11), "
                "radon (§13-5), lyd (§13-7), dagslys og ventilasjon. "
                "Du vet at kjellere fra 60-80-tallet ofte har for lav romhøyde. "
                "Du vet at TEK17 §12-7(3) tillater lavere romhøyde ved bruksendring tilleggsdel→hoveddel. "
                "Gi realistiske kostnadsestimater. "
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
        ai = json.loads(text)

        return {
            "eiendom": {
                "knr": knr, "gnr": gnr, "bnr": bnr,
                "adresse": adresse, "kommunenavn": kommunenavn,
            },
            "bruksendring": {
                "fra": fra_bruk, "til": til_bruk,
                "areal_m2": areal_m2, "under_terreng": under_terreng,
            },
            "tek17_referansekrav": TEK17_KRAV_OPPHOLDSROM,
            **ai,
            "disclaimer": (
                "Denne analysen er AI-generert beslutningsstøtte. "
                "TEK17-krav må verifiseres med oppmåling av faktiske forhold. "
                "Konsulter kvalifisert fagperson for søknad om bruksendring."
            ),
        }

    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI-svar feilet: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bruksendringsanalyse feilet: {exc}")
