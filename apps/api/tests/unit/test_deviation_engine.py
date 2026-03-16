"""Unit tests for DeviationEngine."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../../services"))

from plan_parser.parser import StructuredPlanData, FloorData, SpaceData, MeasurementData
from deviation_engine.engine import DeviationEngine


def make_plan(floors_config: list[dict]) -> StructuredPlanData:
    """Helper to create a StructuredPlanData from simple config."""
    floors = []
    total_area = 0.0
    room_count = 0
    for floor_cfg in floors_config:
        spaces = []
        floor_area = 0.0
        for space_cfg in floor_cfg.get("spaces", []):
            space = SpaceData(
                name=space_cfg["name"],
                space_type=space_cfg.get("type", "rom"),
                floor_number=floor_cfg["floor"],
                area=space_cfg.get("area", 20.0),
                confidence=space_cfg.get("confidence", 0.9),
                attributes=space_cfg.get("attributes", {}),
            )
            spaces.append(space)
            floor_area += space.area or 0
        floor = FloorData(
            floor_number=floor_cfg["floor"],
            label=f"Etasje {floor_cfg['floor']}",
            total_area=floor_area,
            spaces=spaces,
        )
        floors.append(floor)
        total_area += floor_area
        room_count += len(spaces)
    return StructuredPlanData(
        document_id="test-doc",
        storage_key="test/key",
        floors=floors,
        measurements=[],
        total_area=total_area,
        room_count=room_count,
    )


class TestDeviationEngine:

    def setup_method(self):
        self.engine = DeviationEngine()

    def test_identical_plans_no_deviations(self):
        plan = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 30.0},
                       {"name": "Soverom", "type": "soverom", "area": 12.0}]
        }])
        deviations = self.engine.compare(plan, plan)
        # Identical plans should produce no meaningful deviations
        assert len(deviations) == 0 or all(d.confidence < 0.3 for d in deviations)

    def test_new_room_detected_as_addition(self):
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 30.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [
                {"name": "Stue", "type": "stue", "area": 30.0},
                {"name": "Kontor", "type": "kontor", "area": 15.0},
            ]
        }])
        deviations = self.engine.compare(reference, current)
        categories = [d.category for d in deviations]
        assert any("ADDITION" in str(c).upper() for c in categories), f"Expected ADDITION in {categories}"

    def test_removed_room_detected(self):
        reference = make_plan([{
            "floor": 1,
            "spaces": [
                {"name": "Stue", "type": "stue", "area": 30.0},
                {"name": "Soverom 1", "type": "soverom", "area": 12.0},
            ]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 30.0}]
        }])
        deviations = self.engine.compare(reference, current)
        categories = [d.category for d in deviations]
        assert any("UNDERBUILDING" in str(c).upper() or "ADDITION" in str(c).upper() for c in categories)

    def test_room_type_change_detected(self):
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Soverom 1", "type": "soverom", "area": 12.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Soverom 1", "type": "kontor", "area": 12.0}]
        }])
        deviations = self.engine.compare(reference, current)
        assert len(deviations) >= 1

    def test_confidence_in_valid_range(self):
        reference = make_plan([{"floor": 1, "spaces": [{"name": "Stue", "area": 30.0}]}])
        current = make_plan([{"floor": 1, "spaces": [{"name": "Stue", "area": 50.0}]}])
        deviations = self.engine.compare(reference, current)
        for dev in deviations:
            assert 0.0 <= dev.confidence <= 1.0, f"Confidence out of range: {dev.confidence}"

    def test_large_area_increase_triggers_addition(self):
        """>20% total area change should produce HIGH severity ADDITION_DETECTED."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 80.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 100.0}]
        }])
        deviations = self.engine.compare(reference, current)
        additions = [d for d in deviations if d.category == "ADDITION_DETECTED"]
        assert len(additions) >= 1
        high_severity = [d for d in additions if d.severity == "HIGH"]
        assert len(high_severity) >= 1

    def test_large_area_decrease_triggers_underbuilding(self):
        """Significant area reduction triggers UNDERBUILDING_DETECTED."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 100.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 60.0}]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "UNDERBUILDING_DETECTED" in cats

    def test_new_floor_triggers_addition(self):
        """A new floor in current plan triggers ADDITION_DETECTED."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 30.0}]
        }])
        current = make_plan([
            {"floor": 1, "spaces": [{"name": "Stue", "type": "stue", "area": 30.0}]},
            {"floor": 2, "spaces": [{"name": "Soverom", "type": "soverom", "area": 15.0}]},
        ])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "ADDITION_DETECTED" in cats

    def test_bedroom_converted_to_office_triggers_discrepancy(self):
        """Bedroom changed to office triggers BEDROOM_UTILITY_DISCREPANCY."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Soverom 2", "type": "soverom", "area": 11.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Soverom 2", "type": "kontor", "area": 11.0}]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "BEDROOM_UTILITY_DISCREPANCY" in cats, f"Categories: {cats}"

    def test_balcony_removed_triggers_discrepancy(self):
        """Balcony present in reference but missing in current triggers BALCONY_TERRACE_DISCREPANCY."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [
                {"name": "Stue", "type": "stue", "area": 25.0},
                {"name": "Balkong", "type": "balkong", "area": 8.0},
            ]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 25.0}]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "BALCONY_TERRACE_DISCREPANCY" in cats, f"Categories: {cats}"

    def test_uninspected_area_low_confidence_space(self):
        """Space with confidence < 0.5 triggers UNINSPECTED_AREA."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 30.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [
                {"name": "Stue", "type": "stue", "area": 30.0},
                {"name": "Ukjent rom", "type": "rom", "area": 12.0, "confidence": 0.3},
            ]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "UNINSPECTED_AREA" in cats, f"Categories: {cats}"

    def test_use_change_indication_residential_to_commercial(self):
        """Room changed from residential to commercial triggers USE_CHANGE_INDICATION."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 30.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "butikk", "area": 30.0}]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "USE_CHANGE_INDICATION" in cats, f"Categories: {cats}"

    def test_marketed_function_discrepancy(self):
        """Room named 'soverom' but approved as 'bod' triggers MARKETED_FUNCTION_DISCREPANCY."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Soverom 1", "type": "bod", "area": 8.0}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Soverom 1", "type": "bod", "area": 8.0}]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "MARKETED_FUNCTION_DISCREPANCY" in cats, f"Categories: {cats}"

    def test_door_placement_change_detected(self):
        """Changed door count triggers DOOR_PLACEMENT_CHANGE."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 25.0,
                        "attributes": {"door_count": 2}}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 25.0,
                        "attributes": {"door_count": 1}}]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "DOOR_PLACEMENT_CHANGE" in cats, f"Categories: {cats}"

    def test_window_placement_change_detected(self):
        """Changed window count triggers WINDOW_PLACEMENT_CHANGE."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 25.0,
                        "attributes": {"window_count": 3}}]
        }])
        current = make_plan([{
            "floor": 1,
            "spaces": [{"name": "Stue", "type": "stue", "area": 25.0,
                        "attributes": {"window_count": 1}}]
        }])
        deviations = self.engine.compare(reference, current)
        cats = [d.category for d in deviations]
        assert "WINDOW_PLACEMENT_CHANGE" in cats, f"Categories: {cats}"

    def test_all_deviations_have_norwegian_description(self):
        """All deviation descriptions must be non-empty Norwegian text."""
        reference = make_plan([{
            "floor": 1,
            "spaces": [
                {"name": "Stue", "type": "stue", "area": 30.0},
                {"name": "Soverom", "type": "soverom", "area": 12.0},
            ]
        }])
        current = make_plan([
            {
                "floor": 1,
                "spaces": [
                    {"name": "Stue", "type": "stue", "area": 30.0},
                    {"name": "Soverom", "type": "kontor", "area": 12.0},
                ]
            },
            {
                "floor": 2,
                "spaces": [{"name": "Hobbyrom", "type": "rom", "area": 18.0, "confidence": 0.4}]
            },
        ])
        deviations = self.engine.compare(reference, current)
        for dev in deviations:
            assert dev.description, "Description must not be empty"
            assert len(dev.description) > 20, f"Description too short: {dev.description!r}"

    def test_deviation_categories_are_valid_strings(self):
        """All deviation categories must be valid DeviationCategory strings."""
        from deviation_engine.engine import DeviationResult

        valid_categories = {
            "ROOM_DEFINITION_CHANGE", "BEDROOM_UTILITY_DISCREPANCY",
            "DOOR_PLACEMENT_CHANGE", "WINDOW_PLACEMENT_CHANGE",
            "BALCONY_TERRACE_DISCREPANCY", "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED", "UNINSPECTED_AREA",
            "USE_CHANGE_INDICATION", "MARKETED_FUNCTION_DISCREPANCY",
        }
        reference = make_plan([{"floor": 1, "spaces": [{"name": "Stue", "type": "stue", "area": 80.0}]}])
        current = make_plan([
            {"floor": 1, "spaces": [
                {"name": "Stue", "type": "butikk", "area": 110.0},
                {"name": "Soverom 1", "type": "kontor", "area": 15.0, "confidence": 0.3},
            ]},
            {"floor": 2, "spaces": [{"name": "Ny etasje rom", "type": "rom", "area": 20.0}]},
        ])
        deviations = self.engine.compare(reference, current)
        for dev in deviations:
            assert dev.category in valid_categories, f"Unknown category: {dev.category}"
