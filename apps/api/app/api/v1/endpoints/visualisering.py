"""
ByggSjekk – Visualisering og 3D-konvertering.

Tjeneste for å:
1. Analysere arkitektbilder, skisser og plantegninger med Claude Vision
2. Generere fotorealistiske renders av bygg og rom
3. Gi anbefalinger om stil, materialer og utforming

Bruker:
- Anthropic Claude claude-sonnet-4-6 for bildeanalyse
- Replicate / Stable Diffusion XL for render-generering (krever REPLICATE_API_KEY)
"""

from __future__ import annotations

import base64
import json
import os
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

TILLATTE_FORMATER = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAKS_FILSTØRRELSE = 10 * 1024 * 1024  # 10 MB

STILALTERNATIVER = {
    "nordisk": "Nordic minimalist architecture, clean lines, light wood, white walls, Scandinavian design",
    "moderne": "Modern contemporary architecture, flat roof, large windows, clean geometric forms, concrete and glass",
    "klassisk": "Classical Norwegian architecture, pitched roof, traditional wooden facade, warm colors",
    "industriell": "Industrial style, exposed brick, steel beams, large factory windows, raw materials",
    "naturlig": "Organic natural architecture, earth tones, timber frame, blending with nature, sustainable materials",
}


@router.post(
    "/analyser-bilde",
    summary="Analyser arkitektbilde med AI",
    response_model=dict,
)
async def analyser_bilde(
    fil: Annotated[UploadFile, File(description="Bilde av bygg, skisse eller plantegning (JPEG/PNG/WebP)")],
    bildetype: Annotated[
        str,
        Form(description="Bildetypen: 'foto' | 'plantegning' | 'skisse' | 'fasade' | 'finn_annonse'"),
    ] = "foto",
    ønsket_endring: Annotated[
        str,
        Form(description="Beskriv hva du ønsker å endre eller visualisere"),
    ] = "",
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Analyserer et bilde av et bygg, en skisse eller plantegning med Claude Vision.

    Returnerer:
    - Arkitektonisk analyse (bygningstype, stil, materialer, tilstand)
    - Identifiserte muligheter for endring/tilbygg
    - Konkrete anbefalinger for videre arbeid
    - Grunnlag for render-generering
    """
    # Valider filtype og størrelse
    if fil.content_type not in TILLATTE_FORMATER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filformat ikke støttet. Tillatte: JPEG, PNG, WebP. Fikk: {fil.content_type}",
        )

    innhold = await fil.read()
    if len(innhold) > MAKS_FILSTØRRELSE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Filen er for stor. Maks 10 MB. Fikk: {len(innhold) / 1024 / 1024:.1f} MB",
        )

    # Konverter til base64 for Claude
    b64 = base64.standard_b64encode(innhold).decode()
    media_type = fil.content_type or "image/jpeg"

    # Bygg analyse-prompt basert på bildetype
    bildetype_kontekst = {
        "foto": "et fotografi av et bygg eller rom",
        "plantegning": "en arkitektonisk plantegning",
        "skisse": "en håndtegnet skisse av et bygg eller tiltak",
        "fasade": "en fasadetegning av et bygg",
        "finn_annonse": "et boligfoto fra en eiendomsannonse",
    }.get(bildetype, "et arkitektonisk bilde")

    ønsket_tekst = f"\n\nBrukerens ønske: {ønsket_endring}" if ønsket_endring else ""

    user_prompt = f"""Analyser dette {bildetype_kontekst} og gi en detaljert arkitektonisk vurdering.{ønsket_tekst}

Svar BARE med gyldig JSON i dette formatet:
{{
  "bygningstype": "Enebolig / Tomannsbolig / etc.",
  "arkitekturstil": "Nordisk / Moderne / Klassisk etc.",
  "byggeaar_estimat": "Ca. 1970-tall",
  "materialer": ["Tre", "Teglstein", "Betong"],
  "tilstand": "God / Moderat / Bør renoveres",
  "fasade_beskrivelse": "Kort beskrivelse av fasaden",
  "muligheter": [
    {{
      "type": "Tilbygg / Fasadeoppgradering / etc.",
      "beskrivelse": "Konkret beskrivelse av muligheten",
      "kompleksitet": "Lav / Middels / Høy",
      "estimert_kostnad": "200 000 – 400 000 kr"
    }}
  ],
  "anbefalinger": [
    "Konkret anbefaling 1",
    "Konkret anbefaling 2"
  ],
  "render_prompt": "English prompt for Stable Diffusion to generate a photorealistic render of this building with improvements",
  "arkitektoniske_styrker": ["Styrke 1", "Styrke 2"],
  "arkitektoniske_utfordringer": ["Utfordring 1"]
}}"""

    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.AsyncAnthropic(api_key=api_key)

        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": user_prompt,
                        },
                    ],
                }
            ],
        )

        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()

        analyse = json.loads(text)

        return {
            "bildetype": bildetype,
            "analyse": analyse,
            "ønsket_endring": ønsket_endring,
            "render_klar": bool(analyse.get("render_prompt")),
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="AI-bildemodul ikke tilgjengelig")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI-svar kunne ikke tolkes: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bildeanalyse feilet: {exc}")


@router.post(
    "/generer-render",
    summary="Generer fotorealistisk render av bygg",
    response_model=dict,
)
async def generer_render(
    stil: Annotated[str, Form(description="Arkitekturstil: nordisk|moderne|klassisk|industriell|naturlig")] = "nordisk",
    beskrivelse: Annotated[str, Form(description="Beskriv bygget eller endringen du vil visualisere")] = "",
    rom_type: Annotated[str, Form(description="Romtype ved interiørrender: stue|kjøkken|soverom|bad|utendørs")] = "utendørs",
    referanse_bilde: Annotated[Optional[UploadFile], File(description="Referansebilde (valgfritt)")] = None,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Genererer en fotorealistisk arkitekturender basert på stil og beskrivelse.

    Støtter to render-backends (i prioritert rekkefølge):
    1. fal.ai – Flux / Nanobanana (sett FAL_KEY)
    2. Replicate – SDXL (sett REPLICATE_API_KEY)
    """
    fal_key = os.environ.get("FAL_KEY", "")
    replicate_key = os.environ.get("REPLICATE_API_KEY", "")

    stilbeskrivelse = STILALTERNATIVER.get(stil, STILALTERNATIVER["nordisk"])
    rom_kontekst = {
        "stue": "living room interior, cozy, natural light",
        "kjøkken": "kitchen interior, functional, modern appliances",
        "soverom": "bedroom interior, calm, relaxing atmosphere",
        "bad": "bathroom interior, clean, spa-like",
        "utendørs": "exterior view, garden, natural surroundings",
    }.get(rom_type, "exterior view")

    full_prompt = (
        f"{beskrivelse}, {stilbeskrivelse}, {rom_kontekst}, "
        f"architectural photography, high quality, 8K, photorealistic, "
        f"professional architectural render, natural lighting"
    )
    negative_prompt = (
        "ugly, blurry, distorted, unrealistic, cartoon, sketch, low quality, "
        "watermark, text, people, cars, oversaturated"
    )

    if not fal_key and not replicate_key:
        return {
            "status": "demo",
            "melding": (
                "Render-generering er ikke aktivert. "
                "Legg til FAL_KEY (fal.ai) eller REPLICATE_API_KEY i .env for å aktivere."
            ),
            "prompt": full_prompt,
            "stil": stil,
            "forhåndsvisning_url": None,
        }

    # ── fal.ai backend (primær) ─────────────────────────────
    if fal_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as http:
                # Bruk fal.ai Flux Schnell (rask) eller Nanobanana
                submit_resp = await http.post(
                    "https://queue.fal.run/fal-ai/flux/schnell",
                    headers={
                        "Authorization": f"Key {fal_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": full_prompt,
                        "image_size": "landscape_16_9",
                        "num_inference_steps": 4,
                        "num_images": 1,
                        "enable_safety_checker": True,
                    },
                )
                if submit_resp.status_code == 200:
                    result = submit_resp.json()
                    images = result.get("images", [])
                    bilde_url = images[0].get("url") if images else None
                    return {
                        "status": "suksess",
                        "bilde_url": bilde_url,
                        "prompt": full_prompt,
                        "stil": stil,
                        "motor": "fal.ai/flux-schnell",
                    }

                # Asynkron kø-modus (202)
                if submit_resp.status_code == 202:
                    queue_data = submit_resp.json()
                    request_id = queue_data.get("request_id", "")
                    status_url = queue_data.get("status_url", "")
                    response_url = queue_data.get("response_url", "")

                    if not response_url and request_id:
                        response_url = f"https://queue.fal.run/fal-ai/flux/schnell/requests/{request_id}"

                    if response_url:
                        import asyncio
                        for _ in range(30):
                            await asyncio.sleep(2)
                            poll = await http.get(
                                response_url,
                                headers={"Authorization": f"Key {fal_key}"},
                            )
                            if poll.status_code == 200:
                                result = poll.json()
                                images = result.get("images", [])
                                bilde_url = images[0].get("url") if images else None
                                return {
                                    "status": "suksess",
                                    "bilde_url": bilde_url,
                                    "prompt": full_prompt,
                                    "stil": stil,
                                    "motor": "fal.ai/flux-schnell",
                                }
                            elif poll.status_code != 202:
                                break

                # Fallthrough til Replicate hvis fal.ai feilet
                if not replicate_key:
                    raise HTTPException(status_code=502, detail=f"fal.ai render feilet: HTTP {submit_resp.status_code}")

        except HTTPException:
            raise
        except Exception:
            if not replicate_key:
                raise

    # ── Replicate backend (fallback) ────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=120) as http:
            create_resp = await http.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {replicate_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    "input": {
                        "prompt": full_prompt,
                        "negative_prompt": negative_prompt,
                        "width": 1024,
                        "height": 768,
                        "num_inference_steps": 30,
                        "guidance_scale": 7.5,
                    },
                },
            )
            prediction = create_resp.json()
            prediction_id = prediction.get("id")
            if not prediction_id:
                raise HTTPException(status_code=502, detail="Replicate API feilet")

            import asyncio
            for _ in range(30):
                await asyncio.sleep(2)
                poll_resp = await http.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {replicate_key}"},
                )
                status_data = poll_resp.json()
                if status_data.get("status") == "succeeded":
                    output = status_data.get("output", [])
                    bilde_url = output[0] if output else None
                    return {
                        "status": "suksess",
                        "bilde_url": bilde_url,
                        "prompt": full_prompt,
                        "stil": stil,
                        "motor": "replicate/sdxl",
                        "prediction_id": prediction_id,
                    }
                elif status_data.get("status") == "failed":
                    raise HTTPException(status_code=502, detail="Render-generering feilet")

            raise HTTPException(status_code=504, detail="Render tok for lang tid")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Render-generering feilet: {exc}")


