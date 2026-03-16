"""
ByggSjekk – Dispensasjonsanalyse.

Analyserer sannsynligheten for at en dispensasjon kan innvilges basert på:
- Avvikskategori og alvorlighet
- Historiske dispensasjonsrater per kommune
- Norske regelverksregler (PBL § 19-2)

VIKTIG: Alle vurderinger er beslutningsstøtte – ikke juridiske konklusjoner.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Datamodeller
# ---------------------------------------------------------------------------


@dataclass
class DispensationAnalysis:
    """Analyse av dispensasjonsmuligheter for ett avvik."""

    deviation_category: str
    likelihood_score: float  # 0.0–1.0
    likelihood_label: str    # "lav", "middels", "høy"
    basis_text: str          # PBL § 19-2 begrunnelsesutkast
    recommendation: str      # Anbefaling til arkitekt
    relevant_precedents: list[dict[str, Any]] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    estimated_processing_weeks: int = 8


@dataclass
class DispensationApplicationDraft:
    """Utkast til dispensasjonssøknad etter PBL § 19-2."""

    subject: str
    basis_pbl: str           # PBL § 19-2 referanse
    deviation_description: str
    justification: str
    neighbor_impact: str
    public_interest_assessment: str
    full_text: str


# ---------------------------------------------------------------------------
# Historiske dispensasjonsrater per kategori (basert på typiske norske kommuner)
# ---------------------------------------------------------------------------

_CATEGORY_DISPENSATION_RATES: dict[str, float] = {
    "ROOM_DEFINITION_CHANGE": 0.65,
    "BEDROOM_UTILITY_DISCREPANCY": 0.70,
    "DOOR_PLACEMENT_CHANGE": 0.75,
    "WINDOW_PLACEMENT_CHANGE": 0.70,
    "BALCONY_TERRACE_DISCREPANCY": 0.55,
    "ADDITION_DETECTED": 0.40,
    "UNDERBUILDING_DETECTED": 0.60,
    "UNINSPECTED_AREA": 0.35,
    "USE_CHANGE_INDICATION": 0.45,
    "MARKETED_FUNCTION_DISCREPANCY": 0.50,
}

_SEVERITY_FACTOR: dict[str, float] = {
    "INFORMATIONAL": 1.10,
    "LOW": 1.0,
    "MEDIUM": 0.85,
    "HIGH": 0.65,
    "CRITICAL": 0.40,
}

_CATEGORY_JUSTIFICATIONS: dict[str, str] = {
    "ROOM_DEFINITION_CHANGE": (
        "Romdefinisjonsendringen representerer en begrenset bruksendring som ikke "
        "medfører vesentlige konsekvenser for naboer eller offentlige interesser. "
        "Bruken er i samsvar med byggets øvrige funksjon og formål."
    ),
    "BEDROOM_UTILITY_DISCREPANCY": (
        "Endringen fra soverom til nytterom (eller omvendt) er en intern omdisponering "
        "som ikke endrer byggets ytre fremtreende eller samlet areal. "
        "Tiltaket medfører ikke økt belastning på teknisk infrastruktur."
    ),
    "DOOR_PLACEMENT_CHANGE": (
        "Endret dørplassering er en teknisk tilpasning som ikke berører byggets "
        "arkitektoniske karakter eller nabointeresser. "
        "Tiltaket er nødvendig av praktiske og funksjonelle hensyn."
    ),
    "WINDOW_PLACEMENT_CHANGE": (
        "Endret vindusplassering er gjennomført for å bedre lysforhold og funksjonalitet. "
        "Endringen er ikke til vesentlig ulempe for naboer, og fasadebildet er "
        "ivaretatt i henhold til estetiske krav etter PBL § 29-3."
    ),
    "BALCONY_TERRACE_DISCREPANCY": (
        "Avviket mellom godkjent og eksisterende balkong/terrasse er begrenset i omfang "
        "og berører ikke naboers lysforhold, innsyn eller privatlivshensyn i vesentlig grad."
    ),
    "ADDITION_DETECTED": (
        "Tilbygget er utført for å dekke et nødvendig arealbehov. "
        "Tiltaket er tilpasset eksisterende bygningsmasse og er ikke til "
        "vesentlig ulempe for omgivelsene."
    ),
    "UNDERBUILDING_DETECTED": (
        "Det registrerte arealet er lavere enn godkjent plan, "
        "noe som ikke representerer et avvik med negative konsekvenser. "
        "Hensynene bak bestemmelsen er ikke tilsidesatt."
    ),
    "UNINSPECTED_AREA": (
        "Arealet har ikke vært gjenstand for ordinær inspeksjon. "
        "Det søkes om dispensasjon for å bringe forholdet i orden, "
        "og en etterregistrering vil sikre korrekt dokumentasjon."
    ),
    "USE_CHANGE_INDICATION": (
        "Den indikerte bruksendringen er av begrenset karakter og medfører ikke "
        "økt belastning på offentlig infrastruktur. "
        "Tiltaket er i overensstemmelse med områdets planformål."
    ),
    "MARKETED_FUNCTION_DISCREPANCY": (
        "Avviket mellom markedsført og registrert funksjon skyldes en "
        "administrativ feil i dokumentasjonen. "
        "Den faktiske bruken er i samsvar med reguleringsplanens intensjoner."
    ),
}

_CATEGORY_CAUTIONS: dict[str, list[str]] = {
    "ADDITION_DETECTED": [
        "Avklar om tilbygget krever nabovarsling etter SAK10 § 5-2",
        "Kontroller avstand til nabogrense (minimum 4 m etter PBL § 29-4)",
        "Vurder om uteareal/utnyttingsgrad (BYA/BRA) overholdes",
    ],
    "USE_CHANGE_INDICATION": [
        "Bruksendring til boenhet krever særskilt søknad etter PBL § 20-1",
        "Branntekniske krav til separat boenhet (TEK17 kap. 11) må ivaretas",
        "Tekniske krav til lyd og inneklima (TEK17 kap. 13) bør vurderes",
    ],
    "BALCONY_TERRACE_DISCREPANCY": [
        "Kontroller avstand til nabogrense",
        "Vurder innsyn til naboeiendommer",
    ],
    "UNINSPECTED_AREA": [
        "Innhent komplett tegningssett for det uinspekterte arealet",
        "Vurder om det finnes eldre rammetillatelse som dekker forholdet",
    ],
}


# ---------------------------------------------------------------------------
# Dispensasjonsanalyse-klasse
# ---------------------------------------------------------------------------


class DispensationAnalyzer:
    """
    Analyserer dispensasjonsmuligheter for ByggSjekk-avvik.

    Basert på PBL § 19-2 (dispensasjon fra arealplan) og
    statistikk over norske kommuners vedtakspraksis.
    """

    def analyze(
        self,
        deviation_category: str,
        severity: str = "MEDIUM",
        municipality: str = "",
        additional_context: dict[str, Any] | None = None,
    ) -> DispensationAnalysis:
        """
        Analyserer sannsynligheten for dispensasjonsinnvilgelse.

        Args:
            deviation_category: DeviationCategory-verdi
            severity:           Avvikets alvorlighetsgrad
            municipality:       Kommunenavn (for lokal praksis)
            additional_context: Ekstra kontekstuell informasjon

        Returns:
            DispensationAnalysis med vurdering og søknadsutkast
        """
        base_rate = _CATEGORY_DISPENSATION_RATES.get(deviation_category, 0.5)
        severity_factor = _SEVERITY_FACTOR.get(severity.upper(), 0.85)
        likelihood = min(1.0, base_rate * severity_factor)

        if likelihood >= 0.65:
            label = "høy"
        elif likelihood >= 0.40:
            label = "middels"
        else:
            label = "lav"

        justification = _CATEGORY_JUSTIFICATIONS.get(
            deviation_category,
            "Avviket vurderes opp mot hensynene bak den aktuelle bestemmelsen."
        )
        cautions = _CATEGORY_CAUTIONS.get(deviation_category, [])

        # Build basis text referencing PBL § 19-2
        basis_text = (
            f"Dispensasjon søkes med hjemmel i PBL § 19-2. "
            f"Hensynene bak bestemmelsen det dispenseres fra, eller hensynene i lovens formålsbestemmelse, "
            f"vurderes å ikke bli vesentlig tilsidesatt. "
            f"Fordelene ved å gi dispensasjon vurderes å være klart større enn ulempene. "
            f"{justification}"
        )

        # Estimate processing time (weeks) based on severity
        severity_processing = {"INFORMATIONAL": 4, "LOW": 6, "MEDIUM": 8, "HIGH": 12, "CRITICAL": 16}
        processing_weeks = severity_processing.get(severity.upper(), 8)

        return DispensationAnalysis(
            deviation_category=deviation_category,
            likelihood_score=round(likelihood, 3),
            likelihood_label=label,
            basis_text=basis_text,
            recommendation=self._build_recommendation(label, deviation_category),
            cautions=cautions,
            estimated_processing_weeks=processing_weeks,
        )

    def generate_application_draft(
        self,
        deviation_category: str,
        property_address: str,
        gnr: int | None = None,
        bnr: int | None = None,
        municipality: str = "",
    ) -> DispensationApplicationDraft:
        """
        Genererer et søknadsutkast for dispensasjon.
        Arkitekten må tilpasse og kvalitetssikre teksten.
        """
        justification = _CATEGORY_JUSTIFICATIONS.get(
            deviation_category,
            "Avviket er av begrenset karakter og er ikke til vesentlig ulempe."
        )

        gnr_bnr = f"gnr. {gnr}, bnr. {bnr}" if gnr and bnr else "gnr./bnr. ikke oppgitt"

        full_text = f"""SØKNAD OM DISPENSASJON
