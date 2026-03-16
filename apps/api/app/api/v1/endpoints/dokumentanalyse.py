"""
ByggSjekk – Dokumentanalyse og Godkjente Tegninger.

Inspirert av Findable.ai og Prosper-AI.no:
1. Henter godkjente byggetegninger fra eByggesak (gratis – erstatter Norkart/Ambita)
2. AI-klassifisering av bygningsdokumenter
3. Risikovurdering fra offentlige registre
4. Compliance gap-analyse
5. Salgsoppgave-analyse

POST /dokumentanalyse/eiendom – Komplett dokumentanalyse
GET  /dokumentanalyse/tegninger – Godkjente tegninger (gratis)
POST /dokumentanalyse/salgsoppgave – Analyser salgsoppgave-PDF
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.core.deps import get_current_user, require_ai_access
from app.models.user import User

router = APIRouter()

# Legg til services-stien (fungerer bade lokalt og i Docker)
for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Godkjente tegninger (gratis – erstatter Norkart/Ambita)
# ---------------------------------------------------------------------------

@router.get(
    "/tegninger",
    summary="Hent godkjente byggetegninger (gratis – erstatter Norkart/Ambita)",
    response_model=dict,
)
async def hent_godkjente_tegninger(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Henter sist godkjente byggetegninger fra kommunalt arkiv (eByggesak).

    I motsetning til Norkart/Ambita som tar betalt for dette, tilbyr NOPS
    dette gratis til alle brukere.

    Returnerer:
    - Liste over alle byggesaker med tilhørende dokumenter/tegninger
    - Lenker til sist godkjente tegninger (plan, fasade, snitt)
    - Status per tegningstype (godkjent/midlertidig/mangler)
    """
    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter

        adapter = get_kartverket_adapter()
        kr = await adapter.full_oppslag(knr, gnr, bnr, 0, 0)

        if isinstance(kr, Exception):
            raise HTTPException(status_code=502, detail="Kunne ikke hente eiendomsdata")

        # Ekstraher byggesaker og tilhørende dokumenter
        tegninger: list[dict] = []
        byggesaker: list[dict] = []

        for sak in (kr.byggesaker or []):
            saksdata = {
                "saksnummer": getattr(sak, "saksnummer", None),
                "tittel": getattr(sak, "tittel", None) or getattr(sak, "beskrivelse", None) or getattr(sak, "sakstype", "Ukjent sak"),
                "status": getattr(sak, "status", None),
                "vedtaksdato": getattr(sak, "vedtaksdato", None),
                "sakstype": getattr(sak, "sakstype", None),
            }
            byggesaker.append(saksdata)

            # Sjekk om saken har tilknyttede dokumenter
            docs = getattr(sak, "dokumenter", None) or []
            for doc in docs:
                doc_tittel = getattr(doc, "tittel", "") or ""
                doc_url = getattr(doc, "url", None) or getattr(doc, "lenke", None)
                doc_type = _klassifiser_tegning(doc_tittel)

                tegninger.append({
                    "tittel": doc_tittel,
                    "type": doc_type,
                    "url": doc_url,
                    "saksnummer": saksdata["saksnummer"],
                    "vedtaksdato": saksdata["vedtaksdato"],
                    "status": saksdata["status"],
                })

        # Bestem hvilke tegningstyper som finnes/mangler
        funnet_typer = {t["type"] for t in tegninger if t["type"] != "annet"}
        forventede = {"plantegning", "fasadetegning", "snitt-tegning", "situasjonsplan"}
        mangler = forventede - funnet_typer

        # Eiendomsinfo
        eiendom_info = {}
        if kr.eiendom:
            eiendom_info = {
                "adresse": kr.eiendom.adresse,
                "areal_m2": kr.eiendom.areal_m2,
                "kommunenavn": kr.kommune.kommunenavn if kr.kommune else knr,
            }

        return {
            "eiendom": {
                "knr": knr,
                "gnr": gnr,
                "bnr": bnr,
                **eiendom_info,
            },
            "antall_byggesaker": len(byggesaker),
            "byggesaker": byggesaker,
            "tegninger": tegninger,
            "tegningstyper_funnet": sorted(funnet_typer),
            "tegningstyper_mangler": sorted(mangler),
            "se_eiendom_url": f"https://seeiendom.kartverket.no/?kommunenr={knr}&gnr={gnr}&bnr={bnr}",
            "notat": (
                "Tegninger hentes fra kommunalt eByggesak-arkiv. "
                "Tilgjengeligheten varierer per kommune. "
                "NOPS tilbyr denne tjenesten gratis – i motsetning til Norkart/Ambita."
            ),
        }

    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Kartverket-modul ikke tilgjengelig: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tegningshenting feilet: {exc}")


