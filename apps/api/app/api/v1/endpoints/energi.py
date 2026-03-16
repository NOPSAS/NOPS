"""
ByggSjekk – Energiradgivningstjeneste.

POST /energi/analyser   – AI-basert energianalyse med Enova-stotte og TEK17-sjekk
GET  /energi/enova-kalkulator – Deterministisk Enova-stotteberegning
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.core.deps import get_optional_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hent_eiendomsdata(knr: str, gnr: str, bnr: str) -> dict:
    """Henter bygningsdata fra Kartverket. Returnerer best-effort dict."""
    result: dict = {"byggeaar": None, "bra_m2": None, "bygningstype": None}
    try:
        import httpx

        url = (
            f"https://api.kartverket.no/eiendom/v1/matrikkelenheter/{knr}-{gnr}/{bnr}"
        )
        with httpx.Client(timeout=8) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                bygninger = data.get("bygninger") or []
                if bygninger:
                    b = bygninger[0]
                    result["byggeaar"] = b.get("byggeaar")
                    result["bra_m2"] = b.get("bruksareal") or b.get("bruksarealTotalt")
                    result["bygningstype"] = b.get("bygningstype", {}).get(
                        "tekst"
                    ) or b.get("bygningstype", {}).get("kode")
    except Exception:
        pass

    # Fallback: prov matrikkel-API
    if result["byggeaar"] is None:
        try:
            import httpx

            url2 = f"https://ws.geonorge.no/adresser/v1/sok?kommunenummer={knr}&gardsnummer={gnr}&bruksnummer={bnr}&treffPerSide=1"
            with httpx.Client(timeout=5) as client:
                resp2 = client.get(url2)
                if resp2.status_code == 200:
                    hits = resp2.json().get("adresser", [])
                    if hits:
                        result["bygningstype"] = result["bygningstype"] or "Bolig"
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Endepunkt 1: POST /energi/analyser
# ---------------------------------------------------------------------------

@router.post("/analyser", summary="AI-basert energianalyse for norsk bolig")
async def analyser_energi(
    knr: str = Query(..., description="Kommunenummer, f.eks. 0301"),
    gnr: str = Query(..., description="Gardsnummer"),
    bnr: str = Query(..., description="Bruksnummer"),
    oppvarmingskilde: str = Query(
        "elektrisk",
        description="Oppvarmingskilde: elektrisk|varmepumpe|fjernvarme|ved|olje|gass",
    ),
    har_solceller: bool = Query(False, description="Har boligen solceller?"),
    planlagte_tiltak: str = Query(
        "",
        description="Kommaseparerte tiltak: etterisolering,vinduer,varmepumpe,solceller",
    ),
    user=Depends(get_optional_user),
) -> dict:
    """
    Gratis grunnanalyse av energistatus for en norsk bolig.

    Henter eiendomsdata fra Kartverket og bruker Claude til a generere
    energiprofil, bygningsanalyse, anbefalte tiltak, Enova-stotte,
    TEK17-sjekk og energimerke-potensial.
    """

    eiendom = _hent_eiendomsdata(knr, gnr, bnr)
    byggeaar = eiendom.get("byggeaar") or "ukjent"
    bra = eiendom.get("bra_m2") or "ukjent"
    bygningstype = eiendom.get("bygningstype") or "ukjent"

    tiltak_tekst = planlagte_tiltak if planlagte_tiltak else "ingen"

    prompt = f"""Lag en komplett energianalyse for denne norske boligen.

Eiendom: {knr}-{gnr}/{bnr}
Byggeaar: {byggeaar}
Bruksareal (BRA): {bra} m2
Bygningstype: {bygningstype}
Oppvarmingskilde: {oppvarmingskilde}
Har solceller: {har_solceller}
Planlagte tiltak: {tiltak_tekst}

Bruk realistiske norske priser, U-verdier og Enova-satser (2024/2025).
Energimerke-skala kWh/m2: A<95, B<120, C<145, D<175, E<205, F<250, G>250.
Strompris: ca 1.50 kr/kWh inkl. nettleie. CO2-utslipp: elektrisk=0, olje=2.68 kg/kWh, gass=2.0 kg/kWh, ved=0 (fornybar), fjernvarme=0.1 kg/kWh.

