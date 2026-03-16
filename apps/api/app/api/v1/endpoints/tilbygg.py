"""
ByggSjekk – Tilbygganalyse med arealregnestykke.

Beregner hvor mye man kan bygge ut basert på:
1. Tomteareal fra matrikkel
2. Tillatt utnyttelsesgrad fra reguleringsplan (%-BYA)
3. Areal avsatt til ulike formål (bolig, vei, natur)
4. Nåværende bebyggelse (BYA/fotavtrykk)
5. Parkeringsareal (36 m² tommelfingerregel)
6. DIBK-regler for søknadsfritt tilbygg

POST /tilbygg/analyser – Komplett tilbygganalyse med arealregnestykke
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


# DIBK-regler for søknadsfrie tiltak
SOKNADSFRITT_TILBYGG = {
    "maks_bra_m2": 15,
    "maks_avstand_nabogrense_m": 4.0,
    "beskrivelse": (
        "Tilbygg inntil 15 m² BRA kan bygges uten søknad (SAK10 §4-1 c), forutsatt at: "
        "avstand til nabogrense er minst 4 m, tilbygget er i samsvar med reguleringsplan, "
        "og det ikke inneholder rom for varig opphold (beboelse). "
        "Du må melde fra til kommunen innen 4 uker etter ferdigstillelse."
    ),
    "kilde": "https://dibk.no/bygge-eller-endre/sett-opp-tilbygg-uten-a-soke",
}

PARKERING_AREAL_M2 = 36  # Tommelfingerregel for 2 parkeringsplasser


@router.post(
    "/analyser",
    summary="Tilbygganalyse med arealregnestykke – hvor mye kan du bygge?",
    response_model=dict,
)
async def analyser_tilbygg(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    ønsket_tilbygg_m2: Annotated[int | None, Query(description="Ønsket tilbygg i m² BYA")] = None,
    har_garasje_i_huset: Annotated[bool, Query(description="Er parkeringen bygd inn som garasje?")] = False,
    beskrivelse: Annotated[str, Query()] = "",
    current_user=Depends(get_optional_user),
) -> dict:
    """
    Komplett tilbygganalyse:

    1. Henter tomteareal og eksisterende bebyggelse fra Kartverket
    2. Henter tillatt utnyttelsesgrad (%-BYA) fra reguleringsplan/Planslurpen
    3. Beregner arealregnestykke:
       - Tomteareal × BYA% = maks tillatt bebygd areal
       - Minus parkeringsareal (36 m² hvis ikke innbygget garasje)
       - Minus areal til vei/annet
       - Minus eksisterende bebyggelse (BYA/fotavtrykk)
       = Tilgjengelig for utbygging
    4. Sjekker om tilbygget er søknadsfritt (≤15 m², SAK10 §4-1)
    5. AI-analyse med anbefalinger
    """
    try:
        import anthropic

        # ── Hent data ───────────────────────────────────────────
        tomteareal = None
        adresse = f"Gnr. {gnr}, Bnr. {bnr}"
        kommunenavn = knr
        bygninger = []
        eksisterende_bya = 0

        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            kr = await get_kartverket_adapter().full_oppslag(knr, gnr, bnr, 0, 0)
            if not isinstance(kr, Exception):
                if kr.eiendom:
                    tomteareal = kr.eiendom.areal_m2
                    adresse = kr.eiendom.adresse or adresse
                if kr.kommune:
                    kommunenavn = kr.kommune.kommunenavn or knr
                for b in (kr.bygninger or []):
                    bya = b.bruksareal or 0  # BRA som proxy for BYA
                    bygninger.append({
                        "type": b.bygningstype,
                        "bra": b.bruksareal,
                        "bya_estimat": bya,
                        "byggeaar": b.byggeaar,
                    })
                    eksisterende_bya += bya
        except Exception:
            pass

        # Planbestemmelser
        bya_prosent = None
        maks_hoyde = None
        tillatt_bruk = None

        try:
            from services.municipality_connectors.planslurpen import get_planslurpen_adapter
            ps = await get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, 0, 0)
            if not isinstance(ps, Exception) and ps.antall_planer > 0:
                for p in ps.planer[:3]:
                    if p.maks_utnyttelse and bya_prosent is None:
                        # Prøv å ekstrahere tall fra streng som "30% BYA" eller "0.30"
                        import re
                        match = re.search(r'(\d+)\s*%', str(p.maks_utnyttelse))
                        if match:
                            bya_prosent = float(match.group(1))
                        else:
                            try:
                                val = float(str(p.maks_utnyttelse).replace(',', '.'))
                                bya_prosent = val * 100 if val < 1 else val
                            except ValueError:
                                pass
                    if p.maks_hoyde and maks_hoyde is None:
                        maks_hoyde = p.maks_hoyde
                    if p.tillatt_bruk and tillatt_bruk is None:
                        tillatt_bruk = p.tillatt_bruk
        except Exception:
            pass

        # ── Deterministisk arealregnestykke ─────────────────────
        arealregnestykke = {}
        tilgjengelig_m2 = None

        if tomteareal and bya_prosent:
            maks_bya = tomteareal * bya_prosent / 100
            parkering_fratrekk = 0 if har_garasje_i_huset else PARKERING_AREAL_M2
            netto_byggbart = maks_bya - parkering_fratrekk
            tilgjengelig_m2 = max(0, netto_byggbart - eksisterende_bya)

            arealregnestykke = {
                "tomteareal_m2": round(tomteareal),
                "bya_prosent": bya_prosent,
                "maks_tillatt_bya_m2": round(maks_bya),
                "parkering_fratrekk_m2": parkering_fratrekk,
                "parkering_note": "Innbygget garasje – ikke fratrukket" if har_garasje_i_huset else "36 m² for 2 parkeringsplasser (tommelfingerregel)",
                "netto_byggbart_m2": round(netto_byggbart),
                "eksisterende_bebyggelse_bya_m2": round(eksisterende_bya),
                "tilgjengelig_for_utbygging_m2": round(tilgjengelig_m2),
            }

        # ── Søknadsfritt-sjekk ──────────────────────────────────
        soknadsfritt = False
        if tilgjengelig_m2 is not None and tilgjengelig_m2 > 0:
            soknadsfritt = tilgjengelig_m2 <= SOKNADSFRITT_TILBYGG["maks_bra_m2"] or (
                ønsket_tilbygg_m2 is not None and ønsket_tilbygg_m2 <= SOKNADSFRITT_TILBYGG["maks_bra_m2"]
            )

        # ── AI-analyse ──────────────────────────────────────────
        byg_tekst = "\n".join(
            f"- {b['type'] or 'Ukjent'}: BRA={b['bra'] or '?'} m², BYA≈{b['bya_estimat']} m², Byggeår={b['byggeaar'] or '?'}"
            for b in bygninger
        ) if bygninger else "Ingen bygningsdata."

        user_prompt = f"""Analyser tilbyggmuligheter for denne eiendommen.

