"""
ByggSjekk / nops.no – Eiendomsintelligens AI-analyse.

Bruker Anthropic Claude eller OpenAI GPT til å analysere en eiendom basert på
alle tilgjengelige datakilder og generere en strukturert rapport med:
- Risikovurdering
- Avviksanalyse
- Dispensasjonsgrunnlag
- Anbefalinger til arkitekt
- Markedsposisjonering

VIKTIG: Alle vurderinger er beslutningsstøtte – ikke juridiske konklusjoner.
"""

from __future__ import annotations

import logging
import sys
import os as _os
from dataclasses import dataclass, field
from typing import Any

_svc_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "../.."))
if _svc_root not in sys.path:
    sys.path.insert(0, _svc_root)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataklasser
# ---------------------------------------------------------------------------


@dataclass
class PropertyAnalysisResult:
    """Komplett AI-analyse av en eiendom."""

    eiendom_id: str          # gnr/bnr/kommunenr
    risiko_nivaa: str        # "LAV" | "MIDDELS" | "HØY" | "KRITISK"
    risiko_score: float      # 0.0–1.0
    sammendrag: str          # Kort norsk sammendrag
    nøkkelfinninger: list[str] = field(default_factory=list)
    anbefalinger: list[str] = field(default_factory=list)
    avviksvurdering: str = ""
    dispensasjonsgrunnlag: str = ""
    reguleringsplan_vurdering: str = ""
    dok_analyse_vurdering: str = ""
    fraskrivelse: str = (
        "Denne analysen er generert av ByggSjekk AI og er kun ment som beslutningsstøtte. "
        "Ansvarlig arkitekt må alltid kvalitetssikre og ta endelige beslutninger. "
        "Analysen er ikke en juridisk vurdering."
    )
    kilde_data: dict[str, Any] = field(default_factory=dict)
    model_used: str = ""


# ---------------------------------------------------------------------------
# Prompt-bygger
# ---------------------------------------------------------------------------


