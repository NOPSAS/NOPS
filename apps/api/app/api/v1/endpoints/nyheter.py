"""
ByggSjekk – Eiendomsnyheter-aggregator.

Henter nyheter fra norske eiendomsmedier via RSS/Atom-feeds.
Kilder: Estate Nyheter, EiendomsWatch, Eiendom Norge, E24, Aftenposten,
ABC Nyheter, regjeringen.no m.fl.

GET /nyheter – Siste nyheter fra alle kilder
GET /nyheter/kilder – Liste over konfigurerte kilder
"""
from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_optional_user

router = APIRouter()


@dataclass
class Nyhetskilde:
    id: str
    navn: str
    url: str
    feed_url: str
    kategori: str  # "bransje" | "marked" | "politikk" | "generelt"
    logo_tekst: str  # Kort tekst for visning


@dataclass
class Nyhetsartikkel:
    tittel: str
    url: str
    kilde: str
    kilde_id: str
    publisert: str
    beskrivelse: str
    kategori: str


# ── Konfigurerte nyhetskilder ───────────────────────────────
KILDER: list[Nyhetskilde] = [
    Nyhetskilde(
        id="estate",
        navn="Estate Nyheter",
        url="https://estatenyheter.no",
        feed_url="https://estatenyheter.no/feed/",
        kategori="bransje",
        logo_tekst="EN",
    ),
    Nyhetskilde(
        id="eiendomswatch",
        navn="EiendomsWatch",
        url="https://eiendomswatch.no",
        feed_url="https://eiendomswatch.no/feed/",
        kategori="bransje",
        logo_tekst="EW",
    ),
    Nyhetskilde(
        id="eiendomnorge",
        navn="Eiendom Norge",
        url="https://eiendomnorge.no",
        feed_url="https://eiendomnorge.no/feed/",
        kategori="marked",
        logo_tekst="NO",
    ),
    Nyhetskilde(
        id="norskeiendom",
        navn="Norsk Eiendom",
        url="https://norskeiendom.org",
        feed_url="https://norskeiendom.org/feed/",
        kategori="bransje",
        logo_tekst="NE",
    ),
    Nyhetskilde(
        id="e24",
        navn="E24 Eiendom",
        url="https://e24.no/emne/eiendom",
        feed_url="https://e24.no/rss2/?topic=eiendom",
        kategori="generelt",
        logo_tekst="E24",
    ),
    Nyhetskilde(
        id="aftenposten",
        navn="Aftenposten Bolig",
        url="https://aftenposten.no",
        feed_url="https://www.aftenposten.no/rss/bolig",
        kategori="generelt",
        logo_tekst="AP",
    ),
    Nyhetskilde(
        id="abc",
        navn="ABC Nyheter Eiendom",
        url="https://abcnyheter.no/tag/eiendom",
        feed_url="https://abcnyheter.no/rss/eiendom",
        kategori="generelt",
        logo_tekst="ABC",
    ),
    Nyhetskilde(
        id="regjeringen",
        navn="Regjeringen – Plan og bygg",
        url="https://regjeringen.no/no/tema/plan-bygg-og-eiendom",
        feed_url="https://www.regjeringen.no/no/rss/tema/plan-bygg-og-eiendom/?format=atom",
        kategori="politikk",
        logo_tekst="GOV",
    ),
]


def _parse_rss_item(item: ET.Element, kilde: Nyhetskilde) -> Nyhetsartikkel | None:
    """Parser et RSS/Atom <item> eller <entry> element."""
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # RSS 2.0
    tittel = item.findtext("title") or ""
    url = item.findtext("link") or ""
    beskrivelse = item.findtext("description") or ""
    publisert = item.findtext("pubDate") or item.findtext("dc:date") or ""

    # Atom fallback
    if not tittel:
        tittel = item.findtext("atom:title", "", ns)
    if not url:
        link_elem = item.find("atom:link", ns)
        if link_elem is not None:
            url = link_elem.get("href", "")
    if not publisert:
        publisert = item.findtext("atom:published", "", ns) or item.findtext("atom:updated", "", ns)

    if not tittel or not url:
        return None

    # Rens HTML fra beskrivelse
    if "<" in beskrivelse:
        import re
        beskrivelse = re.sub(r"<[^>]+>", "", beskrivelse)
    beskrivelse = beskrivelse[:300].strip()

    return Nyhetsartikkel(
        tittel=tittel.strip(),
        url=url.strip(),
        kilde=kilde.navn,
        kilde_id=kilde.id,
        publisert=publisert.strip(),
        beskrivelse=beskrivelse,
        kategori=kilde.kategori,
    )


async def _hent_feed(client: httpx.AsyncClient, kilde: Nyhetskilde) -> list[Nyhetsartikkel]:
    """Henter og parser en RSS/Atom-feed for en kilde."""
    try:
        resp = await client.get(
            kilde.feed_url,
            headers={"User-Agent": "nops.no/ByggSjekk Feed Reader (+https://nops.no)"},
            timeout=8,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.text)

        # RSS 2.0: //channel/item
        items = root.findall(".//item")
        # Atom: //entry
        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//atom:entry", ns)
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        artikler = []
        for item in items[:10]:  # Max 10 per kilde
            a = _parse_rss_item(item, kilde)
            if a:
                artikler.append(a)
        return artikler
    except Exception:
        return []


@router.get(
    "",
    summary="Siste eiendomsnyheter fra norske medier",
    response_model=dict,
)
async def hent_nyheter(
    kategori: Annotated[str | None, Query(description="Filtrer: bransje|marked|politikk|generelt")] = None,
    antall: Annotated[int, Query(ge=1, le=100)] = 30,
    current_user = Depends(get_optional_user),
) -> dict:
    """Henter og aggregerer nyheter fra alle konfigurerte eiendomsmedier."""
    kilder_aa_hente = KILDER
    if kategori:
        kilder_aa_hente = [k for k in KILDER if k.kategori == kategori]

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_hent_feed(client, k) for k in kilder_aa_hente],
            return_exceptions=True,
        )

    alle: list[Nyhetsartikkel] = []
    for r in results:
        if isinstance(r, list):
            alle.extend(r)

    # Sorter etter publiseringsdato (nyeste først, best-effort)
    def _parse_dato(s: str) -> datetime:
        for fmt in [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
        ]:
            try:
                return datetime.strptime(s, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.min

    alle.sort(key=lambda a: _parse_dato(a.publisert), reverse=True)
    alle = alle[:antall]

    return {
        "antall": len(alle),
        "kategori_filter": kategori,
        "artikler": [
            {
                "tittel": a.tittel,
                "url": a.url,
                "kilde": a.kilde,
                "kilde_id": a.kilde_id,
                "publisert": a.publisert,
                "beskrivelse": a.beskrivelse,
                "kategori": a.kategori,
            }
            for a in alle
        ],
    }


@router.get(
    "/kilder",
    summary="Konfigurerte nyhetskilder",
    response_model=dict,
)
async def hent_kilder(
    current_user = Depends(get_optional_user),
) -> dict:
    return {
        "antall": len(KILDER),
        "kilder": [
            {
                "id": k.id,
                "navn": k.navn,
                "url": k.url,
                "kategori": k.kategori,
                "logo_tekst": k.logo_tekst,
            }
            for k in KILDER
        ],
    }