## Eiendom
- Adresse: {adresse}
- Kommune: {kommunenavn} (knr: {knr}), Gnr/Bnr: {gnr}/{bnr}
- Tomteareal: {f'{tomteareal:.0f} m²' if tomteareal else 'ukjent'}

## Eksisterende bebyggelse
{byg_tekst}
Samlet BYA estimat: {eksisterende_bya} m²

## Reguleringsplan
- Tillatt BYA: {f'{bya_prosent}%' if bya_prosent else 'ukjent'}
- Maks høyde: {maks_hoyde or 'ukjent'}
- Tillatt bruk: {tillatt_bruk or 'ukjent'}

## Arealregnestykke (beregnet)
{json.dumps(arealregnestykke, indent=2, ensure_ascii=False) if arealregnestykke else 'Ikke nok data for beregning'}

## Ønsket tilbygg
{f'{ønsket_tilbygg_m2} m²' if ønsket_tilbygg_m2 else 'Ikke spesifisert'}
Innbygget garasje: {'Ja' if har_garasje_i_huset else 'Nei'}
Beskrivelse: {beskrivelse or 'Ikke oppgitt'}

Svar BARE med gyldig JSON:
{{
  "kan_bygge_tilbygg": true,
  "maks_tilbygg_m2": {round(tilgjengelig_m2) if tilgjengelig_m2 else 0},
  "konklusjon": "Kort konklusjon (2-3 setninger)",
  "soknadsfritt": {{
    "mulig": {str(soknadsfritt).lower()},
    "maks_m2": 15,
    "vilkaar": ["Min 4m til nabogrense", "Ikke rom for varig opphold", "I samsvar med reguleringsplan"],
    "meldeplikt": "Meld fra til kommunen innen 4 uker",
    "dibk_lenke": "https://dibk.no/bygge-eller-endre/sett-opp-tilbygg-uten-a-soke"
  }},
  "soknadsplikt_vurdering": {{
    "type": "Søknadsfritt/Forenklet søknad/Full byggesøknad",
    "begrunnelse": "Hvorfor denne søknadstypen gjelder",
    "hjemmel": "SAK10 §4-1 / PBL §20-1 / PBL §20-4"
  }},
  "forslag": [
    {{
      "navn": "Forslag 1: Tilbygg {ønsket_tilbygg_m2 or 15} m²",
      "bya_m2": {ønsket_tilbygg_m2 or 15},
      "soknadstype": "Søknadsfritt/Forenklet/Full",
      "estimert_kostnad": "150 000 – 300 000 kr",
      "gjennomforbarhet": "Høy/Middels/Lav",
      "beskrivelse": "Kort beskrivelse"
    }}
  ],
  "tek17_krav": [
    {{
      "krav": "TEK17-krav som gjelder",
      "paragraf": "TEK17 §12-2",
      "relevant_for_tilbygg": true,
      "kommentar": "Detaljer"
    }}
  ],
  "anbefalinger": ["Anbefaling 1", "Anbefaling 2"],
  "neste_steg": ["Steg 1", "Steg 2"],
  "dokumenter_som_trengs": ["Situasjonsplan", "Fasadetegninger", "Snitt-tegninger"]
}}"""

        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=(
                "Du er en norsk byggesaksekspert med kunnskap om PBL, SAK10, TEK17 og DIBK-veiledere. "
                "Gi presise arealberegninger basert på dataene. Bruk realistiske kostnadsestimater. "
                "Sjekk alltid om tiltaket kan gjøres søknadsfritt etter SAK10 §4-1. "
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
                "tomteareal_m2": tomteareal,
            },
            "arealregnestykke": arealregnestykke or ai.get("arealregnestykke", {}),
            "eksisterende_bygninger": bygninger,
            **ai,
            "dibk_veiledere": {
                "tilbygg_uten_soknad": "https://dibk.no/bygge-eller-endre/sett-opp-tilbygg-uten-a-soke",
                "garasje_uten_soknad": "https://dibk.no/bygge-eller-endre/sett-opp-garasje-uten-a-soke",
                "bod_uten_soknad": "https://dibk.no/bygge-eller-endre/sett-opp-frittliggende-bygning-uten-a-soke",
            },
            "disclaimer": (
                "Arealberegningene er basert på offentlige registerdata og kan avvike fra faktiske forhold. "
                "BYA-estimat er basert på BRA fra matrikkelen og kan avvike. "
                "Verifiser alltid med oppmåling og kommunens byggesaksavdeling."
            ),
        }

    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI-svar feilet: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tilbygganalyse feilet: {exc}")