def _bygg_analyse_prompt(eiendom_data: dict[str, Any]) -> str:
    """Bygger en norsk analyseprompt basert på eiendomsdata."""

    # Ekstraher nøkkelinformasjon
    knr = eiendom_data.get("kommunenummer", "")
    gnr = eiendom_data.get("gnr", "")
    bnr = eiendom_data.get("bnr", "")
    eiendom = eiendom_data.get("eiendom") or {}
    adresse = eiendom.get("adresse", f"Gnr. {gnr} Bnr. {bnr}")
    kommune = (eiendom_data.get("kommune") or {}).get("kommunenavn", knr)

    bygninger = eiendom_data.get("bygninger", [])
    byggesaker = eiendom_data.get("byggesaker", [])
    planrapport = eiendom_data.get("planrapport") or {}
    dok_analyse = eiendom_data.get("dok_analyse") or {}
    feilmeldinger = eiendom_data.get("feilmeldinger", [])

    # Formater byggesaker
    byggesak_tekst = ""
    if byggesaker:
        byggesak_tekst = "\n".join(
            f"- {s.get('tittel') or s.get('beskrivelse') or s.get('sakstype', 'Ukjent sak')}: "
            f"Status={s.get('status', '?')}, Vedtaksdato={s.get('vedtaksdato', '?')}"
            for s in byggesaker[:10]
        )
    else:
        byggesak_tekst = "Ingen byggesaker funnet i offentlige registre."

    # Formater arealplaner
    planer = planrapport.get("gjeldende_planer", [])
    plan_tekst = ""
    if planer:
        plan_tekst = "\n".join(
            f"- {p.get('plan_navn', '')}: {p.get('plan_type', '')} "
            f"(Status: {p.get('status', '?')}, Formål: {p.get('arealformål', '?')})"
            for p in planer[:5]
        )
    else:
        plan_tekst = "Ingen arealplaner funnet."

    # Formater dispensasjoner
    dispenser = planrapport.get("dispensasjoner", [])
    disp_tekst = ""
    if dispenser:
        disp_tekst = "\n".join(
            f"- {d.get('beskrivelse') or d.get('saks_type', 'Ukjent')}: "
            f"Status={d.get('status', '?')}"
            for d in dispenser[:5]
        )
    else:
        disp_tekst = "Ingen registrerte dispensasjoner."

    # Formater DOK-analyse
    dok_berørt = len(dok_analyse.get("berørte_datasett", []))
    dok_datasett = [d.get("navn", "") for d in dok_analyse.get("berørte_datasett", [])[:5]]
    dok_tekst = (
        f"{dok_berørt} berørte datasett: {', '.join(dok_datasett)}"
        if dok_datasett else "Ingen DOK-analyse tilgjengelig."
    )

    # Formater bygninger
    byg_tekst = ""
    if bygninger:
        byg_tekst = "\n".join(
            f"- Bygningsnr. {b.get('bygningsnummer', '?')}: "
            f"{b.get('bygningstype', '?')}, Byggeår={b.get('byggeaar', '?')}, "
            f"BRA={b.get('bruksareal', '?')} m², Status={b.get('bygningstatus', '?')}"
            for b in bygninger[:5]
        )
    else:
        byg_tekst = "Ingen bygningsdata tilgjengelig."

    prompt = f"""Du er en norsk byggesaksekspert og arkitekt med inngående kunnskap om:
- Plan- og bygningsloven (PBL 2010)
- Byggteknisk forskrift TEK17 (og eldre TEK10/TEK97)
- Byggesaksforskriften SAK10
- SINTEF Byggforsk-veiledere (garasjer, bruksendring, grad av utnytting, ferdigattest, nabovarsel)
- Kommunal byggesaksbehandling og dispensasjonspraksis

Analyser følgende eiendom og gi en strukturert vurdering:

## Eiendom
- Adresse: {adresse}
- Kommune: {kommune} (kommunenr: {knr})
- Matrikkel: Gnr. {gnr}, Bnr. {bnr}
- Tomteareal: {eiendom.get('areal_m2', 'ukjent')} m²

## Bygninger
{byg_tekst}

## Byggesakshistorikk
{byggesak_tekst}

## Gjeldende arealplaner
{plan_tekst}

## Registrerte dispensasjoner
{disp_tekst}

## DOK-analyse (kartgrunnlag)
{dok_tekst}

{'## Feilmeldinger fra datakilder' + chr(10) + chr(10).join(feilmeldinger) if feilmeldinger else ''}

---

Referér til spesifikke paragrafer (f.eks. PBL § 20-1, TEK17 § 12-2) når du identifiserer avvik. Bruk paragrafkoden i nøkkelfinninger og anbefalinger.

Gi en komplett analyse i følgende JSON-format. Svar BARE med gyldig JSON, ingen annen tekst:

{{
  "risiko_nivaa": "LAV|MIDDELS|HØY|KRITISK",
  "risiko_score": 0.0,
  "sammendrag": "Norsk sammendrag på 2-3 setninger",
  "nøkkelfinninger": [
    "Funn 1",
    "Funn 2"
  ],
  "anbefalinger": [
    "Anbefaling 1",
    "Anbefaling 2"
  ],
  "avviksvurdering": "Vurdering av potensielle avvik mellom godkjente tegninger og faktisk tilstand",
  "dispensasjonsgrunnlag": "Vurdering av dispensasjonssituasjonen",
  "reguleringsplan_vurdering": "Vurdering av reguleringsplan og tillatt arealbruk",
  "dok_analyse_vurdering": "Vurdering av DOK-analyse-funn og risiko",
  "paragraf_referanser": ["PBL-20-1", "TEK17-12-2"]
}}

Fokus på:
1. Identifiser potensielle ulovlige byggearbeider basert på byggesakshistorikken
2. Vurder samsvar mellom registrert og faktisk bygningstype/areal
3. Identifiser dispensasjonsrisiko
4. Pek på mangler i dokumentasjon
5. Gi konkrete anbefalinger til arkitekt om hva som bør undersøkes nærmere

Risikonivå-definisjon:
- LAV: Ingen åpenbare avvik eller risikofaktorer
- MIDDELS: Noen forhold som bør undersøkes
- HØY: Mulige ulovlige tiltak eller vesentlige avvik
- KRITISK: Alvorlige byggesaksbrudd eller sikkerhetsmessige forhold"""

    # Legg til relevant regelverk
    try:
        from services.regulations.regelverk import bygg_regelverk_kontekst
        regelverk_tekst = bygg_regelverk_kontekst()  # inkluder standard utvalg
        prompt += f"\n\n{regelverk_tekst}"
    except Exception:
        pass

    return prompt


# ---------------------------------------------------------------------------
# Analyzer klasse
# ---------------------------------------------------------------------------


