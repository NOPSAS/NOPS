"""Unit tests for RuleRegistry, RuleMatcher, RuleExplainer."""
import sys
import os
import pytest
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../../services"))

from rule_engine.registry import RuleRegistry, RuleMatcher, RuleExplainer


@dataclass
class MockDeviationResult:
    category: str
    severity: str = "MEDIUM"
    description: str = "Test avvik"
    confidence: float = 0.8
    evidence_references: list = None

    def __post_init__(self):
        if self.evidence_references is None:
            self.evidence_references = []


class TestRuleRegistry:

    def setup_method(self):
        self.registry = RuleRegistry()

    def test_load_rules_returns_list(self):
        rules = self.registry.load_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_all_rules_have_required_fields(self):
        for rule in self.registry.load_rules():
            assert hasattr(rule, "rule_code")
            assert hasattr(rule, "title")
            assert hasattr(rule, "applies_to_categories")
            assert isinstance(rule.applies_to_categories, list)

    def test_get_rule_by_code(self):
        rules = self.registry.load_rules()
        first_code = rules[0].rule_code
        found = self.registry.get_rule(first_code)
        assert found is not None
        assert found.rule_code == first_code

    def test_get_nonexistent_rule_returns_none(self):
        result = self.registry.get_rule("NONEXISTENT-999")
        assert result is None


class TestRuleMatcher:

    def setup_method(self):
        registry = RuleRegistry()
        self.matcher = RuleMatcher(registry)

    def test_finds_matches_for_addition_detected(self):
        deviation = MockDeviationResult(category="ADDITION_DETECTED")
        matches = self.matcher.find_matching_rules(deviation)
        # Should find at least PBL-20-1
        assert len(matches) >= 1

    def test_finds_matches_for_bedroom_discrepancy(self):
        deviation = MockDeviationResult(category="BEDROOM_UTILITY_DISCREPANCY")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) >= 1

    def test_no_matches_for_unknown_category(self):
        deviation = MockDeviationResult(category="NONEXISTENT_CATEGORY")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) == 0

    def test_match_has_confidence_in_range(self):
        deviation = MockDeviationResult(category="ROOM_DEFINITION_CHANGE")
        matches = self.matcher.find_matching_rules(deviation)
        for match in matches:
            assert 0.0 <= match.confidence <= 1.0

    def test_match_has_norwegian_rationale(self):
        deviation = MockDeviationResult(category="ADDITION_DETECTED")
        matches = self.matcher.find_matching_rules(deviation)
        if matches:
            assert len(matches[0].rationale) > 10  # Non-empty Norwegian text

    def test_finds_matches_for_door_placement_change(self):
        deviation = MockDeviationResult(category="DOOR_PLACEMENT_CHANGE")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) >= 1, "Expected at least one rule for DOOR_PLACEMENT_CHANGE"

    def test_finds_matches_for_window_placement_change(self):
        deviation = MockDeviationResult(category="WINDOW_PLACEMENT_CHANGE")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) >= 1, "Expected at least one rule for WINDOW_PLACEMENT_CHANGE"

    def test_finds_matches_for_balcony_terrace_discrepancy(self):
        deviation = MockDeviationResult(category="BALCONY_TERRACE_DISCREPANCY")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) >= 1, "Expected at least one rule for BALCONY_TERRACE_DISCREPANCY"

    def test_finds_matches_for_marketed_function_discrepancy(self):
        deviation = MockDeviationResult(category="MARKETED_FUNCTION_DISCREPANCY")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) >= 1, "Expected at least one rule for MARKETED_FUNCTION_DISCREPANCY"

    def test_finds_matches_for_use_change_indication(self):
        deviation = MockDeviationResult(category="USE_CHANGE_INDICATION")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) >= 1, "Expected at least one rule for USE_CHANGE_INDICATION"

    def test_finds_matches_for_uninspected_area(self):
        deviation = MockDeviationResult(category="UNINSPECTED_AREA")
        matches = self.matcher.find_matching_rules(deviation)
        assert len(matches) >= 1, "Expected at least one rule for UNINSPECTED_AREA"

    def test_all_deviation_categories_have_rules(self):
        """Every DeviationCategory must have at least 2 matching rules."""
        all_categories = [
            "ROOM_DEFINITION_CHANGE",
            "BEDROOM_UTILITY_DISCREPANCY",
            "DOOR_PLACEMENT_CHANGE",
            "WINDOW_PLACEMENT_CHANGE",
            "BALCONY_TERRACE_DISCREPANCY",
            "ADDITION_DETECTED",
            "UNDERBUILDING_DETECTED",
            "UNINSPECTED_AREA",
            "USE_CHANGE_INDICATION",
            "MARKETED_FUNCTION_DISCREPANCY",
        ]
        for cat in all_categories:
            deviation = MockDeviationResult(category=cat)
            matches = self.matcher.find_matching_rules(deviation)
            assert len(matches) >= 2, (
                f"Category '{cat}' has only {len(matches)} rule(s) – need at least 2"
            )


class TestRuleExplainer:

    def setup_method(self):
        registry = RuleRegistry()
        rule = registry.load_rules()[0]
        self.explainer = RuleExplainer()
        self.rule = rule

    def test_explain_returns_string(self):
        deviation = MockDeviationResult(category="ADDITION_DETECTED")
        text = self.explainer.explain(self.rule, deviation)
        assert isinstance(text, str)
        assert len(text) > 10

    def test_explanation_no_forbidden_words(self):
        """Faglig prinsipp: systemet bruker aldri kategoriske juridiske konklusjoner."""
        deviation = MockDeviationResult(category="ADDITION_DETECTED")
        text = self.explainer.explain(self.rule, deviation).lower()
        forbidden = ["ulovlig", "er godkjent", "krever søknad"]
        for word in forbidden:
            assert word not in text, f"Forbidden word '{word}' found in explanation"