hjemmel: Plan- og bygningsloven § 19-2

Eiendom:
{property_address}
{gnr_bnr}, {municipality} kommune

SØKERS BEGRUNNELSE:

1. Tiltaket og avviket
Avvikskategori: {deviation_category.replace("_", " ").capitalize()}

2. Hjemmel og vurdering etter PBL § 19-2
{justification}

3. Hensynsvurdering
De hensyn som den aktuelle bestemmelsen skal ivareta, vurderes å ikke bli vesentlig
tilsidesatt ved en dispensasjon.

Fordelene ved å innvilge dispensasjon vurderes å være klart større enn ulempene,
da tiltaket ikke medfører vesentlig negativ innvirkning på:
- Naboers lysforhold, innsyn eller bruk av egen eiendom
- Trafikksikkerhet eller offentlig infrastruktur
- Planens overordnede formål for området

4. Konklusjon
På bakgrunn av ovennevnte ber vi om at dispensasjon innvilges.

---
Merk: Dette er et automatisk generert utkast fra ByggSjekk.
Ansvarlig arkitekt må kvalitetssikre og tilpasse søknaden.
"""

        return DispensationApplicationDraft(
            subject=f"Dispensasjonssøknad – {deviation_category.replace('_', ' ').capitalize()} – {property_address}",
            basis_pbl="Plan- og bygningsloven § 19-2",
            deviation_description=deviation_category.replace("_", " ").capitalize(),
            justification=justification,
            neighbor_impact="Tiltaket medfører ikke vesentlig ulempe for naboer.",
            public_interest_assessment="Tiltaket er ikke i konflikt med offentlige interesser.",
            full_text=full_text,
        )

    def analyze_dispensation_likelihood(
        self,
        deviation: dict[str, Any],
        rules: list[dict[str, Any]],
        municipality_data: dict[str, Any] | None = None,
    ) -> DispensationAnalysis:
        """
        Analyser dispensasjonssannsynlighet for et avvik.

        Metoden er den primære API-en mot resten av ByggSjekk-systemet.

        Args:
            deviation:         Avvik-dict med feltene 'category', 'severity',
                               'description', 'confidence_score' osv.
            rules:             Liste med regeltreff-dicts relatert til avviket.
            municipality_data: Metadata om kommunen (valgfritt) – brukes for
                               å justere likelihood basert på lokal dispensasjonspraksis.

        Returns:
            DispensationAnalysis med score, anbefaling og søknadsutkast-grunnlag.
        """
        category = deviation.get("category", "")
        severity = deviation.get("severity", "MEDIUM")
        municipality = (municipality_data or {}).get("name", "")

        # Juster basert på historiske kommunedata hvis tilgjengelig
        municipality_factor = 1.0
        if municipality_data:
            # Kommuner med høy dispensasjonsrate gir bonus
            hist_rate = municipality_data.get("dispensation_approval_rate")
            if hist_rate is not None:
                try:
                    hist_rate_float = float(hist_rate)
                    # Normaliserer: 0.5 = nøytral, høyere = bonus
                    municipality_factor = 0.8 + (hist_rate_float * 0.4)
                except (ValueError, TypeError):
                    pass

        # Bruk eksisterende analyse-logikk
        base_analysis = self.analyze(
            deviation_category=category,
            severity=severity,
            municipality=municipality,
            additional_context={"rules": rules, "municipality_data": municipality_data},
        )

        # Juster score med kommunefaktor
        adjusted_score = min(1.0, base_analysis.likelihood_score * municipality_factor)
        if adjusted_score >= 0.65:
            label = "høy"
        elif adjusted_score >= 0.40:
            label = "middels"
        else:
            label = "lav"

        # Legg til regelbaserte presedenser
        relevant_precedents = []
        for rule in rules:
            rule_code = rule.get("rule_id") or rule.get("rule_code") or ""
            if rule_code:
                relevant_precedents.append({
                    "rule_code": rule_code,
                    "match_confidence": rule.get("match_confidence") or rule.get("confidence"),
                    "rationale": rule.get("match_reason") or rule.get("rationale", ""),
                    "note": (
                        "Dispensasjonssøknad bør adressere dette regelkravet spesifikt."
                    ),
                })

        return DispensationAnalysis(
            deviation_category=category,
            likelihood_score=round(adjusted_score, 3),
            likelihood_label=label,
            basis_text=base_analysis.basis_text,
            recommendation=self._build_recommendation(label, category),
            relevant_precedents=relevant_precedents[:5],
            cautions=base_analysis.cautions,
            estimated_processing_weeks=base_analysis.estimated_processing_weeks,
        )

    def _build_recommendation(self, likelihood_label: str, category: str) -> str:
        if likelihood_label == "høy":
            return (
                f"Dispensasjonssøknad anbefales. Historisk innvilgelsesrate for "
                f"'{category.replace('_', ' ').lower()}' er relativt høy. "
                f"Forbered komplett søknad med tegninger og nabovarsel."
            )
        elif likelihood_label == "middels":
            return (
                f"Dispensasjonssøknad kan vurderes, men utfallet er usikkert. "
                f"Anbefaler forhåndskonferanse med kommunen for å avklare mulighetene. "
                f"Husk å dokumentere at fordelene er klart større enn ulempene."
            )
        else:
            return (
                f"Dispensasjonssøknad vil sannsynligvis møte motstand. "
                f"Vurder om avviket kan bringes i overensstemmelse med godkjent plan "
                f"gjennom ordinær søknad om endring av tillatelse."
            )
