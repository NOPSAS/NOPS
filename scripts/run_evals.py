"""
ByggSjekk – Evalueringsscript for avviksmotoren.

Kjøres: python scripts/run_evals.py

Måler precision, recall og F1 for DeviationEngine på 5 predefinerte scenarier.
Krever ingen database eller Docker – kjøres mot in-memory mock data.
"""
from __future__ import annotations
import sys
import os

# Add service paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../services"))

from dataclasses import dataclass
from services.plan_parser.parser import StructuredPlanData, FloorData, SpaceData, MeasurementData
from services.deviation_engine.engine import DeviationEngine


@dataclass
class EvalScenario:
    name: str
    reference_plan: StructuredPlanData
    current_plan: StructuredPlanData
    expected_categories: set[str]  # Expected deviation categories


def make_plan(spaces_per_floor: dict[int, list[dict]], total_area: float | None = None) -> StructuredPlanData:
    """Build a StructuredPlanData from a dict of floor -> space configs."""
    floors = []
    calc_area = 0.0
    room_count = 0
    for floor_num, space_configs in spaces_per_floor.items():
        spaces = []
        floor_area = 0.0
        for cfg in space_configs:
            space = SpaceData(
                name=cfg["name"],
                space_type=cfg.get("type", "rom"),
                floor_number=floor_num,
                area=cfg.get("area", 15.0),
                confidence=cfg.get("confidence", 0.92),
                attributes={},
            )
            spaces.append(space)
            floor_area += space.area or 0
        floor = FloorData(
            floor_number=floor_num,
            label=f"Etasje {floor_num}",
            total_area=floor_area,
            spaces=spaces,
            raw_annotations=[],
        )
        floors.append(floor)
        calc_area += floor_area
        room_count += len(spaces)
    return StructuredPlanData(
        document_id=f"eval-doc-{id(floors)}",
        storage_key="eval/key",
        floors=floors,
        measurements=[],
        total_area=total_area or calc_area,
        room_count=room_count,
        metadata={"source": "eval_script"},
    )


SCENARIOS: list[EvalScenario] = [
    # Scenario 1: Ingen endringer → 0 avvik
    EvalScenario(
        name="1_ingen_endringer",
        reference_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Kjøkken", "type": "kjøkken", "area": 14.0},
            {"name": "Soverom 1", "type": "soverom", "area": 13.0},
            {"name": "Bad", "type": "bad", "area": 7.0},
        ]}),
        current_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Kjøkken", "type": "kjøkken", "area": 14.0},
            {"name": "Soverom 1", "type": "soverom", "area": 13.0},
            {"name": "Bad", "type": "bad", "area": 7.0},
        ]}),
        expected_categories=set(),
    ),

    # Scenario 2: Soverom omdøpt til kontor → BEDROOM_UTILITY_DISCREPANCY
    EvalScenario(
        name="2_soverom_til_kontor",
        reference_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Soverom 1", "type": "soverom", "area": 13.0},
        ]}),
        current_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Soverom 1", "type": "kontor", "area": 13.0},
        ]}),
        expected_categories={"BEDROOM_UTILITY_DISCREPANCY"},
    ),

    # Scenario 3: Nytt rom → ADDITION_DETECTED
    EvalScenario(
        name="3_nytt_rom",
        reference_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Soverom 1", "type": "soverom", "area": 13.0},
        ]}),
        current_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Soverom 1", "type": "soverom", "area": 13.0},
            {"name": "Kontor", "type": "kontor", "area": 18.0},
        ]}),
        expected_categories={"ADDITION_DETECTED"},
    ),

    # Scenario 4: Fjernet rom → UNDERBUILDING_DETECTED
    EvalScenario(
        name="4_fjernet_rom",
        reference_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Soverom 1", "type": "soverom", "area": 13.0},
            {"name": "Soverom 2", "type": "soverom", "area": 11.0},
        ]}),
        current_plan=make_plan({1: [
            {"name": "Stue", "type": "stue", "area": 32.0},
            {"name": "Soverom 1", "type": "soverom", "area": 13.0},
        ]}),
        expected_categories={"UNDERBUILDING_DETECTED"},
    ),

    # Scenario 5: Blandet – romtypendring + tilbygg
    EvalScenario(
        name="5_blandet_endringer",
        reference_plan=make_plan({
            1: [
                {"name": "Stue", "type": "stue", "area": 32.0},
                {"name": "Soverom 1", "type": "soverom", "area": 13.0},
                {"name": "Bod", "type": "bod", "area": 5.0},
            ],
        }),
        current_plan=make_plan({
            1: [
                {"name": "Stue", "type": "stue", "area": 32.0},
                {"name": "Soverom 1", "type": "kontor", "area": 13.0},  # type change
                {"name": "Bod", "type": "bod", "area": 5.0},
                {"name": "Vaskerom", "type": "vaskerom", "area": 8.0},  # new room
            ],
        }),
        expected_categories={"BEDROOM_UTILITY_DISCREPANCY", "ADDITION_DETECTED"},
    ),
]


