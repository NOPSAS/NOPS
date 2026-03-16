"""
services/reporting/generator.py

Rapportgenerator for ByggSjekk.

Genererer to rapporttyper:
  1. Intern arkitektrapport: full detaljeringsgrad med confidence-scorer og evidens
  2. Kunderapport: høynivå-sammendrag uten juridisk terminologi

Begge rapporter inkluderer tydelig ansvarsfraskrivelse:
  Arkitekten er alltid siste kontrollinstans. Rapporten er beslutningsstøtte,
  ikke en juridisk vurdering.

Bruk:
    generator = ReportGenerator()
    internal = generator.generate_internal_report(case, deviations, rule_matches)
    customer = generator.generate_customer_report(case, deviations)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# =============================================================================
# Konstanter
# =============================================================================

DISCLAIMER_INTERNAL = (
    "VIKTIG: Denne rapporten er generert av ByggSjekk som et beslutningsstøtteverktøy. "
    "Alle vurderinger er basert på AI-analyse og regelmatching med tilhørende confidence-skorer. "
    "Arkitekten er alltid siste kontrollinstans og må verifisere alle funn før konklusjoner trekkes. "
    "Rapporten er ikke en juridisk vurdering og kan ikke brukes som grunnlag for søknader "
    "uten faglig gjennomgang av ansvarlig arkitekt."
)

DISCLAIMER_CUSTOMER = (
    "Denne rapporten er generert av ByggSjekk som et beslutningsstøtteverktøy for arkitekter. "
    "Rapporten er ikke en juridisk vurdering. Alle funn er potensielle avvik som må vurderes "
    "av ansvarlig arkitekt. Kontakt din arkitekt for faglig rådgivning om konkrete tiltak."
)

SEVERITY_LABELS_NO = {
    "CRITICAL": "Kritisk",
    "HIGH": "Høy",
    "MEDIUM": "Middels",
    "LOW": "Lav",
    "INFORMATIONAL": "Informasjon",
}

CATEGORY_LABELS_NO = {
    "ROOM_DEFINITION_CHANGE": "Romdefinisjonsendring",
    "BEDROOM_UTILITY_DISCREPANCY": "Soverom / bruksromsavvik",
    "DOOR_PLACEMENT_CHANGE": "Endret dørplassering",
    "WINDOW_PLACEMENT_CHANGE": "Endret vindusplassering",
    "BALCONY_TERRACE_DISCREPANCY": "Balkong / terrasseavvik",
    "ADDITION_DETECTED": "Tilbygg oppdaget",
    "UNDERBUILDING_DETECTED": "Underbygging oppdaget",
    "UNINSPECTED_AREA": "Udokumentert areal",
    "USE_CHANGE_INDICATION": "Bruksendring indikert",
    "MARKETED_FUNCTION_DISCREPANCY": "Markedsfort funksjon avviker",
}

STATUS_LABELS_NO = {
    "PENDING_REVIEW": "Venter på gjennomgang",
    "UNDER_REVIEW": "Under gjennomgang",
    "CONFIRMED": "Bekreftet",
    "DISMISSED": "Avvist",
    "DISPENSATION_APPLIED": "Dispensasjon søkt",
    "RESOLVED": "Løst",
}


# =============================================================================
# Hjelpefunksjoner
# =============================================================================

def _confidence_label(score: float) -> str:
    """Konverter confidence-score til lesbar etikett."""
    if score >= 0.90:
        return "Svært høy"
    elif score >= 0.75:
        return "Høy"
    elif score >= 0.55:
        return "Middels"
    elif score >= 0.35:
        return "Lav"
    else:
        return "Svært lav"


def _format_date(dt: datetime | str | None) -> str | None:
    """Formater dato til norsk datoformat."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.strftime("%d.%m.%Y")


def _severity_sort_key(deviation: dict[str, Any]) -> int:
    """Sorteringsnøkkel for alvorlighetsgrad (høyest først)."""
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFORMATIONAL": 4}
    return order.get(deviation.get("severity", "LOW"), 99)