Svar BARE med gyldig JSON (ingen kommentarer, ingen markdown):
{{
  "energiprofil": {{
    "estimert_energimerke": "<A-G>",
    "estimert_forbruk_kwh": <int>,
    "forbruk_per_m2": <int>,
    "nasjonalt_gjennomsnitt_kwh_m2": 150,
    "over_under_snitt": "<+/-X%>",
    "co2_utslipp_kg": <int>,
    "energikostnad_aar_kr": <int>
  }},
  "bygningsanalyse": {{
    "byggeaar": {byggeaar if isinstance(byggeaar, int) else f'"{byggeaar}"'},
    "antatt_isolasjonsstandard": "<beskrivelse>",
    "antatt_vinduer": "<beskrivelse>",
    "antatt_tetthet": "<beskrivelse med luftvekslinger/t>",
    "antatt_u_verdi_vegg": <float>,
    "antatt_u_verdi_tak": <float>,
    "antatt_u_verdi_vindu": <float>,
    "svake_punkter": ["<punkt1>", "<punkt2>", "<punkt3>"]
  }},
  "anbefalte_tiltak": [
    {{
      "prioritet": <int>,
      "tiltak": "<navn>",
      "beskrivelse": "<konkret beskrivelse>",
      "estimert_kostnad_kr": <int>,
      "estimert_besparelse_aar_kr": <int>,
      "tilbakebetalingstid_aar": <float>,
      "enova_stotte_kr": <int>,
      "netto_kostnad_kr": <int>,
      "ny_u_verdi": <float eller null>,
      "energibesparelse_kwh": <int>,
      "co2_reduksjon_kg": <int>,
      "kompleksitet": "<Lav|Middels|Hoy>"
    }}
  ],
  "enova_muligheter": {{
    "total_mulig_stotte_kr": <int>,
    "tiltak_med_stotte": [
      {{"tiltak": "<navn>", "maks_stotte": <int>, "vilkaar": "<vilkar>"}}
    ],
    "lenke": "https://www.enova.no/privat/"
  }},
  "energimerke_potensial": {{
    "naavaerende": "<A-G>",
    "etter_alle_tiltak": "<A-G>",
    "forbedring_steg": ["<X->Y: tiltak>"]
  }},
  "sammenligning_tek17": {{
    "oppfyller_tek17": <true|false>,
    "mangler": ["<mangel1>", "<mangel2>"],
    "estimert_kostnad_tek17_nivaa": <int>
  }},
  "tips": ["<tip1>", "<tip2>", "<tip3>"],
  "neste_steg": ["Bestill energiradgivning via Enova", "Kontakt nops.no for 3D-modell og energiberegning"]
}}"""

    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise HTTPException(
                status_code=503, detail="ANTHROPIC_API_KEY ikke konfigurert"
            )

        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system="Du er en norsk energiradgiver med kunnskap om TEK17 \u00a714-2, Enova-stotteordninger og norsk byggeskikk. Estimer energiforbruk basert pa byggeaar, areal og bygningstype. Bruk realistiske norske priser og U-verdier. Energimerke A-G basert pa kWh/m2: A<95, B<120, C<145, D<175, E<205, F<250, G>250.",
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
                "byggeaar": byggeaar,
                "bra_m2": bra,
                "bygningstype": bygningstype,
            },
            **analyse,
        }

    except ImportError:
        raise HTTPException(
            status_code=503, detail="Anthropic-modulen er ikke installert"
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502, detail=f"AI-svar kunne ikke tolkes: {exc}"
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Energianalyse feilet: {exc}"
        )


# ---------------------------------------------------------------------------
# Endepunkt 2: GET /energi/enova-kalkulator
# ---------------------------------------------------------------------------

ENOVA_SATSER = {
    "etterisolering": {
        "stotte_per_m2": 200,
        "maks_stotte": 30000,
        "vilkaar": "U-verdi <= 0.18 W/(m2K)",
    },
    "vinduer": {
        "stotte_per_m2": 150,
        "maks_stotte": 20000,
        "vilkaar": "U-verdi <= 0.80 W/(m2K)",
    },
    "varmepumpe": {
        "stotte_fast": 10000,
        "maks_stotte": 10000,
        "vilkaar": "Luft-vann eller bergvarme",
    },
    "solceller": {
        "stotte_per_kwp": 2000,
        "maks_stotte": 15000,
        "vilkaar": "Tilknyttet stromnettet",
    },
    "balansert_ventilasjon": {
        "stotte_fast": 15000,
        "maks_stotte": 15000,
        "vilkaar": "Balansert ventilasjon med varmegjenvinning >= 80%",
    },
}


@router.get(
    "/enova-kalkulator",
    summary="Deterministisk Enova-stotteberegning",
)
async def enova_kalkulator(
    tiltak: str = Query(
        ...,
        description="Kommaseparerte tiltak: etterisolering,vinduer,varmepumpe,solceller,balansert_ventilasjon",
    ),
    areal_m2: int = Query(..., description="Bruksareal i kvadratmeter"),
) -> dict:
    """
    Enklere deterministisk beregning av Enova-stotte basert pa kjente satser.
    Krever ingen AI-kall.
    """
    valgte = [t.strip().lower().replace(" ", "_") for t in tiltak.split(",") if t.strip()]

    resultater = []
    total_stotte = 0

    for t in valgte:
        if t not in ENOVA_SATSER:
            continue

        sats = ENOVA_SATSER[t]
        maks = sats["maks_stotte"]

        if "stotte_per_m2" in sats:
            beregnet = min(sats["stotte_per_m2"] * areal_m2, maks)
        elif "stotte_per_kwp" in sats:
            # Estimer kWp basert pa takflate (ca 15% av BRA)
            estimert_kwp = max(1, math.floor(areal_m2 * 0.15 / 7))
            beregnet = min(sats["stotte_per_kwp"] * estimert_kwp, maks)
        else:
            beregnet = sats.get("stotte_fast", 0)

        beregnet = int(beregnet)
        total_stotte += beregnet

        resultater.append(
            {
                "tiltak": t,
                "estimert_stotte_kr": beregnet,
                "maks_stotte_kr": maks,
                "vilkaar": sats["vilkaar"],
            }
        )

    ukjente = [t for t in valgte if t not in ENOVA_SATSER]

    return {
        "areal_m2": areal_m2,
        "tiltak_beregnet": resultater,
        "ukjente_tiltak": ukjente,
        "total_estimert_stotte_kr": total_stotte,
        "merknad": "Beregningen er basert pa kjente Enova-satser og er et estimat. Faktisk stotte avhenger av dokumentasjon og godkjenning.",
        "lenke": "https://www.enova.no/privat/",
    }
