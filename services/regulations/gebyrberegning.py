"""
Kommunale gebyrberegninger for byggesaker.

Inneholder kjente gebyrstrukturer for norske kommuner samt en AI-assistert
estimeringsmotor for kommuner uten hardkodede satser.

Standardgebyrer som alltid inngår:
  - Grunngebyr: basisgebyr per søknad
  - Tilsynsgebyr: tilleggsgebyr for kommunalt tilsyn
  - Registreringsgebyr: gebyr for matrikkelføring
  - Situasjonskart: gebyr for kommunalt situasjonskart
  - Ferdigattest: gebyr ved ferdigmelding

Prosjektgebyr beregnes etter tiltakstype og størrelse (m²).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GebyrPost:
    navn: str
    belop: float
    beskrivelse: str
    alltid_med: bool = True  # Vises alltid, uavhengig av prosjektstørrelse


@dataclass
class GebyrResultat:
    kommunenummer: str
    kommunenavn: str
    tiltakstype: str
    areal_m2: Optional[int]
    gebyrer: list[GebyrPost]
    total_gebyr: float
    notat: str
    kilde: str  # "hardkodet" | "estimert"
    disclaimer: str = (
        "OBS: Disse gebyrene er estimater basert på kjente satser. "
        "Kontakt kommunen eller se kommunens gebyrregulativ for eksakte priser. "
        "Gebyrer er ekskl. mva."
    )


# ---------------------------------------------------------------------------
# Kjente gebyrstrukturer
# ---------------------------------------------------------------------------

def _nesodden_gebyrer(tiltakstype: str, areal_m2: Optional[int]) -> list[GebyrPost]:
    """
    Nesodden kommune (knr=3212) gebyrregulativ 2026.
    Basert på Nesodden kommunes offentlige gebyrregulativ.
    """
    gebyrer: list[GebyrPost] = [
        GebyrPost(
            navn="Grunngebyr",
            belop=6_240,
            beskrivelse="Basisgebyr for søknadsbehandling (SAK10 §3-1)",
            alltid_med=True,
        ),
        GebyrPost(
            navn="Tilsynsgebyr",
            belop=3_120,
            beskrivelse="Gebyr for kommunalt tilsyn av tiltaket",
            alltid_med=True,
        ),
        GebyrPost(
            navn="Registreringsgebyr (Matrikkel)",
            belop=1_950,
            beskrivelse="Gebyr for matrikkelføring og ajourhold",
            alltid_med=True,
        ),
        GebyrPost(
            navn="Situasjonskart",
            belop=2_400,
            beskrivelse="Gebyr for digitalt situasjonskart fra kommunen",
            alltid_med=True,
        ),
        GebyrPost(
            navn="Ferdigattest",
            belop=3_744,
            beskrivelse="Gebyr for ferdigmelding og utstedelse av ferdigattest",
            alltid_med=True,
        ),
    ]

    # Prosjektgebyr basert på tiltakstype og størrelse
    if tiltakstype in ("tilbygg", "påbygg"):
        if areal_m2 and areal_m2 <= 15:
            gebyrer.append(GebyrPost(
                navn=f"Prosjektgebyr – {tiltakstype} ≤ 15 m²",
                belop=4_680,
                beskrivelse=f"Gebyr for {tiltakstype} opp til 15 m² BRA",
                alltid_med=False,
            ))
        elif areal_m2 and areal_m2 <= 50:
            gebyrer.append(GebyrPost(
                navn=f"Prosjektgebyr – {tiltakstype} 15–50 m²",
                belop=9_360,
                beskrivelse=f"Gebyr for {tiltakstype} 15–50 m² BRA",
                alltid_med=False,
            ))
        elif areal_m2 and areal_m2 <= 100:
            gebyrer.append(GebyrPost(
                navn=f"Prosjektgebyr – {tiltakstype} 50–100 m²",
                belop=15_600,
                beskrivelse=f"Gebyr for {tiltakstype} 50–100 m² BRA",
                alltid_med=False,
            ))
        else:
            gebyrer.append(GebyrPost(
                navn=f"Prosjektgebyr – {tiltakstype} > 100 m²",
                belop=23_400,
                beskrivelse=f"Gebyr for {tiltakstype} over 100 m² BRA",
                alltid_med=False,
            ))

    elif tiltakstype in ("garasje", "carport", "uthus", "bod"):
        areal = areal_m2 or 30
        if areal <= 50:
            gebyrer.append(GebyrPost(
                navn=f"Prosjektgebyr – {tiltakstype} ≤ 50 m²",
                belop=6_240,
                beskrivelse=f"Gebyr for {tiltakstype} opp til 50 m²",
                alltid_med=False,
            ))
        else:
            gebyrer.append(GebyrPost(
                navn=f"Prosjektgebyr – {tiltakstype} > 50 m²",
                belop=10_920,
                beskrivelse=f"Gebyr for {tiltakstype} over 50 m²",
                alltid_med=False,
            ))

    elif tiltakstype in ("nybygg", "enebolig", "tomannsbolig"):
        areal = areal_m2 or 150
        if areal <= 100:
            prosjektgeb = 23_400
        elif areal <= 200:
            prosjektgeb = 39_000
        elif areal <= 300:
            prosjektgeb = 54_600
        else:
            prosjektgeb = 70_200
        gebyrer.append(GebyrPost(
            navn=f"Prosjektgebyr – nybygg {areal} m²",
            belop=prosjektgeb,
            beskrivelse=f"Gebyr for nybygg {areal} m² BRA",
            alltid_med=False,
        ))

    elif tiltakstype == "bruksendring":
        gebyrer.append(GebyrPost(
            navn="Prosjektgebyr – bruksendring",
            belop=7_800,
            beskrivelse="Gebyr for søknad om bruksendring",
            alltid_med=False,
        ))

    elif tiltakstype == "terrasse":
        gebyrer.append(GebyrPost(
            navn="Prosjektgebyr – terrasse",
            belop=4_680,
            beskrivelse="Gebyr for terrasse/balkongsøknad",
            alltid_med=False,
        ))

    elif tiltakstype in ("fasadeendring", "vinduer", "dør"):
        gebyrer.append(GebyrPost(
            navn="Prosjektgebyr – fasadeendring",
            belop=3_120,
            beskrivelse="Gebyr for søknad om fasadeendring",
            alltid_med=False,
        ))

    elif tiltakstype == "riving":
        gebyrer.append(GebyrPost(
            navn="Prosjektgebyr – riving",
            belop=6_240,
            beskrivelse="Gebyr for rivingstillatelse",
            alltid_med=False,
        ))

    else:
        # Generisk prosjektgebyr
        gebyrer.append(GebyrPost(
            navn=f"Prosjektgebyr – {tiltakstype}",
            belop=9_360,
            beskrivelse="Gebyr for søknadsbehandling",
            alltid_med=False,
        ))

    return gebyrer


# Kommuneoversikt: legg til nye kommuner her
_KJENTE_KOMMUNER: dict[str, dict] = {
    "3212": {
        "navn": "Nesodden",
        "gebyr_func": _nesodden_gebyrer,
    },
}


def beregn_gebyrer(
    kommunenummer: str,
    kommunenavn: str,
    tiltakstype: str,
    areal_m2: Optional[int] = None,
) -> GebyrResultat:
    """
    Beregner forventede kommunale gebyrer for et byggetiltak.

    For kjente kommuner brukes hardkodede satser fra gebyrregulativet.
    For ukjente kommuner returneres et estimat med typiske norske satser.
    """
    tiltakstype_norm = tiltakstype.lower().strip()

    if kommunenummer in _KJENTE_KOMMUNER:
        kommune_info = _KJENTE_KOMMUNER[kommunenummer]
        gebyrer = kommune_info["gebyr_func"](tiltakstype_norm, areal_m2)
        total = sum(g.belop for g in gebyrer)
        return GebyrResultat(
            kommunenummer=kommunenummer,
            kommunenavn=kommune_info["navn"],
            tiltakstype=tiltakstype_norm,
            areal_m2=areal_m2,
            gebyrer=gebyrer,
            total_gebyr=total,
            notat=f"Satser fra {kommune_info['navn']} kommunes gebyrregulativ 2026.",
            kilde="hardkodet",
        )
    else:
        # Generiske estimater for ukjente kommuner (typiske norske satser)
        gebyrer = _generiske_gebyrer(tiltakstype_norm, areal_m2)
        total = sum(g.belop for g in gebyrer)
        return GebyrResultat(
            kommunenummer=kommunenummer,
            kommunenavn=kommunenavn,
            tiltakstype=tiltakstype_norm,
            areal_m2=areal_m2,
            gebyrer=gebyrer,
            total_gebyr=total,
            notat=(
                f"Estimert basert på typiske norske kommunale gebyrsatser. "
                f"Se {kommunenavn} kommunes gebyrregulativ for eksakte priser."
            ),
            kilde="estimert",
        )


def _generiske_gebyrer(tiltakstype: str, areal_m2: Optional[int]) -> list[GebyrPost]:
    """Generiske estimater for kommuner uten hardkodede satser."""
    # Bruker typiske norske gjennomsnittssatser (2025/2026)
    gebyrer: list[GebyrPost] = [
        GebyrPost("Grunngebyr", 5_500, "Basisgebyr for søknadsbehandling", True),
        GebyrPost("Tilsynsgebyr", 2_800, "Gebyr for kommunalt tilsyn", True),
        GebyrPost("Registreringsgebyr (Matrikkel)", 1_750, "Gebyr for matrikkelføring", True),
        GebyrPost("Situasjonskart", 2_200, "Gebyr for situasjonskart fra kommunen", True),
        GebyrPost("Ferdigattest", 3_300, "Gebyr for ferdigattest", True),
    ]

    if tiltakstype in ("tilbygg", "påbygg"):
        areal = areal_m2 or 30
        if areal <= 15:
            gebyrer.append(GebyrPost(f"Prosjektgebyr – {tiltakstype} ≤ 15 m²", 4_000, "", False))
        elif areal <= 50:
            gebyrer.append(GebyrPost(f"Prosjektgebyr – {tiltakstype} 15–50 m²", 8_500, "", False))
        elif areal <= 100:
            gebyrer.append(GebyrPost(f"Prosjektgebyr – {tiltakstype} 50–100 m²", 14_000, "", False))
        else:
            gebyrer.append(GebyrPost(f"Prosjektgebyr – {tiltakstype} > 100 m²", 21_000, "", False))
    elif tiltakstype in ("garasje", "carport", "uthus"):
        areal = areal_m2 or 30
        gebyrer.append(GebyrPost(
            f"Prosjektgebyr – {tiltakstype}",
            5_500 if areal <= 50 else 9_500, "", False
        ))
    elif tiltakstype in ("nybygg", "enebolig", "tomannsbolig"):
        areal = areal_m2 or 150
        prosjektgeb = max(20_000, int(areal * 180))  # ca 180 kr/m²
        gebyrer.append(GebyrPost(f"Prosjektgebyr – nybygg {areal} m²", prosjektgeb, "", False))
    elif tiltakstype == "bruksendring":
        gebyrer.append(GebyrPost("Prosjektgebyr – bruksendring", 7_000, "", False))
    elif tiltakstype in ("fasadeendring", "vinduer", "dør"):
        gebyrer.append(GebyrPost("Prosjektgebyr – fasadeendring", 2_800, "", False))
    elif tiltakstype == "riving":
        gebyrer.append(GebyrPost("Prosjektgebyr – riving", 5_500, "", False))
    elif tiltakstype == "terrasse":
        gebyrer.append(GebyrPost("Prosjektgebyr – terrasse", 4_000, "", False))
    else:
        gebyrer.append(GebyrPost(f"Prosjektgebyr – {tiltakstype}", 8_000, "", False))

    return gebyrer
