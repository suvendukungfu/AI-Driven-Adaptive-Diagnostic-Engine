"""
Unit tests for the AdaptiveEngine class.

Tests verify:
  - IRT probability computation
  - Ability update in correct / incorrect scenarios
  - Clamping to [0.1, 1.0]
  - Next-question selection (closest difficulty)
  - Exclusion of already-answered questions
  - Edge cases (empty pool, boundary values)
"""

import math
import pytest

from app.services.adaptive_engine import AdaptiveEngine


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def engine() -> AdaptiveEngine:
    """Default engine with learning_rate = 0.1."""
    return AdaptiveEngine(learning_rate=0.1)


class MockQuestion:
    """Minimal question stub for testing."""
    def __init__(self, id: str, difficulty: float):
        self.id = id
        self.difficulty = difficulty


# ── IRT Probability Tests ─────────────────────────────────────────────

class TestIRTProbability:
    """Verify the logistic IRT probability formula."""

    def test_equal_ability_and_difficulty(self, engine):
        """When θ == β, P should be exactly 0.5."""
        p = engine._irt_probability(0.5, 0.5)
        assert p == 0.5

    def test_high_ability_gives_high_probability(self, engine):
        """When θ >> β, P should approach 1.0."""
        p = engine._irt_probability(1.0, 0.1)
        assert p > 0.7

    def test_low_ability_gives_low_probability(self, engine):
        """When θ << β, P should approach 0.0."""
        p = engine._irt_probability(0.1, 1.0)
        assert p < 0.3


# ── Ability Update Tests ──────────────────────────────────────────────

class TestAbilityUpdate:
    """Verify the ability update rule: θ_new = θ + α × (result − P)."""

    def test_correct_increases_ability(self, engine):
        """Correct answer → ability should increase."""
        # P(0.5, 0.5) = 0.5; new = 0.5 + 0.1*(1.0 - 0.5) = 0.55
        new = engine.update_ability(0.5, 0.5, is_correct=True)
        assert new == pytest.approx(0.55)

    def test_incorrect_decreases_ability(self, engine):
        """Incorrect answer → ability should decrease."""
        # P(0.5, 0.5) = 0.5; new = 0.5 + 0.1*(0.0 - 0.5) = 0.45
        new = engine.update_ability(0.5, 0.5, is_correct=False)
        assert new == pytest.approx(0.45)

    def test_correct_on_hard_item_big_jump(self, engine):
        """Correct on a hard item should give a bigger ability increase."""
        # ability = 0.3, difficulty = 0.9 → P is low → big positive push
        new = engine.update_ability(0.3, 0.9, is_correct=True)
        delta = new - 0.3
        assert delta > 0.05  # Larger than the equal-difficulty case

    def test_wrong_on_easy_item_big_drop(self, engine):
        """Wrong on an easy item should give a bigger ability decrease."""
        # ability = 0.8, difficulty = 0.2 → P is high → big negative push
        new = engine.update_ability(0.8, 0.2, is_correct=False)
        delta = new - 0.8
        assert delta < -0.05


# ── Clamping Tests ────────────────────────────────────────────────────

class TestClamping:
    """Ability must always be clamped to [0.1, 1.0]."""

    def test_upper_clamp(self, engine):
        new = engine.update_ability(0.99, 0.1, is_correct=True)
        assert new <= 1.0

    def test_lower_clamp(self, engine):
        new = engine.update_ability(0.11, 0.9, is_correct=False)
        assert new >= 0.1

    def test_all_results_within_bounds(self, engine):
        """Exhaustive check across many ability/difficulty combos."""
        for ability in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
            for difficulty in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
                for correct in [True, False]:
                    result = engine.update_ability(ability, difficulty, correct)
                    assert 0.1 <= result <= 1.0


# ── Question Selection Tests ─────────────────────────────────────────

class TestQuestionSelection:
    """Verify the closest-difficulty selection strategy."""

    def test_selects_closest_difficulty(self, engine):
        pool = [MockQuestion("1", 0.2), MockQuestion("2", 0.5), MockQuestion("3", 0.8)]
        selected = engine.select_next_question(pool, 0.45, [])
        assert selected.id == "2"  # 0.5 is closest to 0.45

    def test_excludes_answered_questions(self, engine):
        pool = [MockQuestion("1", 0.5), MockQuestion("2", 0.6)]
        selected = engine.select_next_question(pool, 0.48, ["1"])
        assert selected.id == "2"

    def test_returns_none_when_pool_exhausted(self, engine):
        pool = [MockQuestion("1", 0.5)]
        selected = engine.select_next_question(pool, 0.5, ["1"])
        assert selected is None

    def test_empty_pool(self, engine):
        selected = engine.select_next_question([], 0.5, [])
        assert selected is None
