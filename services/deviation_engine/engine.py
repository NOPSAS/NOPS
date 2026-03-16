"""
DeviationEngine – sammenligner to StructuredPlan-objekter og returnerer avvik.

Avvikskategorier (domenespesifikke, fra spec):
    ROOM_DEFINITION_CHANGE       – rom omdefinert til annen funksjon
    BEDROOM_UTILITY_DISCREPANCY  – soverom brukt som annet/vice versa
    DOOR_PLACEMENT_CHANGE        – dørplassering endret
    WINDOW_PLACEMENT_CHANGE      – vindusplassering endret
    BALCONY_TERRACE_DISCREPANCY  – balkong/terrasse avvik
    ADDITION_DETECTED            – tilbygg/utvidelse oppdaget
    UNDERBUILDING_DETECTED       – underbygging/manglende rom oppdaget
    UNINSPECTED_AREA             – område ikke vurdert / lav confidence
    USE_CHANGE_INDICATION        – bruksendring indikert
    MARKETED_FUNCTION_DISCREPANCY – markedsført funksjon stemmer ikke
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Thresholds
TOTAL_AREA_DEVIATION_PCT = 0.05   # 5% total area change triggers ADDITION/UNDERBUILDING
SPACE_AREA_DEVIATION_PCT = 0.15   # 15% per-space area change
MIN_CONFIDENCE = 0.60

# Space types considered "bedroom" (Norwegian)
BEDROOM_TYPES = {"soverom", "bedroom", "hybel"}
# Space types considered living spaces (varig opphold)
LIVING_TYPES = {"stue", "kjøkken", "kjøkken/stue", "stue/kjøkken", "livingroom", "living"}
# Space types considered utility/non-living
UTILITY_TYPES = {"kontor", "office", "bod", "vaskerom", "gang", "hall", "entre", "wc", "bad", "bathroom"}
# Space types considered outdoor/extra
OUTDOOR_TYPES = {"balkong", "balcony", "terrasse", "terrace", "veranda"}


@dataclass
class DeviationResult:
    category: str
    severity: str
    description: str
    confidence: float
    evidence_references: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.confidence = min(max(self.confidence, 0.0), 1.0)


class ConfidenceScorer:
    """Adjusts confidence based on evidence quality."""

    def score(
        self,
        base_confidence: float,
        num_evidence: int,
        area_pct_change: float | None = None,
    ) -> float:
        score = base_confidence
        # More evidence → higher confidence
        if num_evidence >= 2:
            score = min(score + 0.05, 1.0)
        # Larger area change → higher confidence
        if area_pct_change is not None:
            if abs(area_pct_change) > 0.30:
                score = min(score + 0.10, 1.0)
            elif abs(area_pct_change) < 0.05:
                score = max(score - 0.10, MIN_CONFIDENCE)
        return round(min(max(score, 0.0), 1.0), 3)


class EvidenceLinker:
    """Creates structured evidence references."""

    def room_change(self, space_name: str, floor: int, ref_value: Any, curr_value: Any) -> dict:
        return {
            "type": "room_comparison",
            "space_name": space_name,
            "floor_number": floor,
            "reference_value": ref_value,
            "current_value": curr_value,
        }

    def floor_comparison(self, ref_floors: list[int], curr_floors: list[int]) -> dict:
        return {
            "type": "floor_comparison",
            "reference_floors": ref_floors,
            "current_floors": curr_floors,
        }

    def area_comparison(self, label: str, ref_area: float, curr_area: float) -> dict:
        pct = (curr_area - ref_area) / ref_area if ref_area > 0 else 0
        return {
            "type": "area_comparison",
            "label": label,
            "reference_area_m2": round(ref_area, 2),
            "current_area_m2": round(curr_area, 2),
            "pct_change": round(pct * 100, 1),
        }


class DeviationEngine:
    """
    Compares a reference StructuredPlan with a current StructuredPlan
    and returns a list of DeviationResult objects.
    """

    def __init__(self):
        self.scorer = ConfidenceScorer()
        self.linker = EvidenceLinker()

    def compare(self, reference_plan: Any, current_plan: Any) -> list[DeviationResult]:
        """
        Compare two StructuredPlanData objects and return deviations.
        Each check returns 0 or more DeviationResult objects.
        """
        deviations: list[DeviationResult] = []

        deviations.extend(self._check_total_area(reference_plan, current_plan))
        deviations.extend(self._check_floors_added_removed(reference_plan, current_plan))
        deviations.extend(self._check_room_additions_removals(reference_plan, current_plan))
        deviations.extend(self._check_room_type_changes(reference_plan, current_plan))
        deviations.extend(self._check_bedroom_discrepancy(reference_plan, current_plan))
        deviations.extend(self._check_outdoor_spaces(reference_plan, current_plan))
        deviations.extend(self._check_uninspected_areas(current_plan))
        deviations.extend(self._check_use_change(reference_plan, current_plan))
        deviations.extend(self._check_marketed_function(reference_plan, current_plan))
        deviations.extend(self._check_door_placement(reference_plan, current_plan))
        deviations.extend(self._check_window_placement(reference_plan, current_plan))

        return deviations

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_total_area(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """Detect significant total area change → ADDITION or UNDERBUILDING."""
        results = []
        ref_area = ref.total_area or 0.0
        curr_area = curr.total_area or 0.0

        if ref_area <= 0:
            return results

        pct = (curr_area - ref_area) / ref_area
        if abs(pct) < TOTAL_AREA_DEVIATION_PCT:
            return results

        if pct > 0:
            category = "ADDITION_DETECTED"
            severity = "HIGH" if pct > 0.20 else "MEDIUM"
            desc = (
                f"Totalt bruttoareal er økt med {pct*100:.1f}% "
                f"({ref_area:.1f} m² → {curr_area:.1f} m²). "
                "Dette kan indikere et ikke-dokumentert tilbygg eller påbygg."
            )
        else:
            category = "UNDERBUILDING_DETECTED"
            severity = "HIGH" if abs(pct) > 0.20 else "MEDIUM"
            desc = (
                f"Totalt bruttoareal er redusert med {abs(pct)*100:.1f}% "
                f"({ref_area:.1f} m² → {curr_area:.1f} m²). "
                "Dette kan indikere at areal er fjernet eller at tidligere rom ikke er dokumentert."
            )

        confidence = self.scorer.score(0.80, 1, pct)
        evidence = [self.linker.area_comparison("Totalt areal", ref_area, curr_area)]
        results.append(DeviationResult(
            category=category, severity=severity,
            description=desc, confidence=confidence,
            evidence_references=evidence,
        ))
        return results

    def _check_floors_added_removed(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """Detect added or removed floors."""
        results = []
        ref_floors = {f.floor_number for f in ref.floors}
        curr_floors = {f.floor_number for f in curr.floors}

        added = curr_floors - ref_floors
        removed = ref_floors - curr_floors

        for floor_num in added:
            floor = next(f for f in curr.floors if f.floor_number == floor_num)
            area = floor.total_area or 0.0
            results.append(DeviationResult(
                category="ADDITION_DETECTED",
                severity="HIGH",
                description=(
                    f"Ny etasje oppdaget: etasje {floor_num} "
                    f"(ca. {area:.0f} m²) finnes ikke i referansetegningene."
                ),
                confidence=self.scorer.score(0.90, 1),
                evidence_references=[self.linker.floor_comparison(sorted(ref_floors), sorted(curr_floors))],
            ))

        for floor_num in removed:
            results.append(DeviationResult(
                category="UNDERBUILDING_DETECTED",
                severity="MEDIUM",
                description=(
                    f"Etasje {floor_num} fra referansetegningene er ikke dokumentert i nåværende tegninger."
                ),
                confidence=self.scorer.score(0.85, 1),
                evidence_references=[self.linker.floor_comparison(sorted(ref_floors), sorted(curr_floors))],
            ))

        return results

    def _check_room_additions_removals(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """Detect rooms added or removed per floor."""
        results = []

        ref_floors_map = {f.floor_number: f for f in ref.floors}
        curr_floors_map = {f.floor_number: f for f in curr.floors}

        for floor_num in ref_floors_map.keys() & curr_floors_map.keys():
            ref_spaces = {s.name.lower().strip(): s for s in ref_floors_map[floor_num].spaces}
            curr_spaces = {s.name.lower().strip(): s for s in curr_floors_map[floor_num].spaces}

            added_names = set(curr_spaces.keys()) - set(ref_spaces.keys())
            removed_names = set(ref_spaces.keys()) - set(curr_spaces.keys())

            for name in added_names:
                space = curr_spaces[name]
                is_outdoor = space.space_type.lower() in OUTDOOR_TYPES
                if is_outdoor:
                    continue  # handled by outdoor check
                area = space.area or 0.0
                results.append(DeviationResult(
                    category="ADDITION_DETECTED",
                    severity="MEDIUM",
                    description=(
                        f"Rom '{space.name}' (type: {space.space_type}, ca. {area:.0f} m²) "
                        f"på etasje {floor_num} er ikke i referansetegningene."
                    ),
                    confidence=self.scorer.score(0.80, 1),
                    evidence_references=[self.linker.room_change(space.name, floor_num, None, space.space_type)],
                ))

            for name in removed_names:
                space = ref_spaces[name]
                results.append(DeviationResult(
                    category="UNDERBUILDING_DETECTED",
                    severity="MEDIUM",
                    description=(
                        f"Rom '{space.name}' fra referansetegningene er ikke dokumentert i nåværende tegninger "
                        f"(etasje {floor_num})."
                    ),
                    confidence=self.scorer.score(0.80, 1),
                    evidence_references=[self.linker.room_change(space.name, floor_num, space.space_type, None)],
                ))

        return results

    def _check_room_type_changes(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """Detect rooms that changed type/function (ROOM_DEFINITION_CHANGE)."""
        results = []

        ref_floors_map = {f.floor_number: f for f in ref.floors}
        curr_floors_map = {f.floor_number: f for f in curr.floors}

        for floor_num in ref_floors_map.keys() & curr_floors_map.keys():
            ref_spaces = {s.name.lower().strip(): s for s in ref_floors_map[floor_num].spaces}
            curr_spaces = {s.name.lower().strip(): s for s in curr_floors_map[floor_num].spaces}

            for name in ref_spaces.keys() & curr_spaces.keys():
                ref_space = ref_spaces[name]
                curr_space = curr_spaces[name]
                if ref_space.space_type.lower() == curr_space.space_type.lower():
                    continue

                # Check if this is a bedroom → other change (handled separately)
                ref_is_bedroom = ref_space.space_type.lower() in BEDROOM_TYPES
                curr_is_bedroom = curr_space.space_type.lower() in BEDROOM_TYPES
                if ref_is_bedroom != curr_is_bedroom:
                    continue  # handled by bedroom check

                results.append(DeviationResult(
                    category="ROOM_DEFINITION_CHANGE",
                    severity="MEDIUM",
                    description=(
                        f"Rom '{ref_space.name}' på etasje {floor_num} ser ut til å ha endret funksjon: "
                        f"'{ref_space.space_type}' (referanse) → '{curr_space.space_type}' (nåværende). "
                        "Bruksendring av rom kan ha konsekvenser for godkjenningsstatus."
                    ),
                    confidence=self.scorer.score(0.75, 2),
                    evidence_references=[
                        self.linker.room_change(ref_space.name, floor_num, ref_space.space_type, curr_space.space_type)
                    ],
                ))

                # Check per-space area while we're at it
                ref_area = ref_space.area or 0.0
                curr_area = curr_space.area or 0.0
                if ref_area > 0:
                    pct = (curr_area - ref_area) / ref_area
                    if abs(pct) > SPACE_AREA_DEVIATION_PCT:
                        category = "ADDITION_DETECTED" if pct > 0 else "UNDERBUILDING_DETECTED"
                        results.append(DeviationResult(
                            category=category,
                            severity="LOW",
                            description=(
                                f"Areal for '{ref_space.name}' endret med {pct*100:.1f}%: "
                                f"{ref_area:.1f} m² → {curr_area:.1f} m²."
                            ),
                            confidence=self.scorer.score(0.70, 1, pct),
                            evidence_references=[self.linker.area_comparison(ref_space.name, ref_area, curr_area)],
                        ))

        return results

    def _check_bedroom_discrepancy(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """Detect bedroom ↔ non-bedroom changes (BEDROOM_UTILITY_DISCREPANCY)."""
        results = []

        ref_floors_map = {f.floor_number: f for f in ref.floors}
        curr_floors_map = {f.floor_number: f for f in curr.floors}

        for floor_num in ref_floors_map.keys() & curr_floors_map.keys():
            ref_spaces = {s.name.lower().strip(): s for s in ref_floors_map[floor_num].spaces}
            curr_spaces = {s.name.lower().strip(): s for s in curr_floors_map[floor_num].spaces}

            for name in ref_spaces.keys() & curr_spaces.keys():
                ref_space = ref_spaces[name]
                curr_space = curr_spaces[name]

                ref_bedroom = ref_space.space_type.lower() in BEDROOM_TYPES
                curr_bedroom = curr_space.space_type.lower() in BEDROOM_TYPES

                if ref_bedroom == curr_bedroom:
                    continue

                if ref_bedroom and not curr_bedroom:
                    desc = (
                        f"'{ref_space.name}' er registrert som soverom i referansetegningene, "
                        f"men fremstår nå som '{curr_space.space_type}'. "
                        "Endring av soverom til annen bruk kan påvirke boligens godkjente bruksform."
                    )
                else:
                    desc = (
                        f"'{curr_space.name}' ser ut til å brukes som soverom, "
                        f"men er registrert som '{ref_space.space_type}' i referansetegningene. "
                        "Bruk av rom som soverom stiller krav til takhøyde, areal og lysforhold."
                    )

                results.append(DeviationResult(
                    category="BEDROOM_UTILITY_DISCREPANCY",
                    severity="HIGH",
                    description=desc,
                    confidence=self.scorer.score(0.80, 2),
                    evidence_references=[
                        self.linker.room_change(ref_space.name, floor_num, ref_space.space_type, curr_space.space_type)
                    ],
                ))

        return results

    def _check_outdoor_spaces(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """Detect balkong/terrasse discrepancies."""
        results = []

        def get_outdoor(plan: Any) -> dict[str, Any]:
            spaces = {}
            for floor in plan.floors:
                for s in floor.spaces:
                    if s.space_type.lower() in OUTDOOR_TYPES:
                        spaces[s.name.lower().strip()] = s
            return spaces

        ref_outdoor = get_outdoor(ref)
        curr_outdoor = get_outdoor(curr)

        added = set(curr_outdoor.keys()) - set(ref_outdoor.keys())
        removed = set(ref_outdoor.keys()) - set(curr_outdoor.keys())

        for name in added:
            space = curr_outdoor[name]
            results.append(DeviationResult(
                category="BALCONY_TERRACE_DISCREPANCY",
                severity="MEDIUM",
                description=(
                    f"'{space.name}' (type: {space.space_type}) finnes ikke i referansetegningene. "
                    "Ny balkong eller terrasse kan kreve dokumentasjon."
                ),
                confidence=self.scorer.score(0.75, 1),
                evidence_references=[self.linker.room_change(space.name, space.floor_number or 0, None, space.space_type)],
            ))

        for name in removed:
            space = ref_outdoor[name]
            results.append(DeviationResult(
                category="BALCONY_TERRACE_DISCREPANCY",
                severity="LOW",
                description=(
                    f"'{space.name}' fra referansetegningene er ikke dokumentert i nåværende tegninger."
                ),
                confidence=self.scorer.score(0.70, 1),
                evidence_references=[self.linker.room_change(space.name, space.floor_number or 0, space.space_type, None)],
            ))

        return results

    def _check_uninspected_areas(self, curr: Any) -> list[DeviationResult]:
        """Flag spaces with low confidence as UNINSPECTED_AREA."""
        results = []
        for floor in curr.floors:
            for space in floor.spaces:
                if (space.confidence or 1.0) < 0.50:
                    results.append(DeviationResult(
                        category="UNINSPECTED_AREA",
                        severity="LOW",
                        description=(
                            f"Rom '{space.name}' på etasje {floor.floor_number} har lav datakvalitet "
                            f"(confidence={space.confidence:.2f}). "
                            "Rommet bør verifiseres manuelt av arkitekt."
                        ),
                        confidence=space.confidence or 0.4,
                        evidence_references=[
                            self.linker.room_change(space.name, floor.floor_number, space.space_type, "low_confidence")
                        ],
                    ))
        return results

    def _check_use_change(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """
        Detect rooms that indicate a use change (USE_CHANGE_INDICATION).

        Triggers when a room in the current plan has a type associated with
        commercial or non-residential use that was not present in the reference plan.
        """
        COMMERCIAL_TYPES = {
            "butikk", "kontor", "office", "lager", "warehouse",
            "restaurant", "kafe", "cafe", "verksted", "atelier",
            "næring", "næringsareal", "leilighet_næring",
        }
        results = []

        ref_floors_map = {f.floor_number: f for f in ref.floors}
        curr_floors_map = {f.floor_number: f for f in curr.floors}

        for floor_num in ref_floors_map.keys() & curr_floors_map.keys():
            ref_spaces = {s.name.lower().strip(): s for s in ref_floors_map[floor_num].spaces}
            curr_spaces = {s.name.lower().strip(): s for s in curr_floors_map[floor_num].spaces}

            for name in ref_spaces.keys() & curr_spaces.keys():
                ref_space = ref_spaces[name]
                curr_space = curr_spaces[name]

                ref_commercial = ref_space.space_type.lower() in COMMERCIAL_TYPES
                curr_commercial = curr_space.space_type.lower() in COMMERCIAL_TYPES

                # Only flag: residential → commercial transitions
                if not ref_commercial and curr_commercial:
                    results.append(DeviationResult(
                        category="USE_CHANGE_INDICATION",
                        severity="HIGH",
                        description=(
                            f"Rom '{ref_space.name}' på etasje {floor_num} ser ut til å ha endret bruksformål "
                            f"fra '{ref_space.space_type}' (godkjent) til '{curr_space.space_type}' (nåværende). "
                            "Bruksendring fra boligformål til næringsformål er søknadspliktig etter PBL § 31-2."
                        ),
                        confidence=self.scorer.score(0.78, 2),
                        evidence_references=[
                            self.linker.room_change(ref_space.name, floor_num, ref_space.space_type, curr_space.space_type)
                        ],
                    ))

        return results

    def _check_marketed_function(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """
        Detect MARKETED_FUNCTION_DISCREPANCY.

        Flags rooms whose name or attributes imply a marketed function (e.g.
        "soverom" in the name) that does not match the approved space type.
        This is relevant at property sales / valuations.
        """
        results = []

        ref_floors_map = {f.floor_number: f for f in ref.floors}
        curr_floors_map = {f.floor_number: f for f in curr.floors}

        for floor_num in curr_floors_map.keys():
            ref_floor = ref_floors_map.get(floor_num)
            curr_floor = curr_floors_map[floor_num]

            ref_spaces_by_name = (
                {s.name.lower().strip(): s for s in ref_floor.spaces}
                if ref_floor else {}
            )

            for curr_space in curr_floor.spaces:
                name_lower = curr_space.name.lower().strip()
                marketed_as_bedroom = "soverom" in name_lower or "bedroom" in name_lower

                if not marketed_as_bedroom:
                    continue

                ref_space = ref_spaces_by_name.get(name_lower)
                if ref_space is None:
                    # Approved plan doesn't have this room at all
                    continue

                approved_is_bedroom = ref_space.space_type.lower() in BEDROOM_TYPES
                current_is_bedroom = curr_space.space_type.lower() in BEDROOM_TYPES

                if not approved_is_bedroom:
                    # Marketed/labelled as bedroom but not approved as one
                    results.append(DeviationResult(
                        category="MARKETED_FUNCTION_DISCREPANCY",
                        severity="HIGH",
                        description=(
                            f"Rom '{curr_space.name}' er navngitt som soverom, men er godkjent "
                            f"som '{ref_space.space_type}' i gjeldende tegninger. "
                            "Markedsføring av rommet som soverom uten godkjenning kan være villedende "
                            "etter eiendomsmeglingsloven § 6-7."
                        ),
                        confidence=self.scorer.score(0.85, 2),
                        evidence_references=[
                            self.linker.room_change(curr_space.name, floor_num, ref_space.space_type, curr_space.space_type)
                        ],
                    ))

        return results

    def _check_door_placement(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """
        Detect DOOR_PLACEMENT_CHANGE.

        Uses the 'doors' attribute on spaces if present. If a space has a
        different door count or door positions vs the reference, flag it.
        Falls back to detecting missing/extra spaces that suggest door changes.
        """
        results = []

        ref_floors_map = {f.floor_number: f for f in ref.floors}
        curr_floors_map = {f.floor_number: f for f in curr.floors}

        for floor_num in ref_floors_map.keys() & curr_floors_map.keys():
            ref_spaces = {s.name.lower().strip(): s for s in ref_floors_map[floor_num].spaces}
            curr_spaces = {s.name.lower().strip(): s for s in curr_floors_map[floor_num].spaces}

            for name in ref_spaces.keys() & curr_spaces.keys():
                ref_space = ref_spaces[name]
                curr_space = curr_spaces[name]

                ref_attrs = ref_space.attributes or {}
                curr_attrs = curr_space.attributes or {}

                ref_doors = ref_attrs.get("door_count") or ref_attrs.get("doors")
                curr_doors = curr_attrs.get("door_count") or curr_attrs.get("doors")

                if ref_doors is not None and curr_doors is not None and ref_doors != curr_doors:
                    results.append(DeviationResult(
                        category="DOOR_PLACEMENT_CHANGE",
                        severity="LOW",
                        description=(
                            f"Antall dører i '{ref_space.name}' på etasje {floor_num} er endret "
                            f"fra {ref_doors} (referanse) til {curr_doors} (nåværende). "
                            "Endret dørplassering kan påvirke rømningsveier og branncelleinndeling."
                        ),
                        confidence=self.scorer.score(0.70, 2),
                        evidence_references=[
                            self.linker.room_change(ref_space.name, floor_num, f"dører: {ref_doors}", f"dører: {curr_doors}")
                        ],
                    ))
                elif "door_positions" in ref_attrs and "door_positions" in curr_attrs:
                    ref_pos = sorted(str(p) for p in (ref_attrs["door_positions"] or []))
                    curr_pos = sorted(str(p) for p in (curr_attrs["door_positions"] or []))
                    if ref_pos != curr_pos:
                        results.append(DeviationResult(
                            category="DOOR_PLACEMENT_CHANGE",
                            severity="LOW",
                            description=(
                                f"Dørplassering i '{ref_space.name}' på etasje {floor_num} ser ut til å avvike "
                                "fra godkjente tegninger. Bør verifiseres av arkitekt."
                            ),
                            confidence=self.scorer.score(0.65, 2),
                            evidence_references=[
                                self.linker.room_change(ref_space.name, floor_num, str(ref_pos), str(curr_pos))
                            ],
                        ))

        return results

    def _check_window_placement(self, ref: Any, curr: Any) -> list[DeviationResult]:
        """
        Detect WINDOW_PLACEMENT_CHANGE.

        Uses the 'window_count', 'window_area_m2', or 'windows' attribute on
        spaces if present. If a space has significantly different window area or
        count vs the reference, flag it.
        """
        results = []

        ref_floors_map = {f.floor_number: f for f in ref.floors}
        curr_floors_map = {f.floor_number: f for f in curr.floors}

        for floor_num in ref_floors_map.keys() & curr_floors_map.keys():
            ref_spaces = {s.name.lower().strip(): s for s in ref_floors_map[floor_num].spaces}
            curr_spaces = {s.name.lower().strip(): s for s in curr_floors_map[floor_num].spaces}

            for name in ref_spaces.keys() & curr_spaces.keys():
                ref_space = ref_spaces[name]
                curr_space = curr_spaces[name]

                ref_attrs = ref_space.attributes or {}
                curr_attrs = curr_space.attributes or {}

                ref_win = ref_attrs.get("window_count") or ref_attrs.get("windows")
                curr_win = curr_attrs.get("window_count") or curr_attrs.get("windows")

                if ref_win is not None and curr_win is not None and ref_win != curr_win:
                    results.append(DeviationResult(
                        category="WINDOW_PLACEMENT_CHANGE",
                        severity="LOW",
                        description=(
                            f"Antall vinduer i '{ref_space.name}' på etasje {floor_num} er endret "
                            f"fra {ref_win} (referanse) til {curr_win} (nåværende). "
                            "Endring av vindu kan påvirke krav til lysflate (TEK17 § 12-6) "
                            "og rømningsvei."
                        ),
                        confidence=self.scorer.score(0.72, 2),
                        evidence_references=[
                            self.linker.room_change(ref_space.name, floor_num, f"vinduer: {ref_win}", f"vinduer: {curr_win}")
                        ],
                    ))
                else:
                    # Also check window area if available
                    ref_win_area = ref_attrs.get("window_area_m2")
                    curr_win_area = curr_attrs.get("window_area_m2")
                    if ref_win_area is not None and curr_win_area is not None and ref_win_area > 0:
                        pct = (curr_win_area - ref_win_area) / ref_win_area
                        if abs(pct) > 0.20:
                            results.append(DeviationResult(
                                category="WINDOW_PLACEMENT_CHANGE",
                                severity="LOW",
                                description=(
                                    f"Vindusareal i '{ref_space.name}' på etasje {floor_num} er endret "
                                    f"med {pct*100:.1f}%: {ref_win_area:.2f} m² → {curr_win_area:.2f} m². "
                                    "Dette kan påvirke krav til dagslys etter TEK17 § 12-6."
                                ),
                                confidence=self.scorer.score(0.68, 2, pct),
                                evidence_references=[
                                    self.linker.area_comparison(
                                        f"Vindusareal – {ref_space.name}", ref_win_area, curr_win_area
                                    )
                                ],
                            ))

        return results
