"""
ByggSjekk – Smakebit / Gratis eiendomsprofil.

Gir en gratis "smakebit" av alle NOPS-tjenester for enhver eiendom.
Nok til at kunden får verdi – men lite nok til at de vil kjøpe mer.

GET /smakebit/{knr}/{gnr}/{bnr} – Gratis eiendomsprofil med smakebit av alle tjenester
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

router = APIRouter()

for _p in ["/app", "/app/services"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


@router.get(
    "/{knr}/{gnr}/{bnr}",
    summary="Gratis eiendomsprofil – smakebit av alle NOPS-tjenester",
    response_model=dict,
)
async def smakebit(
    knr: Annotated[str, Path(description="Kommunenummer")],
    gnr: Annotated[int, Path(description="Gårdsnummer")],
    bnr: Annotated[int, Path(description="Bruksnummer")],
) -> dict:
    """
    Gratis eiendomsprofil som gir en smakebit av ALLE tjenester.
    Ingen auth nødvendig – åpen for alle.

    Viser nok til at kunden ser verdien, men begrenser detaljer
    slik at de vil oppgradere for full tilgang.

    Returnerer:
    - Grunndata (adresse, areal, byggeår, bygningstype)
    - Antall byggesaker (men ikke detaljer)
    - Reguleringsplan-sammendrag (men ikke bestemmelser)
    - DOK-treff (antall berørte, men ikke hvilke)
    - Verdiindikator (prisklasse, men ikke eksakt estimat)
    - Tilbygg-potensial (ja/nei, men ikke arealregnestykke)
    - Dispensasjonshistorikk (antall, men ikke innhold)
    - Ferdigattest-status (ja/nei)
    - CTA-er til betalte tjenester
    """
    try:
        resultat = {
            "eiendom": {"knr": knr, "gnr": gnr, "bnr": bnr},
            "grunndata": {},
            "byggesaker_smakebit": {},
            "reguleringsplan_smakebit": {},
            "dok_smakebit": {},
            "verdi_smakebit": {},
            "tilbygg_smakebit": {},
            "dispensasjon_smakebit": {},
            "ferdigattest_smakebit": {},
            "tjenester_cta": [],
        }

        # ── Hent alt parallelt ──────────────────────────────────
        tasks = {}

        try:
            from services.municipality_connectors.kartverket import get_kartverket_adapter
            tasks["kartverket"] = get_kartverket_adapter().full_oppslag(knr, gnr, bnr, 0, 0)
        except ImportError:
            pass

        try:
            from services.municipality_connectors.planslurpen import get_planslurpen_adapter
            tasks["planslurpen"] = get_planslurpen_adapter().hent_planbestemmelser(knr, gnr, bnr, 0, 0)
        except ImportError:
            pass

        try:
            from services.municipality_connectors.arealplaner import (
                get_nesodden_adapter, get_dok_adapter, get_arealplaner_adapter,
                EiendomsoppslagResult,
            )
            if knr == "3212":
                tasks["arealplaner"] = get_nesodden_adapter().full_eiendomsoppslag(gnr, bnr, None, None)
            else:
                async def _ap():
                    dok = get_dok_adapter()
                    plan = get_arealplaner_adapter()
                    d, p = await asyncio.gather(
                        dok.analyse_eiendom(knr, gnr, bnr, None, None),
                        plan.hent_planrapport(knr, gnr, bnr, None, None),
                        return_exceptions=True,
                    )
                    r = EiendomsoppslagResult(kommunenummer=knr, gnr=gnr, bnr=bnr)
                    if not isinstance(d, Exception):
                        r.dok_analyse = d
                    if not isinstance(p, Exception):
                        r.planrapport = p
                    return r
                tasks["arealplaner"] = _ap()
        except ImportError:
            pass

        try:
            from services.municipality_connectors.eiendomsdata import get_eiendomsdata_adapter
            tasks["verdi"] = get_eiendomsdata_adapter().hent_historikk(
                kommunenummer=knr, gnr=gnr, bnr=bnr
            )
        except ImportError:
            pass

        results = {}
        if tasks:
            gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for key, result in zip(tasks.keys(), gathered):
                if not isinstance(result, Exception):
                    results[key] = result

        # ── Grunndata (GRATIS – vises fullt) ────────────────────
        kr = results.get("kartverket")
        if kr:
            e = kr.eiendom
            resultat["grunndata"] = {
                "adresse": e.adresse if e else None,
                "postnummer": e.postnummer if e else None,
                "poststed": e.poststed if e else None,
                "kommunenavn": kr.kommune.kommunenavn if kr.kommune else knr,
                "tomteareal_m2": e.areal_m2 if e else None,
            }
            resultat["eiendom"]["adresse"] = e.adresse if e else f"Gnr. {gnr}, Bnr. {bnr}"
            resultat["eiendom"]["kommunenavn"] = kr.kommune.kommunenavn if kr.kommune else knr

            # Bygninger – vis ALT (generøs smakebit)
            if kr.bygninger:
                resultat["grunndata"]["bygninger"] = [
                    {
                        "bygningstype": b.bygningstype,
                        "byggeaar": b.byggeaar,
                        "bruksareal_m2": b.bruksareal,
                        "bygningstatus": getattr(b, "bygningstatus", None),
                    }
                    for b in kr.bygninger[:5]
                ]
                resultat["grunndata"]["antall_bygninger"] = len(kr.bygninger)

            # Byggesaker – vis FULLT (generøs – dette skaper tillit)
            resultat["byggesaker"] = {
                "antall_saker": len(kr.byggesaker) if kr.byggesaker else 0,
                "saker": [
                    {
                        "tittel": getattr(s, "tittel", None) or getattr(s, "beskrivelse", None) or getattr(s, "sakstype", "Ukjent"),
                        "status": getattr(s, "status", None),
                        "vedtaksdato": getattr(s, "vedtaksdato", None),
                        "sakstype": getattr(s, "sakstype", None),
                    }
                    for s in (kr.byggesaker or [])[:10]
                ],
            }

            # ── AVVIKSDETEKSJON (gratis! dette er hook-en) ──────────
            avvik_funnet = []
            har_ferdigattest = False

            for s in (kr.byggesaker or []):
                st = (getattr(s, "status", "") or "").lower()
                if "ferdigattest" in st:
                    har_ferdigattest = True

            # Sjekk 1: Manglende ferdigattest
            saker_uten_fa = [
                s for s in (kr.byggesaker or [])
                if (getattr(s, "status", "") or "").lower() in ("igangsatt", "under arbeid", "godkjent", "rammetillatelse")
            ]
            if saker_uten_fa:
                avvik_funnet.append({
                    "type": "MANGLENDE_FERDIGATTEST",
                    "alvorlighet": "HØY",
                    "beskrivelse": f"{len(saker_uten_fa)} byggesak(er) uten ferdigattest registrert. Dette kan bety at tiltak ikke er ferdigmeldt.",
                    "konsekvens": "Kan påvirke salgsverdi, forsikring og lovlighet. Kommunen kan kreve retting.",
                    "nops_losning": "Vi hjelper deg med å innhente og ordne ferdigattest. Kontakt hey@nops.no.",
                    "pris": "Fra 5 000 kr",
                })

            # Sjekk 2: Areal-avvik mellom bygninger og byggesaker
            if kr.bygninger and kr.byggesaker:
                registrert_bra = sum(b.bruksareal or 0 for b in kr.bygninger)
                if registrert_bra > 0 and len(kr.byggesaker) == 0:
                    avvik_funnet.append({
                        "type": "INGEN_BYGGESAKER",
                        "alvorlighet": "MIDDELS",
                        "beskrivelse": f"Bygning på {registrert_bra} m² er registrert, men ingen byggesaker funnet. Kan tyde på uregistrerte endringer.",
                        "konsekvens": "Mulig ulovlig oppført eller endret bygning.",
                        "nops_losning": "Vi gjør en full avviksanalyse og hjelper med nødvendige søknader.",
                        "pris": "Starter-plan 499 kr/mnd",
                    })

            # Sjekk 3: Gammel bygning uten nyere byggesaker
            if kr.bygninger:
                b0 = kr.bygninger[0]
                if b0.byggeaar and b0.byggeaar < 1970 and len(kr.byggesaker or []) < 2:
                    avvik_funnet.append({
                        "type": "ELDRE_BOLIG_UTEN_DOKUMENTASJON",
                        "alvorlighet": "LAV",
                        "beskrivelse": f"Boligen er fra {b0.byggeaar} med lite byggesakshistorikk. Typisk for eldre boliger med mulige uregistrerte endringer.",
                        "konsekvens": "Endringer gjort uten søknad kan være ulovlige. Viktig å avklare ved salg.",
                        "nops_losning": "Vi innhenter godkjente tegninger fra kommunen (gratis) og gjør en komplett avvikssjekk.",
                        "pris": "Gratis tegningshenting + Starter for full analyse",
                    })

            resultat["avviksdeteksjon"] = {
                "antall_avvik": len(avvik_funnet),
                "avvik": avvik_funnet,
                "har_ferdigattest": har_ferdigattest,
                "vurdering": (
                    "Ingen avvik funnet – eiendommen ser ryddig ut!"
                    if not avvik_funnet else
                    f"{len(avvik_funnet)} mulig(e) avvik funnet. Vi anbefaler en full gjennomgang."
                ),
                "nops_tilbud": {
                    "beskrivelse": "nops.no kan løse dette for deg – vi innhenter tegninger, sjekker avvik og ordner søknader.",
                    "kontakt": "hey@nops.no",
                    "gratis": ["Innhenting av godkjente tegninger", "Ferdigattest-sjekk", "Grunnleggende avvikssjekk"],
                    "betalt": ["Full AI-avviksanalyse", "Byggesøknad for retting", "Dispensasjonssøknad"],
                },
            }

            # Ferdigattest
            resultat["ferdigattest"] = {
                "status": "Ferdigattest funnet" if har_ferdigattest else "Mangler ferdigattest",
                "cta": "Vi hjelper deg med å ordne ferdigattest – kontakt hey@nops.no" if not har_ferdigattest else None,
                "lenke": "/ferdigattest",
            }

        # ── Reguleringsplan (GENERØS – vis alt!) ────────────────
        ap = results.get("arealplaner")
        if ap:
            pr = getattr(ap, "planrapport", ap)
            if hasattr(pr, "gjeldende_planer") and pr.gjeldende_planer:
                resultat["reguleringsplan"] = {
                    "antall_planer": len(pr.gjeldende_planer),
                    "planer": [
                        {
                            "plan_navn": getattr(p, "plan_navn", ""),
                            "plan_type": getattr(p, "plan_type", ""),
                            "arealformaal": getattr(p, "arealformål", ""),
                            "status": getattr(p, "status", ""),
                        }
                        for p in pr.gjeldende_planer[:5]
                    ],
                }

            # Dispensasjoner – vis FULLT
            if hasattr(pr, "dispensasjoner") and pr.dispensasjoner:
                resultat["dispensasjoner"] = {
                    "antall": len(pr.dispensasjoner),
                    "liste": [
                        {
                            "beskrivelse": getattr(d, "beskrivelse", getattr(d, "saks_type", "")),
                            "status": getattr(d, "status", ""),
                        }
                        for d in pr.dispensasjoner[:10]
                    ],
                    "hint": f"{len(pr.dispensasjoner)} dispensasjon(er) registrert – dette kan være relevant for din byggesøknad",
                    "lenke": "/dispensasjon",
                }
            else:
                resultat["dispensasjon_smakebit"] = {
                    "antall_dispensasjoner": 0,
                    "hint": "Ingen dispensasjoner registrert",
                }

            # DOK – vis FULLT med varsler for kritiske funn
            da = getattr(ap, "dok_analyse", None)
            if da and hasattr(da, "berørte_datasett"):
                # Klassifiser kritiske DOK-funn
                _KRITISKE_STIKKORD = {
                    "radon": {
                        "alvorlighet": "HØY",
                        "tittel": "Radon",
                        "beskrivelse": "Eiendommen ligger i et område med forhøyet radonrisiko.",
                        "konsekvens": "Ved byggesak kreves radonsperre og tiltak iht. TEK17 §13-5 (maks 200 Bq/m³). Ved bruksendring av kjeller til boareal er dette kritisk.",
                        "tiltak": "Radonmåling anbefales. Ved bygging: radonmembran i grunn og tilrettelegging for radonbrønn.",
                        "tek17": "TEK17 §13-5",
                    },
                    "flom": {
                        "alvorlighet": "HØY",
                        "tittel": "Flomfare",
                        "beskrivelse": "Eiendommen kan være utsatt for flom.",
                        "konsekvens": "Byggetiltak må plasseres iht. sikkerhetsklasse F1-F3 (TEK17 §7-2). Kan kreve flomvurdering fra NVE.",
                        "tiltak": "Sjekk NVE flomsonekart. Ved byggesøknad: dokumenter sikkerhet mot flom.",
                        "tek17": "TEK17 §7-2",
                    },
                    "kvikkleire": {
                        "alvorlighet": "KRITISK",
                        "tittel": "Kvikkleire",
                        "beskrivelse": "Eiendommen ligger i et område med fare for kvikkleireskred.",
                        "konsekvens": "Geoteknisk vurdering er PÅKREVD ved alle byggetiltak. NVE og kommunen stiller strenge krav.",
                        "tiltak": "Bestill geoteknisk rapport FØR byggesøknad. Kan kreve stabiliserende tiltak.",
                        "tek17": "TEK17 §7-3",
                    },
                    "skred": {
                        "alvorlighet": "HØY",
                        "tittel": "Skredfare",
                        "beskrivelse": "Eiendommen kan være utsatt for skred (stein, jord, snø).",
                        "konsekvens": "Skredfarevurdering kreves ved byggesøknad. Plassering og sikring må dokumenteres.",
                        "tiltak": "Sjekk NVE skredfarekart. Geoteknisk rapport kan være nødvendig.",
                        "tek17": "TEK17 §7-3",
                    },
                    "aktsomhet": {
                        "alvorlighet": "MIDDELS",
                        "tittel": "Aktsomhetssone",
                        "beskrivelse": "Eiendommen ligger i en aktsomhetssone for naturfare.",
                        "konsekvens": "Kommunen kan kreve utredning av naturfare ved byggesøknad.",
                        "tiltak": "Sjekk hvilken type aktsomhetssone det gjelder. Kan kreve geoteknisk eller hydrologisk vurdering.",
                        "tek17": "TEK17 §7-1",
                    },
                    "støy": {
                        "alvorlighet": "MIDDELS",
                        "tittel": "Støysone",
                        "beskrivelse": "Eiendommen ligger i en støysone (vei, jernbane, fly).",
                        "konsekvens": "Ved byggesøknad: krav til fasadeisolering og romplanlegging. Utendørs oppholdsareal kan begrenses.",
                        "tiltak": "Støyberegning kan kreves. Fasade mot støykilde må ha tilstrekkelig lydisolering.",
                        "tek17": "TEK17 §13-6",
                    },
                    "kulturminne": {
                        "alvorlighet": "MIDDELS",
                        "tittel": "Kulturminne / verneverdi",
                        "beskrivelse": "Eiendommen berøres av kulturminneregistreringer.",
                        "konsekvens": "Tiltak kan kreve godkjenning fra fylkeskommunen eller Riksantikvaren. Automatisk fredede kulturminner har streng beskyttelse.",
                        "tiltak": "Kontakt fylkeskommunens kulturminneavdeling. SEFRAK-registrerte bygg har egne regler.",
                        "tek17": "Kulturminneloven",
                    },
                    "forurens": {
                        "alvorlighed": "HØY",
                        "tittel": "Forurenset grunn",
                        "beskrivelse": "Eiendommen kan ha forurenset grunn.",
                        "konsekvens": "Graving og byggearbeid kan kreve miljøteknisk undersøkelse og tiltaksplan.",
                        "tiltak": "Miljøteknisk grunnundersøkelse før byggestart. Kostnad typisk 30 000-100 000 kr.",
                        "tek17": "Forurensningsforskriften kap. 2",
                    },
                }

                dok_varsler = []
                berørte_med_info = []

                for ds in da.berørte_datasett[:15]:
                    ds_navn = (getattr(ds, "navn", "") or "").lower()
                    ds_tema = (getattr(ds, "tema", "") or "").lower()
                    tekst = ds_navn + " " + ds_tema

                    datasett_info = {
                        "navn": getattr(ds, "navn", ""),
                        "tema": getattr(ds, "tema", ""),
                    }

                    # Sjekk mot kritiske stikkord
                    for stikkord, info in _KRITISKE_STIKKORD.items():
                        if stikkord in tekst:
                            datasett_info["varsel"] = info
                            dok_varsler.append({
                                **info,
                                "datasett": getattr(ds, "navn", ""),
                            })
                            break

                    berørte_med_info.append(datasett_info)

                resultat["dok_analyse"] = {
                    "antall_berørt": len(da.berørte_datasett),
                    "antall_ikke_berørt": getattr(da, "antall_ikke_berørt", 0),
                    "berørte_datasett": berørte_med_info,
                    "varsler": dok_varsler,
                    "antall_kritiske_varsler": len([v for v in dok_varsler if v.get("alvorlighet") in ("KRITISK", "HØY")]),
                    "oppsummering": (
                        f"⚠️ {len(dok_varsler)} viktig(e) funn i DOK-analysen som påvirker byggesak. Se detaljer under."
                        if dok_varsler else
                        "Ingen kritiske funn i DOK-analysen."
                    ),
                    "nops_tilbud": (
                        "nops.no hjelper med å håndtere DOK-funn i byggesøknaden – vi sørger for riktig dokumentasjon."
                        if dok_varsler else None
                    ),
                }

        # ── Planslurpen (SMAKEBIT – vis at vi har data, skjul tall) ──
        ps = results.get("planslurpen")
        if ps and hasattr(ps, "antall_planer") and ps.antall_planer > 0:
            p0 = ps.planer[0]
            # Planbestemmelser – vis ALT (generøs)
            resultat["planbestemmelser"] = {
                "maks_hoyde": p0.maks_hoyde,
                "maks_utnyttelse": p0.maks_utnyttelse,
                "tillatt_bruk": p0.tillatt_bruk,
                "plan_navn": p0.plan_navn,
            }

            # Tilbygg-potensial basert på data
            resultat["tilbygg_potensial"] = {
                "har_utnyttelsesgrad": bool(p0.maks_utnyttelse),
                "har_hoydegrense": bool(p0.maks_hoyde),
                "beskrivelse": (
                    f"Maks utnyttelse: {p0.maks_utnyttelse}. Maks høyde: {p0.maks_hoyde or 'PBL §29-4 (gesims 8m, møne 9m)'}. "
                    "Kontakt oss for arealregnestykke – vi beregner nøyaktig hvor mange m² du kan bygge ut."
                ) if p0.maks_utnyttelse else (
                    "Utnyttelsesgrad ikke funnet i plan. Kontakt oss for manuell vurdering."
                ),
                "nops_tilbud": "Vi lager arealregnestykke og tegninger for tilbygg/påbygg – fra 15 000 kr",
                "lenke": "/tjenester",
            }

        # ── Verdi (vis estimat – generøst!) ──────────────────────
        verdi = results.get("verdi")
        if verdi and hasattr(verdi, "estimert_verdi") and verdi.estimert_verdi:
            resultat["verdiestimering"] = {
                "estimert_verdi_kr": verdi.estimert_verdi,
                "pris_per_kvm": verdi.pris_per_kvm,
                "kommune_median_pris": verdi.kommune_median_pris,
                "prisvekst_prosent": verdi.kommune_prisvekst_prosent,
                "estimat_metode": verdi.estimat_metode,
            }

        # ── CTA-er til betalte tjenester ────────────────────────
        resultat["tjenester_cta"] = [
            {
                "tjeneste": "AI-risikoanalyse",
                "beskrivelse": "Full AI-analyse av avvik, dispensasjonsbehov og reguleringsplan",
                "pris": "Starter-plan (499 kr/mnd)",
                "lenke": "/property",
            },
            {
                "tjeneste": "Tilbygg-analyse",
                "beskrivelse": "Komplett arealregnestykke – se nøyaktig hvor mye du kan bygge",
                "pris": "Gratis grunnberegning",
                "lenke": "/property",
            },
            {
                "tjeneste": "Dispensasjonssøknad",
                "beskrivelse": "AI-generert dispensasjonssøknad med fordel/ulempe-vurdering",
                "pris": "Starter-plan",
                "lenke": "/dispensasjon",
            },
            {
                "tjeneste": "Tomtedeling",
                "beskrivelse": "Sjekk om eiendommen kan deles – med arealregnestykke",
                "pris": "Starter-plan",
                "lenke": "/tomtedeling",
            },
            {
                "tjeneste": "Investeringsanalyse",
                "beskrivelse": "Yield, ROI og cashflow-beregning",
                "pris": "Gratis",
                "lenke": "/investering",
            },
            {
                "tjeneste": "Godkjente tegninger",
                "beskrivelse": "Vi innhenter sist godkjente tegninger fra kommunen – gratis",
                "pris": "Gratis",
                "lenke": "/dokumenter",
            },
            {
                "tjeneste": "Komplett pakke",
                "beskrivelse": "Alt automatisk: matrikkel, byggesaker, AI-analyse, renders, PDF",
                "pris": "Fra 2 490 kr",
                "lenke": "/pakke",
            },
        ]

        resultat["se_eiendom_url"] = f"https://seeiendom.kartverket.no/?kommunenr={knr}&gnr={gnr}&bnr={bnr}"

        return resultat

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Smakebit feilet: {exc}")
