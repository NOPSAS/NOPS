"""
ByggSjekk – Rule registry and matching engine.

Provides:
  RuleRegistry   – load and retrieve Rule objects (in-memory seed data + DB)
  RuleMatcher    – find rules applicable to a DeviationResult
  RuleExplainer  – generate a human-readable explanation for a match
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from services.deviation_engine.engine import DeviationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight Rule dataclass (mirrors the ORM model's shape)
# ---------------------------------------------------------------------------


@dataclass
class Rule:
    rule_code: str
    title: str
    description: str
    legal_reference: str
    source: str          # "TEK17" | "PBL" | "SAK10"
    version: str
    applies_to_categories: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class RuleMatch:
    rule: Rule
    deviation: DeviationResult
    rationale: str
    confidence: float
    match_type: str  # "exact" | "category" | "heuristic"


# ---------------------------------------------------------------------------
# Seed rules (subset of TEK17 / PBL rules relevant to the deviation categories)
# ---------------------------------------------------------------------------

_SEED_RULES: list[Rule] = [
    Rule(
        rule_code="TEK17-8-1",
        title="Arealkrav til rom og rommets høyde",
        description=(
            "Rom for varig opphold skal ha et areal på minst 6 m² og takhøyde "
            "på minst 2,4 m. Romhøyden måles som fri høyde."
        ),
        legal_reference="TEK17 § 8-1",
        source="TEK17",
        version="2017",
        applies_to_categories=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED", "ROOM_DEFINITION_CHANGE"],
        parameters={"min_area_m2": 6.0, "min_ceiling_height_m": 2.4},
    ),
    Rule(
        rule_code="TEK17-8-2",
        title="Planløsning og rominndeling",
        description=(
            "Boenheten skal ha hensiktsmessig planløsning. Krav til soverom, "
            "stue, kjøkken og sanitærrom."
        ),
        legal_reference="TEK17 § 8-2",
        source="TEK17",
        version="2017",
        applies_to_categories=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED", "ROOM_DEFINITION_CHANGE"],
        parameters={},
    ),
    Rule(
        rule_code="TEK17-11-9",
        title="Brannceller og brannmotstand",
        description=(
            "Bygning skal inndeles i brannceller slik at brann og røyk ikke "
            "sprer seg uakseptabelt raskt."
        ),
        legal_reference="TEK17 § 11-9",
        source="TEK17",
        version="2017",
        applies_to_categories=["UNINSPECTED_AREA"],
        parameters={},
    ),
    Rule(
        rule_code="TEK17-12-1",
        title="Krav om tilgjengelighet",
        description=(
            "Bygning med boenhet over én etasje skal ha heis eller rullestolrampe. "
            "Snusareal på minst 1,5 m diameter i alle oppholdsrom."
        ),
        legal_reference="TEK17 § 12-1",
        source="TEK17",
        version="2017",
        applies_to_categories=["UNINSPECTED_AREA"],
        parameters={"min_turning_diameter_m": 1.5},
    ),
    Rule(
        rule_code="TEK17-14-2",
        title="Energiramme for boligbygning",
        description=(
            "Boligbygning skal tilfredsstille energirammekrav beregnet som "
            "levert energi per m² BRA per år."
        ),
        legal_reference="TEK17 § 14-2",
        source="TEK17",
        version="2017",
        applies_to_categories=["UNINSPECTED_AREA"],
        parameters={"max_energy_kwh_per_m2": 120},
    ),
    Rule(
        rule_code="PBL-29-4",
        title="Byggverkets høyde og avstand fra nabogrense",
        description=(
            "Bygning kan ikke plasseres nærmere nabogrense enn 4 m, med mindre "
            "kommunen eller naboer samtykker."
        ),
        legal_reference="PBL § 29-4",
        source="PBL",
        version="2008",
        applies_to_categories=["UNINSPECTED_AREA"],
        parameters={"min_setback_m": 4.0},
    ),
    Rule(
        rule_code="PBL-29-3",
        title="Estetikk og tilpasning til omgivelsene",
        description=(
            "Tiltak etter loven skal ha en god utforming og være tilpasset "
            "eksisterende bebyggelse og omgivelsene."
        ),
        legal_reference="PBL § 29-3",
        source="PBL",
        version="2008",
        applies_to_categories=["USE_CHANGE_INDICATION"],
        parameters={},
    ),
    Rule(
        rule_code="SAK10-6-2",
        title="Dokumentasjon av endringer fra godkjent søknad",
        description=(
            "Endringer fra godkjent plan skal dokumenteres og i visse tilfeller "
            "søkes om på nytt (vesentlig avvik)."
        ),
        legal_reference="SAK10 § 6-2",
        source="SAK10",
        version="2010",
        applies_to_categories=[
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
            "ROOM_DEFINITION_CHANGE",
            "USE_CHANGE_INDICATION",
            "UNINSPECTED_AREA",
        ],
        parameters={},
    ),
    Rule(
        rule_code="TEK17-8-3",
        title="Etasjehøyde og loftsetasje",
        description=(
            "Beboelig loft eller underetasje skal oppfylle krav til "
            "takhøyde og areal for rom for varig opphold."
        ),
        legal_reference="TEK17 § 8-3",
        source="TEK17",
        version="2017",
        applies_to_categories=["ADDITION_DETECTED", "UNDERBUILDING_DETECTED", "UNINSPECTED_AREA"],
        parameters={"min_habitable_loft_area_m2": 15.0},
    ),
    # -----------------------------------------------------------------------
    # Rules covering BEDROOM_UTILITY_DISCREPANCY
    # -----------------------------------------------------------------------
    Rule(
        rule_code="TEK17-12-2",
        title="Krav til rom for varig opphold – areal og takhøyde",
        description=(
            "Rom for varig opphold (inkludert soverom) skal ha fri takhøyde på minst 2,4 m "
            "og areal tilpasset sin funksjon. Soverom minimum 7 m². "
            "Bruk av rom som soverom stiller krav til dagslys og ventilasjon."
        ),
        legal_reference="TEK17 § 12-2",
        source="TEK17",
        version="2017",
        applies_to_categories=[
            "BEDROOM_UTILITY_DISCREPANCY",
            "ROOM_DEFINITION_CHANGE",
            "USE_CHANGE_INDICATION",
        ],
        parameters={"min_bedroom_area_m2": 7.0, "min_ceiling_height_m": 2.4},
    ),
    Rule(
        rule_code="PBL-31-2",
        title="Tiltak på eksisterende bebyggelse – bruksendring",
        description=(
            "Vesentlig endring av bruk av eksisterende byggverk er søknadspliktig. "
            "Dette inkluderer omgjøring av soverom til kontor og bruksendring "
            "mellom bolig- og næringsformål."
        ),
        legal_reference="PBL § 31-2",
        source="PBL",
        version="2008",
        applies_to_categories=[
            "BEDROOM_UTILITY_DISCREPANCY",
            "USE_CHANGE_INDICATION",
            "MARKETED_FUNCTION_DISCREPANCY",
        ],
        parameters={},
    ),
    # -----------------------------------------------------------------------
    # Rules covering DOOR_PLACEMENT_CHANGE
    # -----------------------------------------------------------------------
    Rule(
        rule_code="TEK17-12-7-DOR",
        title="Krav til dør og adkomst",
        description=(
            "Dører til og i boenhet skal ha tilstrekkelig fri bredde for rullestol "
            "(minst 0,86 m fri åpning). Dørplassering påvirker adkomst, rømningsvei "
            "og branncelleinndeling."
        ),
        legal_reference="TEK17 § 12-7",
        source="TEK17",
        version="2017",
        applies_to_categories=["DOOR_PLACEMENT_CHANGE"],
        parameters={"min_door_clear_width_m": 0.86},
    ),
    Rule(
        rule_code="TEK17-11-14-ROMNING",
        title="Rømningsvei fra branncelle",
        description=(
            "Fra branncelle skal det finnes minst én rømningsvei til sikkert sted. "
            "Endret dørplassering kan blokkere eller svekke eksisterende rømningsvei."
        ),
        legal_reference="TEK17 § 11-14",
        source="TEK17",
        version="2017",
        applies_to_categories=["DOOR_PLACEMENT_CHANGE", "UNINSPECTED_AREA"],
        parameters={},
    ),
    # -----------------------------------------------------------------------
    # Rules covering WINDOW_PLACEMENT_CHANGE
    # -----------------------------------------------------------------------
    Rule(
        rule_code="TEK17-12-6-VINDU",
        title="Krav til vindu og dagslys",
        description=(
            "Rom for varig opphold skal ha vindu med lysflate på minst 10 % av gulvflaten. "
            "Vindu skal åpnes for naturlig ventilasjon. Soverom skal ha rømningsvei via vindu "
            "der annen utgang mangler."
        ),
        legal_reference="TEK17 § 12-6",
        source="TEK17",
        version="2017",
        applies_to_categories=["WINDOW_PLACEMENT_CHANGE", "ROOM_DEFINITION_CHANGE"],
        parameters={"min_window_ratio": 0.10},
    ),
    Rule(
        rule_code="SAK10-4-1-VINDU",
        title="Fasadeendring uten søknad – unntak",
        description=(
            "Mindre fasadeendringer som ikke endrer byggets karakter er unntatt søknadsplikt. "
            "Endring av vindusstørrelse eller -plassering kan likevel kreve søknad dersom "
            "det endrer fasadens uttrykk vesentlig."
        ),
        legal_reference="SAK10 § 4-1",
        source="SAK10",
        version="2010",
        applies_to_categories=["WINDOW_PLACEMENT_CHANGE"],
        parameters={},
    ),
    # -----------------------------------------------------------------------
    # Rules covering BALCONY_TERRACE_DISCREPANCY
    # -----------------------------------------------------------------------
    Rule(
        rule_code="TEK17-12-15-BALKONG",
        title="Krav til uteplass og balkong",
        description=(
            "Boenhet i blokk og lignende skal ha tilgang til privat uteplass (balkong, "
            "terrasse eller takterrasse) på minst 5 m² med tilfredsstillende solforhold. "
            "Rekkverk skal minst være 1,0 m. Innbygging av balkong uten tillatelse er søknadspliktig."
        ),
        legal_reference="TEK17 § 12-15",
        source="TEK17",
        version="2017",
        applies_to_categories=["BALCONY_TERRACE_DISCREPANCY", "ADDITION_DETECTED"],
        parameters={"min_outdoor_area_m2": 5.0, "min_railing_height_m": 1.0},
    ),
    Rule(
        rule_code="PBL-20-1-BALKONG",
        title="Tilbygg – balkong og terrasse søknadsplikt",
        description=(
            "Oppføring av balkong, terrasse og utebod er søknadspliktige tiltak etter PBL § 20-1. "
            "Innbygging av balkong til oppholdsrom betraktes som bruksendring og tilbygg."
        ),
        legal_reference="PBL § 20-1",
        source="PBL",
        version="2008",
        applies_to_categories=["BALCONY_TERRACE_DISCREPANCY"],
        parameters={},
    ),
    # -----------------------------------------------------------------------
    # Rules covering MARKETED_FUNCTION_DISCREPANCY
    # -----------------------------------------------------------------------
    Rule(
        rule_code="EMGL-6-7",
        title="Markedsføring av boligers funksjon",
        description=(
            "Boliger skal markedsføres i samsvar med faktisk godkjent bruk. "
            "Markedsføring av rom som soverom krever at rommet oppfyller TEK17-krav "
            "til soverom (areal, dagslys, takhøyde, ventilasjon)."
        ),
        legal_reference="Eiendomsmeglingsloven § 6-7",
        source="EIENDOMSMEGLINGSLOVEN",
        version="2007",
        applies_to_categories=[
            "MARKETED_FUNCTION_DISCREPANCY",
            "BEDROOM_UTILITY_DISCREPANCY",
        ],
        parameters={},
    ),
    Rule(
        rule_code="TEK17-12-2-SOVEROM",
        title="Minstekrav for markedsføring som soverom",
        description=(
            "Et rom kan kun markedsføres som soverom dersom det oppfyller minstekravene "
            "for rom for varig opphold: areal ≥ 7 m², takhøyde ≥ 2,4 m, vinduareal ≥ 10 % "
            "av gulvflaten, og tilfredsstillende ventilasjon."
        ),
        legal_reference="TEK17 § 12-2 jf. § 12-6",
        source="TEK17",
        version="2017",
        applies_to_categories=["MARKETED_FUNCTION_DISCREPANCY"],
        parameters={
            "min_area_m2": 7.0,
            "min_ceiling_height_m": 2.4,
            "min_window_ratio": 0.10,
        },
    ),
    # -----------------------------------------------------------------------
    # Rules covering USE_CHANGE_INDICATION
    # -----------------------------------------------------------------------
    Rule(
        rule_code="PBL-20-1-BRUKSENDRING",
        title="Søknadsplikt ved bruksendring",
        description=(
            "Vesentlig bruksendring er søknadspliktig etter PBL § 20-1. "
            "Dette inkluderer endring fra bolig til næring, fra bolig til hybel/pendlerleilighet, "
            "samt tiltak som medfører endring i brannkategori eller risikoklasse."
        ),
        legal_reference="PBL § 20-1",
        source="PBL",
        version="2008",
        applies_to_categories=["USE_CHANGE_INDICATION", "ADDITION_DETECTED"],
        parameters={},
    ),
    Rule(
        rule_code="SAK10-6-2-AVVIK",
        title="Dokumentasjon av vesentlige avvik fra godkjent søknad",
        description=(
            "Vesentlige avvik fra godkjent søknad skal dokumenteres og meldes til kommunen. "
            "Endringer som påvirker bruksareal, rominndeling eller konstruksjonssystem "
            "anses som vesentlige avvik."
        ),
        legal_reference="SAK10 § 6-2",
        source="SAK10",
        version="2010",
        applies_to_categories=[
            "USE_CHANGE_INDICATION",
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
            "ROOM_DEFINITION_CHANGE",
        ],
        parameters={},
    ),
]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class RuleRegistry:
    """In-memory registry of building regulations rules.

    In production this class should also query the ``rules`` database table
    and merge in any tenant-specific or municipality-specific overrides.
    """

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}
        self._load_seed_rules()

    def _load_seed_rules(self) -> None:
        for rule in _SEED_RULES:
            self._rules[rule.rule_code] = rule
        logger.debug("RuleRegistry: loaded %d seed rules.", len(self._rules))

    def load_rules(self) -> list[Rule]:
        """Return all active rules."""
        return [r for r in self._rules.values() if r.is_active]

    def get_rule(self, code: str) -> Rule | None:
        """Return a rule by code, or None if not found."""
        return self._rules.get(code)

    def register(self, rule: Rule) -> None:
        """Add or replace a rule in the registry."""
        self._rules[rule.rule_code] = rule
        logger.debug("RuleRegistry: registered rule '%s'.", rule.rule_code)

    async def load_from_db(self, db) -> None:
        """Load rules from the database, replacing in-memory seed rules."""
        try:
            from sqlalchemy import select
            # Dynamic import to avoid circular deps when used outside FastAPI context
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../apps/api"))
            from app.models.property_case import Rule as RuleModel

            result = await db.execute(select(RuleModel).where(RuleModel.is_active == True))
            db_rules = result.scalars().all()

            if db_rules:
                # Replace in-memory rules with DB rules
                self._rules = {}
                for db_rule in db_rules:
                    rule = Rule(
                        rule_code=db_rule.rule_code,
                        title=db_rule.title,
                        description=db_rule.description,
                        legal_reference=db_rule.legal_reference,
                        source=db_rule.source,
                        version=db_rule.version,
                        applies_to_categories=db_rule.applies_to_categories or [],
                        parameters=db_rule.parameters or {},
                        is_active=db_rule.is_active,
                    )
                    self._rules[rule.rule_code] = rule
                import logging
                logging.getLogger(__name__).info("Loaded %d rules from database.", len(self._rules))
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to load rules from DB, using seed: %s", exc)


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------


class RuleMatcher:
    """Find rules applicable to a given deviation."""

    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self._registry = registry or RuleRegistry()

    def find_matching_rules(
        self, deviation: DeviationResult
    ) -> list[RuleMatch]:
        """Return all rules that cover the deviation's category."""
        matches: list[RuleMatch] = []

        cat = deviation.category if isinstance(deviation.category, str) else deviation.category.value

        for rule in self._registry.load_rules():
            if cat not in rule.applies_to_categories:
                continue

            # Determine match type
            if rule.applies_to_categories == [cat]:
                match_type = "exact"
                confidence = min(deviation.confidence + 0.05, 1.0)
            else:
                match_type = "category"
                confidence = deviation.confidence * 0.90

            rationale = (
                f"Avviket i kategorien '{cat}' faller inn under "
                f"{rule.source} {rule.legal_reference}: {rule.title}."
            )

            matches.append(
                RuleMatch(
                    rule=rule,
                    deviation=deviation,
                    rationale=rationale,
                    confidence=round(confidence, 3),
                    match_type=match_type,
                )
            )

        logger.debug(
            "RuleMatcher: found %d rule match(es) for deviation category '%s'.",
            len(matches),
            cat,
        )
        return matches


# ---------------------------------------------------------------------------
# Explainer
# ---------------------------------------------------------------------------


class RuleExplainer:
    """Generate a human-readable explanation linking a rule to a deviation."""

    def explain(self, rule: Rule, deviation: DeviationResult) -> str:
        """Return a Norwegian-language explanation suitable for an architect report."""
        lines = [
            f"**{rule.rule_code} – {rule.title}**",
            f"Hjemmel: {rule.legal_reference} ({rule.source} {rule.version})",
            "",
            f"Regelens beskrivelse: {rule.description}",
            "",
            f"Avvik: {deviation.description}",
            f"Alvorlighetsgrad: {deviation.severity}",
            f"Konfidensgrad: {deviation.confidence:.0%}",
        ]

        if rule.parameters:
            lines.append("")
            lines.append("Relevante krav:")
            for param, value in rule.parameters.items():
                human_param = param.replace("_", " ").capitalize()
                lines.append(f"  - {human_param}: {value}")

        return "\n".join(lines)