def evaluate_scenario(engine: DeviationEngine, scenario: EvalScenario) -> dict:
    """Run engine on a scenario and compute precision/recall."""
    results = engine.compare(scenario.reference_plan, scenario.current_plan)
    detected_categories = {r.category for r in results}

    expected = scenario.expected_categories
    true_positives = detected_categories & expected
    false_positives = detected_categories - expected
    false_negatives = expected - detected_categories

    precision = len(true_positives) / len(detected_categories) if detected_categories else (1.0 if not expected else 0.0)
    recall = len(true_positives) / len(expected) if expected else (1.0 if not detected_categories else 0.0)
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "scenario": scenario.name,
        "expected": sorted(expected),
        "detected": sorted(detected_categories),
        "true_positives": sorted(true_positives),
        "false_positives": sorted(false_positives),
        "false_negatives": sorted(false_negatives),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "pass": len(false_positives) == 0 and len(false_negatives) == 0,
    }


def main():
    engine = DeviationEngine()

    print("=" * 60)
    print("ByggSjekk – Avviksmotorevaluering")
    print("=" * 60)

    results = []
    for scenario in SCENARIOS:
        result = evaluate_scenario(engine, scenario)
        results.append(result)

        status = "✅ PASS" if result["pass"] else "❌ FAIL"
        print(f"\n{status} {result['scenario']}")
        print(f"  Forventet:  {result['expected'] or '(ingen)'}")
        print(f"  Detektert:  {result['detected'] or '(ingen)'}")
        if result["false_positives"]:
            print(f"  FP (ekstra): {result['false_positives']}")
        if result["false_negatives"]:
            print(f"  FN (misset): {result['false_negatives']}")
        print(f"  Precision={result['precision']:.3f}  Recall={result['recall']:.3f}  F1={result['f1']:.3f}")

    # Aggregate metrics
    avg_precision = sum(r["precision"] for r in results) / len(results)
    avg_recall = sum(r["recall"] for r in results) / len(results)
    avg_f1 = sum(r["f1"] for r in results) / len(results)
    passed = sum(1 for r in results if r["pass"])

    print("\n" + "=" * 60)
    print(f"TOTALT: {passed}/{len(results)} scenarier bestått")
    print(f"Gjennomsnitt – Precision: {avg_precision:.3f}  Recall: {avg_recall:.3f}  F1: {avg_f1:.3f}")

    target_met = avg_precision >= 0.80 and avg_recall >= 0.80
    if target_met:
        print("✅ Målkrav oppfylt: precision ≥ 0.80 og recall ≥ 0.80")
    else:
        print("❌ Målkrav IKKE oppfylt: precision ≥ 0.80 og recall ≥ 0.80")

    print("=" * 60)
    return 0 if target_met else 1


if __name__ == "__main__":
    sys.exit(main())