# =============================================================================
# Rapportgenerator
# =============================================================================

class ReportGenerator:
    """
    Genererer strukturerte rapporter (JSONB-kompatibelt format) for ByggSjekk-saker.

    Rapportene lagres i databasen som JSONB og kan eksporteres til PDF via
    en separat PDF-renderer (f.eks. WeasyPrint eller Playwright).
    """

    def generate_internal_report(
        self,
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
        rule_matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generer intern arkitektrapport med full detaljeringsgrad.

        Inkluderer:
          - Alle avvik med confidence-scorer og AI-evidens
          - Regelreferanser (TEK17, PBL, SAK10) per avvik
          - Statistikk og sammendrag
          - Tydelig ansvarsfraskrivelse

        Args:
            case:         Sak-dict med metadata
            deviations:   Liste med avvik-dicts
            rule_matches: Liste med regeltreff-dicts

        Returns:
            Dict med komplett rapportinnhold (JSONB-klart).
        """
        sorted_devs = sorted(deviations, key=_severity_sort_key)

        # Bygg regeltreff-oppslag: deviation_id -> [rule_matches]
        rule_match_by_dev: dict[str, list[dict]] = {}
        for rm in rule_matches:
            dev_id = rm.get("deviation_id")
            if dev_id:
                rule_match_by_dev.setdefault(dev_id, []).append(rm)

        deviation_entries = []
        for dev in sorted_devs:
            dev_id = dev.get("id", "")
            matches = rule_match_by_dev.get(dev_id, [])
            deviation_entries.append(
                self._build_internal_deviation_entry(dev, matches)
            )

        # Statistikk
        severity_counts: dict[str, int] = {}
        for dev in deviations:
            sev = dev.get("severity", "UNKNOWN")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        avg_confidence = (
            sum(d.get("confidence_score", 0) for d in deviations) / len(deviations)
            if deviations else 0.0
        )

        return {
            "report_type": "INTERNAL",
            "report_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "case": {
                "id": case.get("id"),
                "case_number": case.get("case_number"),
                "title": case.get("title"),
                "status": case.get("status"),
                "assigned_architect": case.get("assigned_architect"),
                "created_at": _format_date(case.get("created_at")),
            },
            "disclaimer": DISCLAIMER_INTERNAL,
            "summary": {
                "total_deviations": len(deviations),
                "by_severity": {
                    SEVERITY_LABELS_NO.get(k, k): v
                    for k, v in severity_counts.items()
                },
                "average_confidence": round(avg_confidence, 3),
                "average_confidence_label": _confidence_label(avg_confidence),
                "total_rule_matches": len(rule_matches),
                "deviations_confirmed": sum(
                    1 for d in deviations if d.get("status") == "CONFIRMED"
                ),
                "deviations_pending": sum(
                    1 for d in deviations if d.get("status") == "PENDING_REVIEW"
                ),
            },
            "deviations": deviation_entries,
            "methodology": {
                "description": (
                    "Avvik er oppdaget ved AI-basert sammenligning av godkjent tegning og "
                    "dagens plantegning. Confidence-score angir systemets sikkerhet på at "
                    "funnet er et reelt avvik. Score > 0.85 ansees som høy sikkerhet."
                ),
                "ai_models_used": list({
                    d.get("ai_model") for d in deviations if d.get("ai_model")
                }),
                "rule_sources": ["TEK17", "PBL 2008", "SAK10"],
            },
        }

    def generate_customer_report(
        self,
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generer kunderapport med høynivå-sammendrag.

        Inkluderer:
          - Oversikt over potensielle avvik (uten juridisk terminologi)
          - Anbefalte neste steg
          - Tydelig ansvarsfraskrivelse

        Args:
            case:       Sak-dict med metadata
            deviations: Liste med avvik-dicts

        Returns:
            Dict med komplett kunderapportinnhold (JSONB-klart).
        """
        sorted_devs = sorted(deviations, key=_severity_sort_key)

        deviation_entries = [
            self._build_customer_deviation_entry(dev) for dev in sorted_devs
        ]

        high_or_critical = [
            d for d in deviations
            if d.get("severity") in ("HIGH", "CRITICAL")
        ]

        return {
            "report_type": "CUSTOMER",
            "report_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "case": {
                "case_number": case.get("case_number"),
                "title": case.get("title"),
                "created_at": _format_date(case.get("created_at")),
            },
            "disclaimer": DISCLAIMER_CUSTOMER,
            "summary": {
                "ingress": (
                    f"Gjennomgangen avdekket {len(deviations)} potensielle avvik mellom "
                    "godkjente tegninger og dagens plantegning. "
                    f"Av disse er {len(high_or_critical)} vurdert som høy eller kritisk prioritet "
                    "og anbefales gjennomgått av arkitekt."
                ),
                "total_observations": len(deviations),
                "high_priority_count": len(high_or_critical),
            },
            "observations": deviation_entries,
            "next_steps": self._generate_next_steps(deviations),
            "contact": {
                "message": (
                    "Ta kontakt med din ansvarlige arkitekt for å diskutere funnene i denne rapporten. "
                    "Arkitekten kan gi deg konkrete råd om hvilke tiltak som eventuelt må iverksettes."
                ),
            },
        }

    # -------------------------------------------------------------------------
    # Private hjelpemetoder
    # -------------------------------------------------------------------------

    def _build_internal_deviation_entry(
        self,
        deviation: dict[str, Any],
        rule_matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Bygg detaljert avvikspost for intern rapport."""
        return {
            "id": deviation.get("id"),
            "deviation_number": deviation.get("deviation_number"),
            "category": CATEGORY_LABELS_NO.get(
                deviation.get("category", ""), deviation.get("category")
            ),
            "category_code": deviation.get("category"),
            "severity": SEVERITY_LABELS_NO.get(
                deviation.get("severity", ""), deviation.get("severity")
            ),
            "severity_code": deviation.get("severity"),
            "status": STATUS_LABELS_NO.get(
                deviation.get("status", ""), deviation.get("status")
            ),
            "title": deviation.get("title"),
            "description": deviation.get("description"),
            "confidence_score": deviation.get("confidence_score"),
            "confidence_label": _confidence_label(deviation.get("confidence_score", 0)),
            "ai_model": deviation.get("ai_model"),
            "ai_model_version": deviation.get("ai_model_version"),
            "evidence": deviation.get("evidence", {}),
            "affected_rooms": deviation.get("affected_room_ids", []),
            "architect_note": deviation.get("architect_note"),
            "rule_matches": [
                {
                    "rule_id": rm.get("rule_id"),
                    "match_confidence": rm.get("match_confidence"),
                    "match_reason": rm.get("match_reason"),
                }
                for rm in rule_matches
            ],
        }

    def _build_customer_deviation_entry(
        self,
        deviation: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Bygg forenklet avvikspost for kunderapport.

        Unngår juridisk terminologi og viser ikke råe confidence-scorer.
        """
        severity = deviation.get("severity", "LOW")
        priority_map = {
            "CRITICAL": "Høy prioritet",
            "HIGH": "Høy prioritet",
            "MEDIUM": "Middels prioritet",
            "LOW": "Lav prioritet",
            "INFORMATIONAL": "Informasjon",
        }

        return {
            "deviation_number": deviation.get("deviation_number"),
            "category": CATEGORY_LABELS_NO.get(
                deviation.get("category", ""), deviation.get("category")
            ),
            "priority": priority_map.get(severity, "Ukjent"),
            "title": deviation.get("title"),
            "summary": self._customer_friendly_description(deviation),
            "recommended_action": self._recommended_action(deviation),
        }

    def _customer_friendly_description(self, deviation: dict[str, Any]) -> str:
        """
        Konverter teknisk avviksbeskrivelse til kundervennlig tekst.

        Unngår ordene "ulovlig", "søknadspliktig", "godkjent" som endelige konklusjoner.
        """
        category = deviation.get("category", "")
        title = deviation.get("title", "")

        prefixes = {
            "ADDITION_DETECTED": "Det er oppdaget et område som ikke er tegnet inn i de dokumenterte planene: ",
            "BEDROOM_UTILITY_DISCREPANCY": "Et rom ser ut til å ha endret bruk siden tegningene ble laget: ",
            "BALCONY_TERRACE_DISCREPANCY": "Det er en forskjell i balkong- eller terrassetegningene: ",
            "ROOM_DEFINITION_CHANGE": "Et rom kan ha fått endret sin definisjon eller bruk: ",
            "USE_CHANGE_INDICATION": "Det er indikasjoner på at bruken av et område kan ha endret seg: ",
        }

        prefix = prefixes.get(category, "Et potensielt avvik er oppdaget: ")
        return f"{prefix}{title}. En arkitekt bør vurdere dette nærmere."

    def _recommended_action(self, deviation: dict[str, Any]) -> str:
        """Generer anbefalt handlingstekst basert på kategori og alvorlighetsgrad."""
        severity = deviation.get("severity", "LOW")
        category = deviation.get("category", "")

        if severity in ("CRITICAL", "HIGH"):
            if category in ("ADDITION_DETECTED", "UNDERBUILDING_DETECTED"):
                return (
                    "Be ansvarlig arkitekt om å vurdere om tiltaket er dokumentert. "
                    "Det kan være nødvendig å kontakte kommunen for avklaring."
                )
            return (
                "Prioriter en gjennomgang med ansvarlig arkitekt. "
                "Arkitekten vil vurdere om ytterligere dokumentasjon er nødvendig."
            )
        elif severity == "MEDIUM":
            return (
                "Arkitekten bør gjennomgå dette funnet og vurdere om det krever oppfølging."
            )
        else:
            return "Dette funnet er registrert for informasjon. Arkitekten vurderer om det krever tiltak."

    def _generate_next_steps(self, deviations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generer prioritert liste over anbefalte neste steg."""
        steps = []

        has_critical = any(d.get("severity") == "CRITICAL" for d in deviations)
        has_high = any(d.get("severity") == "HIGH" for d in deviations)
        has_additions = any(d.get("category") == "ADDITION_DETECTED" for d in deviations)

        if has_critical:
            steps.append({
                "priority": 1,
                "action": "Kontakt ansvarlig arkitekt umiddelbart",
                "reason": "Det er oppdaget funn med høy prioritet som bør vurderes raskt.",
            })

        if has_high or has_additions:
            steps.append({
                "priority": 2,
                "action": "Book gjennomgang med arkitekt",
                "reason": "Arkitekten kan avklare om det er behov for kontakt med kommunen.",
            })

        steps.append({
            "priority": len(steps) + 1,
            "action": "Samle relevant dokumentasjon",
            "reason": (
                "Finn frem kjøpsdokumenter, tegninger og eventuelle tillatelser du har tilgang til. "
                "Dette hjelper arkitekten med gjennomgangen."
            ),
        })

        return steps


# =============================================================================
# Dataklasse for rapportresultat
# =============================================================================

from dataclasses import dataclass, field as _field


@dataclass
class ReportData:
    """Strukturert rapportresultat med innhold og markdown-tekst."""
    report_type: str
    content: dict[str, Any]
    markdown: str
    generated_at: str = _field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    case_id: str | None = None
    version: int = 1


# =============================================================================
# Async norsk rapportgenerator
# =============================================================================

DISCLAIMER_MUNICIPALITY = (
    "VIKTIG: Denne rapporten er generert av ByggSjekk som et beslutningsstøtteverktøy. "
    "Alle funn er potensielle avvik som må vurderes og bekreftes av ansvarlig arkitekt "
    "og eventuelt kommunens byggesaksbehandler. "
    "Rapporten er ikke en søknad om dispensasjon og heller ikke en juridisk vurdering."
)


class NorwegianReportGenerator:
    """
    Asynkron rapportgenerator med norskspråklige rapporter for ByggSjekk.

    Genererer tre rapporttyper:
      1. intern_rapport   – full detaljeringsgrad for arkitekt
      2. kunderapport     – høynivå uten juridisk terminologi
      3. kommunerapport   – strukturert for innsending til kommunen

    Bruker forsiktig norsk språk:
      - "potensielt avvik" fremfor "avvik" som faktum
      - "bør vurderes" fremfor "må behandles"
      - ALDRI "ulovlig", "godkjent" (som endelig konklusjon), "krever søknad" kategorisk
    """

    def __init__(self, nops_base_url: str | None = None) -> None:
        self._nops_base_url = nops_base_url or "https://nops.no"
        self._sync_generator = ReportGenerator()

    async def generate_internal_report(
        self,
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
        rules: list[dict[str, Any]],
    ) -> ReportData:
        """
        Generer intern arkitektrapport med full detaljeringsgrad.

        Inkluderer confidence-scorer, regelreferanser og evidens per avvik.
        Bruker forsiktig norsk fagspråk.

        Args:
            case:       Sak-dict med metadata (id, title, status, assigned_architect osv.)
            deviations: Liste med avvik
            rules:      Liste med regeltreff

        Returns:
            ReportData med strukturert innhold og markdown-tekst.
        """
        content = self._sync_generator.generate_internal_report(case, deviations, rules)
        markdown = self._render_internal_markdown(content, case, deviations)

        return ReportData(
            report_type="INTERNAL",
            content=content,
            markdown=markdown,
            case_id=str(case.get("id", "")),
        )

    async def generate_customer_report(
        self,
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
    ) -> ReportData:
        """
        Generer kunderapport med høynivå-sammendrag.

        Unngår juridisk terminologi. Bruker tilgjengelig, forklarende språk.

        Args:
            case:       Sak-dict med metadata
            deviations: Liste med avvik

        Returns:
            ReportData med strukturert innhold og markdown-tekst.
        """
        content = self._sync_generator.generate_customer_report(case, deviations)
        markdown = self._render_customer_markdown(content, case, deviations)

        return ReportData(
            report_type="CUSTOMER",
            content=content,
            markdown=markdown,
            case_id=str(case.get("id", "")),
        )

    async def generate_municipality_report(
        self,
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
        dispensations: list[dict[str, Any]],
    ) -> ReportData:
        """
        Generer kommunerapport med relevante funn og dispensasjonsvurderinger.

        Rapporten er strukturert for potensielt å vedlegges kommunikasjonsdrafter
        til kommunens byggesaksavdeling. Arkitekten må alltid gjennomgå og godkjenne
        rapporten før den sendes til kommunen.

        Args:
            case:          Sak-dict med metadata
            deviations:    Liste med avvik
            dispensations: Liste med dispensasjonsvurderinger

        Returns:
            ReportData med strukturert innhold og markdown-tekst.
        """
        sorted_devs = sorted(deviations, key=_severity_sort_key)

        high_priority = [
            d for d in sorted_devs
            if d.get("severity") in ("CRITICAL", "HIGH")
        ]
        dispensation_candidates = [
            d for d in sorted_devs
            if d.get("severity") in ("MEDIUM", "HIGH", "CRITICAL")
        ]

        content: dict[str, Any] = {
            "report_type": "MUNICIPALITY",
            "report_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": DISCLAIMER_MUNICIPALITY,
            "case": {
                "id": case.get("id"),
                "case_number": case.get("case_number"),
                "title": case.get("title"),
                "property": case.get("property", {}),
            },
            "summary": {
                "total_observations": len(deviations),
                "high_priority_count": len(high_priority),
                "dispensation_candidates": len(dispensation_candidates),
                "ingress": (
                    f"ByggSjekk har gjennomgått {len(deviations)} potensielle avvik mellom "
                    "godkjente tegninger og dagens plantegning for denne eiendommen. "
                    f"Av disse er {len(high_priority)} vurdert som høy eller kritisk prioritet. "
                    "Alle funn er potensielle og må bekreftes ved befaring og faglig vurdering."
                ),
            },
            "observations": [
                self._build_municipality_observation(d)
                for d in dispensation_candidates
            ],
            "dispensations": [
                self._build_dispensation_entry(d)
                for d in dispensations
            ],
            "request": {
                "type": "INFORMASJONSFORESPØRSEL",
                "description": (
                    "Vi ber om kommunens arkiverte byggesaksopplysninger, "
                    "godkjente tegninger og eventuelle eksisterende dispensasjoner "
                    "knyttet til eiendommen, for bruk i den videre vurderingen."
                ),
            },
            "nops_reference": f"{self._nops_base_url}/case/{case.get('id', '')}",
        }

        markdown = self._render_municipality_markdown(content, case, deviations, dispensations)

        return ReportData(
            report_type="MUNICIPALITY",
            content=content,
            markdown=markdown,
            case_id=str(case.get("id", "")),
        )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _build_municipality_observation(self, deviation: dict[str, Any]) -> dict[str, Any]:
        """Bygg observasjonspost for kommunerapport."""
        severity = deviation.get("severity", "LOW")
        return {
            "id": deviation.get("id"),
            "category": CATEGORY_LABELS_NO.get(
                deviation.get("category", ""), deviation.get("category")
            ),
            "severity": SEVERITY_LABELS_NO.get(severity, severity),
            "description": deviation.get("description", ""),
            "confidence": deviation.get("confidence_score", 0),
            "note": (
                "Potensielt avvik – krever befaring og faglig vurdering av "
                "ansvarlig arkitekt og eventuelt kommunens byggesaksbehandler."
            ),
        }

    def _build_dispensation_entry(self, disp: dict[str, Any]) -> dict[str, Any]:
        """Bygg dispensasjonspost for kommunerapport."""
        return {
            "id": disp.get("id"),
            "deviation_ref": disp.get("deviation_id"),
            "description": disp.get("description", ""),
            "legal_basis": disp.get("legal_basis", "PBL § 19-2"),
            "likelihood_score": disp.get("likelihood_score"),
            "recommendation": disp.get("recommendation", ""),
            "note": "Dispensasjonsvurderingen er kun veiledende og basert på AI-analyse.",
        }

    def _render_internal_markdown(
        self,
        content: dict[str, Any],
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
    ) -> str:
        """Generer markdown-tekst for intern arkitektrapport."""
        lines = [
            f"# Intern ByggSjekk-rapport",
            f"",
            f"**Sak:** {case.get('title', 'Ukjent')}  ",
            f"**Generert:** {_format_date(content.get('generated_at'))}  ",
            f"**Antall avvik:** {len(deviations)}  ",
            f"",
            f"---",
            f"",
            f"**{DISCLAIMER_INTERNAL}**",
            f"",
            f"---",
            f"",
            f"## Sammendrag",
            f"",
        ]

        summary = content.get("summary", {})
        lines += [
            f"- Totale avvik: **{summary.get('total_deviations', 0)}**",
            f"- Gjennomsnittlig konfidens: **{summary.get('average_confidence_label', 'Ukjent')}** "
            f"({round(summary.get('average_confidence', 0) * 100)}%)",
            f"- Bekreftet: {summary.get('deviations_confirmed', 0)}",
            f"- Venter på gjennomgang: {summary.get('deviations_pending', 0)}",
            f"",
            f"### Fordeling etter alvorlighet",
            f"",
        ]

        by_severity = summary.get("by_severity", {})
        for sev_label, count in by_severity.items():
            lines.append(f"- {sev_label}: **{count}**")

        lines += [
            f"",
            f"---",
            f"",
            f"## Avviksliste",
            f"",
        ]

        for dev in content.get("deviations", []):
            lines += [
                f"### {dev.get('deviation_number', '—')} – {dev.get('title', dev.get('category', ''))}",
                f"",
                f"- **Kategori:** {dev.get('category', '—')}",
                f"- **Alvorlighet:** {dev.get('severity', '—')}",
                f"- **Status:** {dev.get('status', '—')}",
                f"- **Konfidens:** {dev.get('confidence_label', '—')} ({round((dev.get('confidence_score') or 0) * 100)}%)",
                f"",
                f"{dev.get('description', '')}",
                f"",
            ]
            if dev.get("architect_note"):
                lines.append(f"*Arkitektnotat: {dev['architect_note']}*")
                lines.append(f"")

        return "\n".join(lines)

    def _render_customer_markdown(
        self,
        content: dict[str, Any],
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
    ) -> str:
        """Generer markdown-tekst for kunderapport."""
        lines = [
            f"# ByggSjekk – Eiendomsgjennomgang",
            f"",
            f"**Eiendommen:** {case.get('title', '')}  ",
            f"**Generert:** {_format_date(content.get('generated_at'))}  ",
            f"",
            f"---",
            f"",
            f"*{DISCLAIMER_CUSTOMER}*",
            f"",
            f"---",
            f"",
            f"## Oversikt",
            f"",
        ]

        summary = content.get("summary", {})
        lines.append(f"{summary.get('ingress', '')}")
        lines.append(f"")

        lines += [
            f"---",
            f"",
            f"## Potensielle funn",
            f"",
        ]

        for obs in content.get("observations", []):
            priority = obs.get("priority", "")
            title = obs.get("title", "")
            summary_text = obs.get("summary", "")
            action = obs.get("recommended_action", "")
            lines += [
                f"### {obs.get('deviation_number', '—')} – {title}",
                f"",
                f"**Prioritet:** {priority}  ",
                f"**Kategori:** {obs.get('category', '—')}",
                f"",
                f"{summary_text}",
                f"",
                f"**Anbefalt tiltak:** {action}",
                f"",
            ]

        lines += [
            f"---",
            f"",
            f"## Neste steg",
            f"",
        ]

        for step in content.get("next_steps", []):
            lines.append(f"**{step.get('priority', '—')}.** {step.get('action', '')}  ")
            lines.append(f"   *{step.get('reason', '')}*")
            lines.append(f"")

        return "\n".join(lines)

    def _render_municipality_markdown(
        self,
        content: dict[str, Any],
        case: dict[str, Any],
        deviations: list[dict[str, Any]],
        dispensations: list[dict[str, Any]],
    ) -> str:
        """Generer markdown-tekst for kommunerapport."""
        prop = case.get("property", {})
        prop_str = (
            f"gnr. {prop.get('gnr', '—')}, bnr. {prop.get('bnr', '—')}, "
            f"{prop.get('municipality', '—')} kommune"
        )

        lines = [
            f"# ByggSjekk – Informasjon til kommunen",
            f"",
            f"**Eiendom:** {prop_str}  ",
            f"**Sak:** {case.get('title', '')}  ",
            f"**Generert:** {_format_date(content.get('generated_at'))}  ",
            f"",
            f"---",
            f"",
            f"*{DISCLAIMER_MUNICIPALITY}*",
            f"",
            f"---",
            f"",
            f"## Bakgrunn og forespørsel",
            f"",
            f"{content.get('summary', {}).get('ingress', '')}",
            f"",
            f"{content.get('request', {}).get('description', '')}",
            f"",
            f"---",
            f"",
            f"## Potensielle avvik til vurdering",
            f"",
        ]

        for obs in content.get("observations", []):
            lines += [
                f"- **{obs.get('category', '—')}** (alvorlighet: {obs.get('severity', '—')}): "
                f"{obs.get('description', '')}",
                f"  *{obs.get('note', '')}*",
                f"",
            ]

        if dispensations:
            lines += [
                f"---",
                f"",
                f"## Dispensasjonsvurderinger (veiledende)",
                f"",
            ]
            for d in dispensations:
                lines += [
                    f"- **Grunnlag:** {d.get('legal_basis', 'PBL § 19-2')}",
                    f"  {d.get('description', '')}",
                    f"  *{d.get('note', '')}*",
                    f"",
                ]

        return "\n".join(lines)