@router.post(
    "/virtuell-staging",
    summary="Virtuell staging – tomt rom til møblert rom (Chaos Vera-inspirert)",
    response_model=dict,
)
async def virtuell_staging(
    rom_bilde: Annotated[UploadFile, File(description="Bilde av tomt rom (JPEG/PNG)")],
    romtype: Annotated[str, Form(description="stue|soverom|kjøkken|bad|kontor")] = "stue",
    stil: Annotated[str, Form(description="nordisk|moderne|klassisk|industriell|japandi")] = "nordisk",
    budsjett: Annotated[str, Form(description="lavt|middels|høyt")] = "middels",
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Analyserer et tomt rom og genererer:
    1. Møbelplasseringsplan (AI-generert)
    2. Materialanbefalinger
    3. Fargepalette
    4. Render-prompt for Stable Diffusion
    5. Produktanbefalinger

    Bruker Claude Vision for romanalyse + Replicate SDXL for staging-render.
    """
    if rom_bilde.content_type not in TILLATTE_FORMATER:
        raise HTTPException(status_code=400, detail="Kun JPEG/PNG/WebP støttes")

    innhold = await rom_bilde.read()
    if len(innhold) > MAKS_FILSTØRRELSE:
        raise HTTPException(status_code=413, detail="Maks 10 MB")

    b64 = base64.standard_b64encode(innhold).decode()
    media_type = rom_bilde.content_type or "image/jpeg"

    stil_map = {
        "nordisk": "Scandinavian minimalist, light wood, white walls, linen textiles, natural light",
        "moderne": "modern contemporary, clean lines, neutral palette, statement furniture",
        "klassisk": "classic Norwegian, warm tones, traditional details, quality materials",
        "industriell": "industrial loft, exposed brick, metal accents, dark palette",
        "japandi": "Japandi style, wabi-sabi, natural materials, zen minimalism, muted earth tones",
    }
    budsjett_map = {
        "lavt": "under 50 000 kr – IKEA og Jysk-løsninger, smart shopping",
        "middels": "50 000–150 000 kr – god kvalitet, mix av IKEA og norske møbelkjeder",
        "høyt": "over 150 000 kr – premium skandinaviske merkevarer, Bolia, Eilersen, HAY",
    }

    prompt = f"""Analyser dette tomme rommet og lag en komplett møblerings- og stagingplan.

Stil: {stil} ({stil_map.get(stil, '')})
Budsjett: {budsjett} ({budsjett_map.get(budsjett, '')})
Romtype: {romtype}

Svar BARE med gyldig JSON:
{{
  "rombeskrivelse": "Kort beskrivelse av rommet (mål estimert, vinduer, lys, byggeår-stil)",
  "møbelplan": "Detaljert norsk tekst om hvordan møblere rommet optimalt",
  "fargepalette": [
    {{"navn": "Farge", "hex": "#FFFFFF", "bruk": "Vegger/Gulv/Tekstiler"}}
  ],
  "materialer": [
    {{"type": "Gulv/Vegger/Tak/Tekstiler", "anbefaling": "Produkt", "grunn": "Hvorfor", "estimert_pris": "kr per m²"}}
  ],
  "produktliste": [
    {{"produkt": "Produktnavn", "type": "Sofa/Bord/Lampe etc", "butikk": "IKEA/Bolia/etc", "estimert_pris": 5000, "prioritet": "Må ha/Bør ha/Nice to have"}}
  ],
  "belysningsplan": "Plan for belysning: tak, gulv, accent",
  "staging_render_prompt": "English Stable Diffusion prompt for photorealistic interior render of this room staged in the chosen style, 8K, interior photography",
  "budsjett_fordeling": [
    {{"kategori": "Møbler", "prosent": 50, "estimat_kr": 25000}}
  ],
  "tips": ["Konkret tip 1", "Konkret tip 2", "Konkret tip 3"]
}}"""

    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.AsyncAnthropic(api_key=api_key)

        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        staging = json.loads(text)

        # Generer staging-render via fal.ai eller Replicate
        render_url = None
        fal_key = os.environ.get("FAL_KEY", "")
        replicate_key = os.environ.get("REPLICATE_API_KEY", "")

        if staging.get("staging_render_prompt") and (fal_key or replicate_key):
            try:
                import httpx
                import asyncio
                render_prompt = staging["staging_render_prompt"]

                if fal_key:
                    # fal.ai Flux Schnell – rask rendering
                    async with httpx.AsyncClient(timeout=90) as http:
                        resp = await http.post(
                            "https://queue.fal.run/fal-ai/flux/schnell",
                            headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"},
                            json={
                                "prompt": render_prompt,
                                "image_size": "landscape_16_9",
                                "num_inference_steps": 4,
                                "num_images": 1,
                            },
                        )
                        if resp.status_code == 200:
                            images = resp.json().get("images", [])
                            render_url = images[0].get("url") if images else None
                        elif resp.status_code == 202:
                            q = resp.json()
                            resp_url = q.get("response_url") or f"https://queue.fal.run/fal-ai/flux/schnell/requests/{q.get('request_id', '')}"
                            for _ in range(20):
                                await asyncio.sleep(2)
                                poll = await http.get(resp_url, headers={"Authorization": f"Key {fal_key}"})
                                if poll.status_code == 200:
                                    images = poll.json().get("images", [])
                                    render_url = images[0].get("url") if images else None
                                    break

                elif replicate_key:
                    # Replicate SDXL fallback
                    async with httpx.AsyncClient(timeout=90) as http:
                        resp = await http.post(
                            "https://api.replicate.com/v1/predictions",
                            headers={"Authorization": f"Token {replicate_key}", "Content-Type": "application/json"},
                            json={
                                "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                                "input": {
                                    "prompt": render_prompt,
                                    "negative_prompt": "empty room, ugly, blurry, distorted, watermark",
                                    "width": 1024, "height": 768, "num_inference_steps": 25,
                                },
                            },
                        )
                        pred_id = resp.json().get("id")
                        if pred_id:
                            for _ in range(20):
                                await asyncio.sleep(3)
                                poll = await http.get(
                                    f"https://api.replicate.com/v1/predictions/{pred_id}",
                                    headers={"Authorization": f"Token {replicate_key}"},
                                )
                                pd = poll.json()
                                if pd.get("status") == "succeeded":
                                    out = pd.get("output", [])
                                    render_url = out[0] if out else None
                                    break
                                elif pd.get("status") == "failed":
                                    break
            except Exception:
                pass  # Render er bonus – ikke blokkerende

        return {
            "romtype": romtype,
            "stil": stil,
            "budsjett": budsjett,
            "staging": staging,
            "render_url": render_url,
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="AI-modul ikke tilgjengelig")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"AI-svar feilet: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Staging feilet: {e}")


@router.post(
    "/analyser-rom",
    summary="AI Romplanlegger – stil, materialer og møbelplan",
    response_model=dict,
)
async def analyser_rom(
    romtype: Annotated[str, Form(description="stue|kjøkken|soverom|bad|kontor|barnerom|terrasse")] = "stue",
    størrelse: Annotated[str, Form(description="small|medium|large")] = "medium",
    stil: Annotated[str, Form(description="nordisk|moderne|industriell|klassisk|japandi|boho")] = "nordisk",
    budsjett: Annotated[str, Form(description="50k|50-150k|150-300k|300k+")] = "50-150k",
    ønsker: Annotated[str, Form(description="Spesielle ønsker og krav")] = "",
    current_user: User = Depends(get_current_user),
) -> dict:
    """AI-basert romplanlegger med fargepalette, materialer, møbelplan og produktanbefalinger."""
    størrelse_map = {"small": "lite rom under 20 m²", "medium": "middels rom 20–40 m²", "large": "stort rom over 40 m²"}
    budsjett_map = {"50k": "under 50 000 kr (IKEA/budsjett)", "50-150k": "50 000–150 000 kr (god kvalitet)", "150-300k": "150 000–300 000 kr (premium)", "300k+": "over 300 000 kr (luksus)"}

    prompt = f"""Du er en norsk interiørarkitekt. Lag en komplett romplanleggingsplan.

Romtype: {romtype}
Størrelse: {størrelse_map.get(størrelse, størrelse)}
Ønsket stil: {stil}
Budsjett: {budsjett_map.get(budsjett, budsjett)}
Spesielle ønsker: {ønsker or 'Ingen'}

Svar BARE med gyldig JSON:
{{
  "planleggingsforslag": "Detaljert norsk tekst om layout, soner og møbelplassering",
  "fargepalette": [
    {{"navn": "Farge", "hex": "#FFFFFF", "bruk": "Vegger", "tone": "Primær/Sekundær/Aksent"}}
  ],
  "materialer": [
    {{"type": "Gulv", "anbefaling": "Produkt og leverandør", "grunn": "Hvorfor", "pris_per_m2": 400}}
  ],
  "belysning": "Komplett belysningsplan med lag (ambient, task, accent)",
  "budsjettfordeling": [
    {{"kategori": "Møbler", "prosent": 40, "estimat_kr": 60000}}
  ],
  "produktanbefalinger": [
    {{"produkt": "IKEA SÖDERHAMN sofa", "butikk": "IKEA", "estimert_pris": 12000, "grunn": "Passer stilen og budsjettet", "prioritet": "Høy"}}
  ],
  "tips": ["Konkret tip om dette rommet"]
}}"""

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        return {"romtype": romtype, "stil": stil, "budsjett": budsjett, "plan": json.loads(text)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Romplanlegger feilet: {e}")