def _klassifiser_tegning(tittel: str) -> str:
    """Klassifiserer en tegning basert på tittel."""
    tittel_lower = tittel.lower()
    if any(w in tittel_lower for w in ["plan", "etasje", "kjeller", "loft", "grunnplan"]):
        return "plantegning"
    if any(w in tittel_lower for w in ["fasade", "oppriss"]):
        return "fasadetegning"
    if any(w in tittel_lower for w in ["snitt", "tverrsnitt", "langsnitt"]):
        return "snitt-tegning"
    if any(w in tittel_lower for w in ["situasjon", "site", "tomt"]):
        return "situasjonsplan"
    if any(w in tittel_lower for w in ["brann", "rømning"]):
        return "branntegning"
    if any(w in tittel_lower for w in ["detalj"]):
        return "detaljtegning"
    return "annet"


# ---------------------------------------------------------------------------
# Komplett eiendoms-dokumentanalyse (Findable + Prosper-inspirert)
# ---------------------------------------------------------------------------

@router.post(
    "/eiendom",
    summary="Komplett dokumentanalyse – risikovurdering og compliance (Findable/Prosper)",
    response_model=dict,
)
async def dokumentanalyse_eiendom(
    knr: Annotated[str, Query(description="Kommunenummer")],
    gnr: Annotated[int, Query(description="Gårdsnummer")],
    bnr: Annotated[int, Query(description="Bruksnummer")],
    current_user: User = Depends(require_ai_access),
) -> dict:
    """
    Komplett dokumentanalyse av en eiendom (inspirert av Findable.ai og Prosper-AI):

    1. Henter all tilgjengelig dokumentasjon fra offentlige registre
    2. Klassifiserer dokumenter etter type og relevans
    3. Identifiserer compliance-gap (manglende dokumenter)
    4. Risikovurdering basert på dokumentasjonsstatus
    5. Anbefalinger for kjøper/selger/arkitekt
    """
    try:
        from services.municipality_connectors.kartverket import get_kartverket_adapter
        from services.municipality_connectors.arealplaner import (
            get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
            EiendomsoppslagResult,
        )
        import anthropic

        # Hent all data parallelt
        kartverket = get_kartverket_adapter()

        if knr == "3212":
            from services.municipality_connectors.arealplaner import get_nesodden_adapter
            arealplaner_task = get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, None, None)
        else:
            async def _arealplaner():
                dok = get_dok_adapter()
                plan = get_arealplaner_adapter()
                dok_r, plan_r = await asyncio.gather(
                    dok.analyse_eiendom(knr, gnr, bnr, None, None),
                    plan.hent_planrapport(knr, gnr, bnr, None, None),
                    return_exceptions=True,
                )
                r = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
                if not isinstance(dok_r, Exception):
                    r.dok_analyse = dok_r
                if not isinstance(plan_r, Exception):
                    r.planrapport = plan_r
                return r
            arealplaner_task = _arealplaner()

        kr, arealdata = await asyncio.gather(
            kartverket.full_oppslag(knr, gnr, bnr, 0, 0),
            arealplaner_task,
            return_exceptions=True,
        )

        # Bygg kontekst for AI
        eiendom_kontekst = f"Eiendom: Gnr. {gnr}, Bnr. {bnr}, Kommune {knr}\n"

        byggesaker_tekst = "Ingen byggesaker funnet."
        har_ferdigattest = False
        antall_saker = 0

        if not isinstance(kr, Exception):
            if kr.eiendom:
                eiendom_kontekst += f"Adresse: {kr.eiendom.adresse}\n"
                eiendom_kontekst += f"Areal: {kr.eiendom.areal_m2} m²\n" if kr.eiendom.areal_m2 else ""
            if kr.bygninger:
                b0 = kr.bygninger[0]
                eiendom_kontekst += f"Bygningstype: {b0.bygningstype}, Byggeår: {b0.byggeaar}, BRA: {b0.bruksareal} m²\n"
            if kr.byggesaker:
                antall_saker = len(kr.byggesaker)
                saker_lines = []
                for s in kr.byggesaker[:10]:
                    tittel = getattr(s, "tittel", None) or getattr(s, "beskrivelse", None) or getattr(s, "sakstype", "Ukjent")
                    st = getattr(s, "status", "?")
                    dato = getattr(s, "vedtaksdato", "?")
                    saker_lines.append(f"- {tittel}: Status={st}, Dato={dato}")
                    if "ferdigattest" in st.lower() if st else False:
                        har_ferdigattest = True
                byggesaker_tekst = "\n".join(saker_lines)

        plan_tekst = "Ingen plandata."
        if not isinstance(arealdata, Exception):
            pr = getattr(arealdata, "planrapport", None)
            if pr and hasattr(pr, "gjeldende_planer") and pr.gjeldende_planer:
                plan_tekst = "\n".join(
                    f"- {p.plan_navn}: {p.arealformål}" for p in pr.gjeldende_planer[:3]
                )

        # AI-analyse
        prompt = f"""Du er en norsk eiendomsdokument-ekspert (inspirert av Findable.ai og Prosper-AI).
Analyser dokumentasjonsstatus for denne eiendommen og gi en komplett risikovurdering.

{eiendom_kontekst}

## Byggesaker ({antall_saker} stk)
{byggesaker_tekst}

## Reguleringsplan
{plan_tekst}

## Ferdigattest
{"Ja, ferdigattest funnet" if har_ferdigattest else "Ingen ferdigattest funnet i registrerte saker"}

Svar BARE med gyldig JSON:
{{
  "dokumentstatus": {{
    "ferdigattest": {{"status": "Godkjent/Mangler/Ukjent", "kommentar": "..."}},
    "byggetillatelse": {{"status": "Godkjent/Mangler/Ukjent", "kommentar": "..."}},
    "reguleringsplan": {{"status": "Gjeldende/Utgått/Ukjent", "kommentar": "..."}},
    "situasjonsplan": {{"status": "Tilgjengelig/Mangler/Ukjent", "kommentar": "..."}},
    "plantegninger": {{"status": "Tilgjengelig/Mangler/Ukjent", "kommentar": "..."}},
    "energiattest": {{"status": "Tilgjengelig/Mangler/Ukjent", "kommentar": "..."}},
    "tilstandsrapport": {{"status": "Anbefalt/Ikke funnet", "kommentar": "..."}}
  }},
  "compliance_gap": [
    {{
      "dokument": "Dokumenttype som mangler",
      "alvorlighet": "Kritisk/Viktig/Anbefalt",
      "konsekvens": "Hva manglende dokument betyr",
      "handling": "Hva eier bør gjøre"
    }}
  ],
  "risiko_vurdering": {{
    "nivaa": "LAV/MIDDELS/HØY",
    "score": 0.0,
    "hovedrisiko": ["Risiko 1", "Risiko 2"],
    "sammendrag": "2-3 setningers risikosammendrag"
  }},
  "anbefalinger": {{
    "kjøper": ["Anbefaling for kjøper 1", "Anbefaling 2"],
    "selger": ["Anbefaling for selger 1"],
    "arkitekt": ["Anbefaling for arkitekt 1"]
  }},
  "transaksjonsvurdering": {{
    "egnet_for_salg": true,
    "klargjøring_nødvendig": ["Hva som bør ordnes før salg"],
    "estimert_tid_klargjøring": "2-4 uker"
  }},
  "disclaimer": "Denne analysen er beslutningsstøtte basert på offentlig tilgjengelig data..."
}}"""

        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
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
            "eiendom": {"knr": knr, "gnr": gnr, "bnr": bnr},
            "antall_byggesaker": antall_saker,
            "har_ferdigattest": har_ferdigattest,
            **analyse,
        }

    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Modul ikke tilgjengelig: {exc}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI-svar feilet: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dokumentanalyse feilet: {exc}")


