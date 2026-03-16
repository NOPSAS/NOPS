"""
ByggSjekk – Finn.no Boliganalyse.

Henter og analyserer boligannonser fra Finn.no:
1. Scraper annonsedata (pris, areal, bilder, plantegninger, salgsoppgave)
2. Analyserer bilder og plantegninger med Claude Vision
3. Sammenligner med Kartverket matrikkeldata for å finne avvik
4. Genererer en komplett eiendomsrapport (visning.ai-stil)
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import sys
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.deps import get_current_user, require_ai_access
from app.models.user import User
import httpx

router = APIRouter()

# sys.path setup som i property.py
_here = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.abspath(os.path.join(_here, "../../.."))
_project_root = os.path.abspath(os.path.join(_api_root, "../.."))
for _p in [_api_root, _project_root, os.path.join(_project_root, "services")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------


async def _hent_finn_annonse(finn_url: str) -> dict:
    """Henter og parser en Finn.no boligannonse."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(
            finn_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Kunne ikke hente Finn-annonse: HTTP {resp.status_code}",
            )

        html = resp.text

        # Ekstraher JSON-LD
        json_ld: dict = {}
        ld_matches = re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        for match in ld_matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, dict):
                    json_ld.update(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            json_ld.update(item)
            except json.JSONDecodeError:
                pass

        # Ekstraher OG-tags
        og_data: dict = {}
        og_matches = re.findall(
            r'<meta\s+(?:property|name)="og:(\w+)"\s+content="([^"]*)"', html
        )
        for key, value in og_matches:
            og_data[key] = value

        # Ekstraher alle bilde-URLer (Finn bruker ofte img med data-src eller src)
        bilde_urls: list[str] = []
        # Finn.no bruker ofte mye bilder i ulike formater
        img_matches = re.findall(
            r"https://images\.finncdn\.no/dynamic/\d+x\d+c/[^\"'>\s]+", html
        )
        # Dedupliser og ta unike
        seen: set[str] = set()
        for url in img_matches:
            # Normaliser til stor versjon
            normalized = re.sub(r"/dynamic/\d+x\d+c/", "/dynamic/1600w/", url)
            if normalized not in seen:
                seen.add(normalized)
                bilde_urls.append(normalized)

        if not bilde_urls:
            # Fallback: alle img-src
            img_matches2 = re.findall(
                r'<img[^>]+src="(https://[^"]+finncdn[^"]+)"', html
            )
            bilde_urls = list(set(img_matches2))[:20]

        # Ekstraher tittel
        tittel = og_data.get("title", "")
        if not tittel:
            title_match = re.search(r"<title>([^<]+)</title>", html)
            tittel = title_match.group(1).strip() if title_match else ""

        # Ekstraher pris
        pris_tekst = ""
        pris_match = re.search(r"(\d[\d\s]*\d)\s*kr", html)
        if pris_match:
            pris_tekst = pris_match.group(1).replace(" ", "").replace("\xa0", "")

        # Ekstraher beskrivelse
        beskrivelse = og_data.get("description", "")

        # Ekstraher adresse fra tittel eller OG
        adresse = ""
        # Finn-titler er ofte "Adresse - Boligtype - Sted"
        if tittel and " - " in tittel:
            adresse = tittel.split(" - ")[0].strip()

        # Ekstraher Finn-kode
        finnkode = ""
        kode_match = re.search(r"finnkode[:\s]*(\d+)", html, re.IGNORECASE)
        if not kode_match:
            kode_match = re.search(r"/(\d{8,12})(?:\?|$|\")", finn_url)
        if kode_match:
            finnkode = kode_match.group(1)

        # Ekstraher nøkkelinfo fra HTML (typisk i dl/dt/dd eller tabellformat)
        nøkkelinfo: dict = {}
        # Finn.no bruker ofte key-value pairs
        kv_matches = re.findall(
            r"<dt[^>]*>([^<]+)</dt>\s*<dd[^>]*>([^<]+)</dd>", html
        )
        for k, v in kv_matches:
            nøkkelinfo[k.strip()] = v.strip()

        return {
            "finn_url": finn_url,
            "finnkode": finnkode,
            "tittel": tittel,
            "adresse": adresse,
            "pris_tekst": pris_tekst,
            "beskrivelse": beskrivelse,
            "bilde_urls": bilde_urls[:15],  # Maks 15 bilder
            "nøkkelinfo": nøkkelinfo,
            "json_ld": json_ld,
            "antall_bilder": len(bilde_urls),
        }


async def _analyser_bilder_med_claude(bilde_urls: list[str], kontekst: str) -> dict:
    """Analyserer inntil 5 bilder fra annonsen med Claude Vision."""
    import anthropic

    # Last ned bilder
    bilder_b64: list[dict] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for url in bilde_urls[:5]:
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) < 5_000_000:
                    b64 = base64.standard_b64encode(resp.content).decode()
                    content_type = resp.headers.get("content-type", "image/jpeg")
                    if "jpeg" in content_type or "jpg" in content_type:
                        media_type = "image/jpeg"
                    elif "png" in content_type:
                        media_type = "image/png"
                    elif "webp" in content_type:
                        media_type = "image/webp"
                    else:
                        media_type = "image/jpeg"
                    bilder_b64.append({"b64": b64, "media_type": media_type})
            except Exception:
                pass

    if not bilder_b64:
        return {"feil": "Ingen bilder kunne lastes ned for analyse"}

    # Bygg Claude Vision melding
    content_blocks: list[dict] = []
    for img in bilder_b64:
        content_blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["media_type"],
                    "data": img["b64"],
                },
            }
        )

    content_blocks.append(
        {
            "type": "text",
            "text": f"""Analyser disse bildene fra en norsk boligannonse.

Kontekst: {kontekst}

Svar BARE med gyldig JSON:
{{
  "bildetype_fordeling": {{
    "eksteriør": 0,
    "interiør": 0,
    "plantegning": 0,
    "kart": 0,
    "annet": 0
  }},
  "bygningsanalyse": {{
    "bygningstype": "Enebolig/Tomannsbolig/Leilighet/Rekkehus",
    "estimert_byggeaar": "1970-tallet",
    "estimert_bra_m2": 0,
    "antall_etasjer": 0,
    "arkitekturstil": "Beskrivende stil",
    "generell_tilstand": "God/Middels/Renoveringsbehov",
    "materialer": ["Tre", "Mur"],
    "tak_type": "Saltak/Flatt tak/Valmtak"
  }},
  "plantegning_analyse": {{
    "funnet_plantegning": true,
    "antall_soverom_i_plantegning": 0,
    "antall_bad": 0,
    "har_kjeller": false,
    "har_loft": false,
    "spesielle_rom": ["Kontor", "Vaskerom"],
    "mulige_avvik": ["Beskrivelse av potensielt avvik mellom plantegning og bilder"]
  }},
  "avviksdeteksjon": {{
    "funnet_avvik": false,
    "avvik_beskrivelser": ["Mulig avvik: kjeller ser ut til å være innredet som boareal uten at det fremgår av plantegningen"],
    "alvorlighetsgrad": "Ingen/Lav/Middels/Høy"
  }},
  "forbedringspotensial": [
    {{
      "type": "Fasadeoppgradering/Tilbygg/Innvendig renovering",
      "beskrivelse": "Hva kan gjøres",
      "estimert_kostnad": "100 000 - 300 000 kr",
      "verdiøkning_estimat": "200 000 - 500 000 kr"
    }}
  ],
  "oppsummering": "Kort norsk oppsummering av eiendommen basert på bildene (3-5 setninger)"
}}""",
        }
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    aclient = anthropic.AsyncAnthropic(api_key=api_key)
    response = await aclient.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": content_blocks}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"rå_analyse": text, "feil": "Kunne ikke parse Claude-respons som JSON"}


async def _hent_matrikkeldata_fra_adresse(adresse: str) -> dict | None:
    """Slår opp adresse i Geonorge og henter matrikkeldata fra Kartverket."""
    if not adresse or len(adresse.strip()) < 3:
        return None

    async with httpx.AsyncClient(timeout=10) as client:
        # Steg 1: Adressesøk i Geonorge
        try:
            resp = await client.get(
                "https://ws.geonorge.no/adresser/v1/sok",
                params={"sok": adresse, "fuzzy": "true", "treffPerSide": "1"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            adresser = data.get("adresser", [])
            if not adresser:
                return None

            adr = adresser[0]
            knr = adr.get("kommunenummer", "")
            gnr = adr.get("gardsnummer")
            bnr = adr.get("bruksnummer")
            if not knr or gnr is None or bnr is None:
                return None
        except Exception:
            return None

        # Steg 2: Hent matrikkeldata fra Kartverket
        matrikkel: dict = {
            "knr": knr,
            "gnr": gnr,
            "bnr": bnr,
            "registrert_areal": None,
            "byggeaar": None,
            "bygningstype": None,
            "har_ferdigattest": None,
        }

        try:
            # Kartverket Matrikkel-API: hent bygninger på eiendommen
            resp = await client.get(
                f"https://ws.geonorge.no/adresser/v1/sok",
                params={
                    "kommunenummer": knr,
                    "gardsnummer": str(gnr),
                    "bruksnummer": str(bnr),
                    "treffPerSide": "5",
                },
            )
            if resp.status_code == 200:
                detaljer = resp.json()
                if detaljer.get("adresser"):
                    a = detaljer["adresser"][0]
                    matrikkel["poststed"] = a.get("poststed", "")
                    matrikkel["postnummer"] = a.get("postnummer", "")
        except Exception:
            pass

        # Kartverket Bygningsdata via Se Eiendom (enkel oppslag)
        try:
            resp = await client.get(
                "https://ws.geonorge.no/kommuneinfo/v1/kommuner/" + knr,
            )
            if resp.status_code == 200:
                kommune_data = resp.json()
                matrikkel["kommune_navn"] = kommune_data.get(
                    "kommunenavnNorsk", kommune_data.get("kommunenavn", "")
                )
        except Exception:
            pass

        matrikkel[
            "seeiendom_url"
        ] = f"https://seeiendom.kartverket.no/eiendom/{knr}/{gnr}/{bnr}"

        return matrikkel


def _generer_avviksrapport(
    finn_data: dict,
    matrikkel_data: dict | None,
    bilde_analyse: dict | None,
) -> dict:
    """Sammenligner data fra ulike kilder og genererer avviksrapport."""
    avvik: list[dict] = []

    # Areal-avvik
    annonsert_areal = None
    for key in ("Primærrom", "Bruksareal", "P-rom", "BRA", "Boligareal"):
        val = finn_data.get("nøkkelinfo", {}).get(key, "")
        if val:
            tall = re.search(r"(\d+)", val)
            if tall:
                annonsert_areal = int(tall.group(1))
                break

    matrikkel_areal = (
        matrikkel_data.get("registrert_areal") if matrikkel_data else None
    )
    estimert_areal = None
    if bilde_analyse and isinstance(bilde_analyse.get("bygningsanalyse"), dict):
        estimert_areal = bilde_analyse["bygningsanalyse"].get("estimert_bra_m2")

    if annonsert_areal and matrikkel_areal:
        diff = abs(annonsert_areal - matrikkel_areal)
        if diff > 10:
            alvorlighet = "HØY" if diff > 30 else "MIDDELS"
            avvik.append(
                {
                    "type": "AREAL_AVVIK",
                    "beskrivelse": (
                        f"Annonsert areal {annonsert_areal} m², "
                        f"matrikkel viser {matrikkel_areal} m² (differanse {diff} m²)"
                    ),
                    "alvorlighet": alvorlighet,
                    "anbefaling": "Be om dokumentasjon på eventuelle ombygginger eller tilbygg",
                }
            )

    if annonsert_areal and estimert_areal and estimert_areal > 0:
        diff = abs(annonsert_areal - estimert_areal)
        if diff > 20:
            avvik.append(
                {
                    "type": "AREAL_ESTIMAT_AVVIK",
                    "beskrivelse": (
                        f"Annonsert areal {annonsert_areal} m², "
                        f"visuelt estimat fra bilder: ~{estimert_areal} m²"
                    ),
                    "alvorlighet": "LAV",
                    "anbefaling": "Verifiser areal ved visning",
                }
            )

    # Byggeår-avvik
    annonsert_byggeaar = None
    for key in ("Byggeår", "Byggeaar", "Oppført"):
        val = finn_data.get("nøkkelinfo", {}).get(key, "")
        if val:
            tall = re.search(r"(\d{4})", val)
            if tall:
                annonsert_byggeaar = int(tall.group(1))
                break

    matrikkel_byggeaar = (
        matrikkel_data.get("byggeaar") if matrikkel_data else None
    )
    if annonsert_byggeaar and matrikkel_byggeaar:
        if abs(annonsert_byggeaar - matrikkel_byggeaar) > 2:
            avvik.append(
                {
                    "type": "BYGGEÅR_AVVIK",
                    "beskrivelse": (
                        f"Annonsert byggeår {annonsert_byggeaar}, "
                        f"matrikkel viser {matrikkel_byggeaar}"
                    ),
                    "alvorlighet": "LAV",
                    "anbefaling": "Kan skyldes rehabilitering – verifiser med selger",
                }
            )

    # Ferdigattest-sjekk
    if matrikkel_data and matrikkel_data.get("har_ferdigattest") is False:
        avvik.append(
            {
                "type": "MANGLENDE_FERDIGATTEST",
                "beskrivelse": "Eiendommen mangler registrert ferdigattest i matrikkelen",
                "alvorlighet": "HØY",
                "anbefaling": (
                    "Be selger om ferdigattest. Sjekk om det finnes "
                    "midlertidig brukstillatelse. Manglende ferdigattest "
                    "kan indikere ulovlige byggearbeider."
                ),
            }
        )

    # Avvik fra bildeanalyse
    if bilde_analyse and isinstance(bilde_analyse.get("avviksdeteksjon"), dict):
        ba_avvik = bilde_analyse["avviksdeteksjon"]
        if ba_avvik.get("funnet_avvik"):
            for beskr in ba_avvik.get("avvik_beskrivelser", []):
                avvik.append(
                    {
                        "type": "VISUELT_AVVIK",
                        "beskrivelse": beskr,
                        "alvorlighet": ba_avvik.get("alvorlighetsgrad", "LAV"),
                        "anbefaling": "Verifiser ved visning og be om dokumentasjon",
                    }
                )

    # Beregn risiko-nivå
    if any(a["alvorlighet"] == "HØY" for a in avvik):
        risiko = "HØY"
    elif any(a["alvorlighet"] == "MIDDELS" for a in avvik):
        risiko = "MIDDELS"
    elif avvik:
        risiko = "LAV"
    else:
        risiko = "LAV"

    return {
        "funnet_avvik": len(avvik) > 0,
        "avvik": avvik,
        "risiko_nivaa": risiko,
    }


def _generer_eiendomsoppsummering(
    finn_data: dict,
    matrikkel_data: dict | None,
    bilde_analyse: dict | None,
    avviksrapport: dict,
) -> dict:
    """Genererer eiendomsoppsummering basert på alle analyserte data."""
    tittel = finn_data.get("tittel", "Ukjent eiendom")
    pris = finn_data.get("pris_tekst", "Ikke oppgitt")

    styrker: list[str] = []
    svakheter: list[str] = []

    # Styrker fra bildeanalyse
    if bilde_analyse and isinstance(bilde_analyse.get("bygningsanalyse"), dict):
        ba = bilde_analyse["bygningsanalyse"]
        tilstand = ba.get("generell_tilstand", "")
        if tilstand and "god" in tilstand.lower():
            styrker.append(f"Generell tilstand vurdert som: {tilstand}")
        elif tilstand and "renovering" in tilstand.lower():
            svakheter.append(f"Generell tilstand vurdert som: {tilstand}")

    if bilde_analyse and isinstance(
        bilde_analyse.get("plantegning_analyse"), dict
    ):
        pa = bilde_analyse["plantegning_analyse"]
        if pa.get("funnet_plantegning"):
            styrker.append("Plantegning tilgjengelig i annonsen")
        else:
            svakheter.append("Ingen plantegning funnet i annonsebildene")

    if not avviksrapport.get("funnet_avvik"):
        styrker.append("Ingen avvik funnet mellom annonsert informasjon og offentlige registre")

    for a in avviksrapport.get("avvik", []):
        svakheter.append(a["beskrivelse"])

    # Forbedringspotensial
    oppussing = "Lavt"
    if bilde_analyse and isinstance(bilde_analyse.get("forbedringspotensial"), list):
        antall = len(bilde_analyse["forbedringspotensial"])
        if antall >= 3:
            oppussing = "Stort"
        elif antall >= 1:
            oppussing = "Middels"

    risiko = avviksrapport.get("risiko_nivaa", "LAV")
    if risiko == "HØY":
        anbefaling = (
            "Høy risiko identifisert. Anbefaler grundig tilstandsrapport "
            "og juridisk gjennomgang før bud. Verifiser alle avvik med selger."
        )
    elif risiko == "MIDDELS":
        anbefaling = (
            "Noen avvik funnet. Anbefaler å undersøke disse nærmere ved visning "
            "og be selger om dokumentasjon."
        )
    else:
        anbefaling = (
            "Lavt risikonivå basert på tilgjengelig informasjon. "
            "Standard due diligence anbefales likevel."
        )

    oppsummering_tekst = ""
    if bilde_analyse and isinstance(bilde_analyse.get("oppsummering"), str):
        oppsummering_tekst = bilde_analyse["oppsummering"]

    return {
        "overskrift": tittel,
        "sammendrag": oppsummering_tekst or f"Bolig til {pris} kr – {tittel}",
        "styrker": styrker if styrker else ["Ikke nok data for å vurdere styrker"],
        "svakheter": svakheter if svakheter else ["Ingen åpenbare svakheter funnet"],
        "anbefaling_kjøper": anbefaling,
        "estimert_oppussingsbehov": oppussing,
    }


# ---------------------------------------------------------------------------
# Endepunkter
# ---------------------------------------------------------------------------


@router.post(
    "/analyser",
    summary="Komplett analyse av Finn.no boligannonse med AI-bildeanalyse og matrikkelsjekk",
    response_model=dict,
)
async def analyser_finn_annonse(
    finn_url: Annotated[
        str,
        Query(
            description=(
                "Finn.no-annonse URL, f.eks. "
                "https://www.finn.no/realestate/homes/ad.html?finnkode=123456789"
            )
        ),
    ],
    current_user: User = Depends(require_ai_access),
) -> dict:
    """
    Komplett analyse av en Finn.no boligannonse.

    Henter annonsedata, analyserer bilder med Claude Vision,
    slår opp matrikkeldata i Kartverket, og genererer avviksrapport.
    """
    # Valider URL
    if "finn.no" not in finn_url.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL må være en Finn.no-annonse",
        )

    # Steg 1: Hent annonsedata
    try:
        finn_data = await _hent_finn_annonse(finn_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Feil ved henting av Finn-annonse: {str(e)}",
        )

    # Steg 2 & 3: Parallelt – hent matrikkeldata og analyser bilder
    adresse = finn_data.get("adresse", "")
    kontekst = (
        f"Tittel: {finn_data.get('tittel', '')}\n"
        f"Adresse: {adresse}\n"
        f"Pris: {finn_data.get('pris_tekst', 'ukjent')} kr\n"
        f"Nøkkelinfo: {json.dumps(finn_data.get('nøkkelinfo', {}), ensure_ascii=False)}"
    )

    matrikkel_task = _hent_matrikkeldata_fra_adresse(adresse)
    bilde_task = (
        _analyser_bilder_med_claude(finn_data["bilde_urls"], kontekst)
        if finn_data.get("bilde_urls")
        else asyncio.coroutine(lambda: {"feil": "Ingen bilder funnet i annonsen"})()
    )

    try:
        matrikkel_data, bilde_analyse = await asyncio.gather(
            matrikkel_task, bilde_task, return_exceptions=True
        )
    except Exception:
        matrikkel_data = None
        bilde_analyse = None

    # Håndter exceptions fra gather
    if isinstance(matrikkel_data, Exception):
        matrikkel_data = None
    if isinstance(bilde_analyse, Exception):
        bilde_analyse = {"feil": f"Bildeanalyse feilet: {str(bilde_analyse)}"}

    # Steg 4: Generer avviksrapport
    avviksrapport = _generer_avviksrapport(finn_data, matrikkel_data, bilde_analyse)

    # Steg 5: Generer eiendomsoppsummering
    oppsummering = _generer_eiendomsoppsummering(
        finn_data, matrikkel_data, bilde_analyse, avviksrapport
    )

    # Kartverket-lenke
    kartverket_lenke = ""
    if matrikkel_data:
        kartverket_lenke = matrikkel_data.get(
            "seeiendom_url",
            f"https://seeiendom.kartverket.no/eiendom/"
            f"{matrikkel_data.get('knr', '')}/{matrikkel_data.get('gnr', '')}/"
            f"{matrikkel_data.get('bnr', '')}",
        )

    return {
        "finn_data": {
            "finn_url": finn_data["finn_url"],
            "finnkode": finn_data["finnkode"],
            "tittel": finn_data["tittel"],
            "adresse": finn_data["adresse"],
            "pris": finn_data["pris_tekst"],
            "antall_bilder": finn_data["antall_bilder"],
            "nøkkelinfo": finn_data["nøkkelinfo"],
        },
        "matrikkel_data": matrikkel_data,
        "bilde_analyse": bilde_analyse,
        "avviksrapport": avviksrapport,
        "eiendomsoppsummering": oppsummering,
        "kartverket_lenke": kartverket_lenke,
        "disclaimer": (
            "Denne analysen er automatisk generert beslutningsstøtte og erstatter "
            "ikke profesjonell tilstandsrapport, takst eller juridisk rådgivning. "
            "Data fra Finn.no er hentet via web scraping og kan være ufullstendig. "
            "Matrikkeldata kan ha forsinkelser. Verifiser alltid informasjon "
            "med offisielle kilder og fagpersoner."
        ),
    }


@router.get(
    "/sjekk-annonse",
    summary="Hent og strukturer Finn.no-annonsedata (uten AI-analyse)",
    response_model=dict,
)
async def sjekk_finn_annonse(
    finn_url: Annotated[
        str,
        Query(
            description=(
                "Finn.no-annonse URL, f.eks. "
                "https://www.finn.no/realestate/homes/ad.html?finnkode=123456789"
            )
        ),
    ],
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Enkel henting og strukturering av Finn.no-annonsedata.

    Returnerer parsed data fra annonsen uten AI-analyse eller matrikkelsjekk.
    Grunnfunksjon tilgjengelig for alle innloggede brukere.
    """
    if "finn.no" not in finn_url.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL må være en Finn.no-annonse",
        )

    try:
        finn_data = await _hent_finn_annonse(finn_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Feil ved henting av Finn-annonse: {str(e)}",
        )

    return finn_data