class PropertyIntelligenceAnalyzer:
    """
    AI-drevet eiendomsanalyse for ByggSjekk / nops.no.

    Bruker konfigurert LLM-leverandør (Anthropic eller OpenAI) til å analysere
    all tilgjengelig eiendomsdata og generere en strukturert rapport.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        anthropic_api_key: str = "",
        openai_api_key: str = "",
        anthropic_model: str = "claude-sonnet-4-6",
        openai_model: str = "gpt-4o",
    ):
        self.provider = provider
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.anthropic_model = anthropic_model
        self.openai_model = openai_model

    async def analyser_eiendom(
        self,
        eiendom_data: dict[str, Any],
    ) -> PropertyAnalysisResult:
        """
        Analyserer en eiendom basert på alle tilgjengelige data.

        Args:
            eiendom_data: Full eiendomsdata fra /property/full endepunktet

        Returns:
            PropertyAnalysisResult med komplett AI-analyse
        """
        knr = eiendom_data.get("kommunenummer", "")
        gnr = eiendom_data.get("gnr", "")
        bnr = eiendom_data.get("bnr", "")
        eiendom_id = f"{knr}/{gnr}/{bnr}"

        prompt = _bygg_analyse_prompt(eiendom_data)

        try:
            if self.provider == "anthropic":
                result_json = await self._kall_anthropic(prompt)
                model_used = self.anthropic_model
            else:
                result_json = await self._kall_openai(prompt)
                model_used = self.openai_model

            return PropertyAnalysisResult(
                eiendom_id=eiendom_id,
                risiko_nivaa=result_json.get("risiko_nivaa", "MIDDELS"),
                risiko_score=float(result_json.get("risiko_score", 0.5)),
                sammendrag=result_json.get("sammendrag", ""),
                nøkkelfinninger=result_json.get("nøkkelfinninger", []),
                anbefalinger=result_json.get("anbefalinger", []),
                avviksvurdering=result_json.get("avviksvurdering", ""),
                dispensasjonsgrunnlag=result_json.get("dispensasjonsgrunnlag", ""),
                reguleringsplan_vurdering=result_json.get("reguleringsplan_vurdering", ""),
                dok_analyse_vurdering=result_json.get("dok_analyse_vurdering", ""),
                kilde_data={
                    "kommunenummer": knr,
                    "gnr": gnr,
                    "bnr": bnr,
                },
                model_used=model_used,
            )

        except Exception as e:
            logger.error("AI-analyse feilet: %s", e)
            # Returner en fallback-analyse basert på data
            return self._regel_basert_fallback(eiendom_id, eiendom_data)

    async def _kall_anthropic(self, prompt: str) -> dict[str, Any]:
        """Kaller Anthropic Claude API."""
        import anthropic
        import json

        client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
        response = await client.messages.create(
            model=self.anthropic_model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Fjern markdown-kodeblokker hvis present
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0].strip()
        return json.loads(text)

    async def _kall_openai(self, prompt: str) -> dict[str, Any]:
        """Kaller OpenAI API."""
        import openai
        import json

        client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        response = await client.chat.completions.create(
            model=self.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=2048,
        )
        return json.loads(response.choices[0].message.content)

    def _regel_basert_fallback(
        self,
        eiendom_id: str,
        eiendom_data: dict[str, Any],
    ) -> PropertyAnalysisResult:
        """Regelbasert fallback-analyse når LLM ikke er tilgjengelig."""
        byggesaker = eiendom_data.get("byggesaker", [])
        dok = eiendom_data.get("dok_analyse") or {}
        dispenser = (eiendom_data.get("planrapport") or {}).get("dispensasjoner", [])

        # Enkel risikovurdering
        risiko_score = 0.2
        nøkkelfinninger = []
        anbefalinger = []

        if not byggesaker:
            nøkkelfinninger.append("Ingen byggesakshistorikk funnet i offentlige registre")
            anbefalinger.append("Innhent komplett byggesakshistorikk fra kommunen manuelt")
            risiko_score += 0.2

        if dispenser:
            nøkkelfinninger.append(f"{len(dispenser)} dispensasjon(er) registrert")
            anbefalinger.append("Gjennomgå dispensasjonshistorikken nøye")
            risiko_score += 0.1 * len(dispenser)

        berørt = len(dok.get("berørte_datasett", []))
        if berørt > 3:
            nøkkelfinninger.append(f"DOK-analyse: {berørt} berørte datasett")
            anbefalinger.append("Vurder risiko knyttet til DOK-berørthet")
            risiko_score += 0.15

        risiko_score = min(1.0, risiko_score)

        if risiko_score < 0.3:
            risiko_nivaa = "LAV"
        elif risiko_score < 0.5:
            risiko_nivaa = "MIDDELS"
        elif risiko_score < 0.75:
            risiko_nivaa = "HØY"
        else:
            risiko_nivaa = "KRITISK"

        return PropertyAnalysisResult(
            eiendom_id=eiendom_id,
            risiko_nivaa=risiko_nivaa,
            risiko_score=round(risiko_score, 2),
            sammendrag=(
                f"Regelbasert analyse (AI ikke tilgjengelig). "
                f"Risikonivå: {risiko_nivaa}. "
                f"Funnet {len(byggesaker)} byggesaker og {len(dispenser)} dispensasjoner."
            ),
            nøkkelfinninger=nøkkelfinninger,
            anbefalinger=anbefalinger or ["Innhent tegninger og gjennomfør manuell kontroll"],
            kilde_data={"kommunenummer": eiendom_data.get("kommunenummer")},
            model_used="regelbasert-fallback",
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_analyzer_instance: PropertyIntelligenceAnalyzer | None = None


def get_property_analyzer() -> PropertyIntelligenceAnalyzer:
    """Returnerer en konfigurert PropertyIntelligenceAnalyzer-instans."""
    global _analyzer_instance
    if _analyzer_instance is None:
        try:
            from app.core.config import settings
            _analyzer_instance = PropertyIntelligenceAnalyzer(
                provider=settings.LLM_PROVIDER,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                openai_api_key=settings.OPENAI_API_KEY,
                anthropic_model=settings.ANTHROPIC_MODEL,
                openai_model=settings.OPENAI_MODEL,
            )
        except ImportError:
            # Brukes utenfor API-kontekst
            _analyzer_instance = PropertyIntelligenceAnalyzer()
    return _analyzer_instance