# ---------------------------------------------------------------------------
# Salgsoppgave-analyse (Prosper-AI-inspirert)
# ---------------------------------------------------------------------------

@router.post(
    "/salgsoppgave",
    summary="Analyser salgsoppgave-PDF med AI (Prosper-AI-inspirert)",
    response_model=dict,
)
async def analyser_salgsoppgave(
    fil: Annotated[UploadFile, File(description="Salgsoppgave PDF")],
    knr: Annotated[str, Form()] = "",
    gnr: Annotated[int, Form()] = 0,
    bnr: Annotated[int, Form()] = 0,
    current_user: User = Depends(require_ai_access),
) -> dict:
    """
    Analyserer en salgsoppgave-PDF og ekstraherer:
    - Nøkkeldata (pris, areal, eierform, fellesgjeld)
    - Risikopunkter
    - Avvik mot offentlige registre
    - Kjøperanbefalinger
    """
    if not fil.content_type or "pdf" not in fil.content_type.lower():
        # Aksepter også bilder av salgsoppgaver
        if fil.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=400, detail="Kun PDF eller bilde støttes")

    innhold = await fil.read()
    if len(innhold) > 20_000_000:
        raise HTTPException(status_code=413, detail="Maks 20 MB")

    try:
        import anthropic

        # For bilder: send direkte til Claude Vision
        # For PDF: ekstraher tekst eller send som bilde
        content_blocks = []

        if fil.content_type and "pdf" in fil.content_type.lower():
            # PDF: Konverter til base64 og send som dokument
            b64 = base64.standard_b64encode(innhold).decode()
            content_blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64,
                },
            })
        else:
            # Bilde: send som image
            b64 = base64.standard_b64encode(innhold).decode()
            media_type = fil.content_type or "image/jpeg"
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            })

        content_blocks.append({
            "type": "text",
            "text": """Analyser denne norske salgsoppgaven og ekstraher all relevant informasjon.

Svar BARE med gyldig JSON:
{
  "eiendom": {
    "adresse": "",
    "matrikkel": "Gnr/Bnr",
    "kommune": "",
    "eierform": "Selveier/Borettslag/Aksjeleilighet",
    "boligtype": "Enebolig/Leilighet/Rekkehus/etc"
  },
  "økonomi": {
    "prisantydning": 0,
    "fellesgjeld": 0,
    "totalpris": 0,
    "felleskostnader_mnd": 0,
    "kommunale_avgifter_aar": 0,
    "formuesverdi": 0
  },
  "areal": {
    "primærrom_p_rom": 0,
    "bruksareal_bra": 0,
    "tomteareal": 0,
    "antall_soverom": 0,
    "antall_bad": 0,
    "etasje": ""
  },
  "bygning": {
    "byggeår": 0,
    "renovert": "",
    "energimerke": "",
    "oppvarming": "",
    "konstruksjon": ""
  },
  "juridisk": {
    "reguleringsplan": "",
    "servitutter": [""],
    "heftelser": [""],
    "ferdigattest": "Ja/Nei/Ukjent",
    "tilstandsrapport_dato": "",
    "eierskifteforsikring": "Ja/Nei"
  },
  "risikopunkter": [
    {
      "type": "Juridisk/Teknisk/Økonomisk",
      "beskrivelse": "Hva som er risikabelt",
      "alvorlighet": "Lav/Middels/Høy",
      "anbefaling": "Hva kjøper bør gjøre"
    }
  ],
  "styrker": ["Styrke 1", "Styrke 2"],
  "svakheter": ["Svakhet 1"],
  "kjøperanbefaling": "Samlet vurdering og anbefaling for kjøper (3-5 setninger)",
  "sammendrag": "Kort sammendrag av eiendommen (2-3 setninger)"
}""",
        })

        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": content_blocks}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        return {
            "analyse": json.loads(text),
            "kilde_fil": fil.filename,
            "disclaimer": (
                "Denne analysen er automatisk generert fra salgsoppgaven. "
                "Verifiser alltid mot originaldokumentet og offentlige registre."
            ),
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="AI-modul ikke tilgjengelig")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Kunne ikke tolke salgsoppgaven: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Salgsoppgave-analyse feilet: {exc}")
