import math
import pytest
from app.services.adaptive_engine import AdaptiveEngine

@pytest.fixture
def engine():
    return AdaptiveEngine(learning_rate=0.1)

def test_probability_calculation(engine):
    # If ability = difficulty, P should be 0.5
    prob = 1 / (1 + math.exp(-(0.5 - 0.5)))
    assert prob == 0.5

def test_correct_response_increases_ability(engine):
    initial_ability = 0.5
    difficulty = 0.5
    # P = 0.5, result = 1.0, learning_rate = 0.1
    # new = 0.5 + 0.1 * (1.0 - 0.5) = 0.5 + 0.05 = 0.55
    new_ability = engine.update_ability(initial_ability, difficulty, True)
    assert new_ability == 0.55

def test_incorrect_response_decreases_ability(engine):
    initial_ability = 0.5
    difficulty = 0.5
    # P = 0.5, result = 0.0
    # new = 0.5 + 0.1 * (0.0 - 0.5) = 0.5 - 0.05 = 0.45
    new_ability = engine.update_ability(initial_ability, difficulty, False)
    assert new_ability == 0.45

def test_clamping_upper_limit(engine):
    # Ability near limit, correct answer
    new_ability = engine.update_ability(0.99, 0.1, True)
    assert new_ability <= 1.0
    assert new_ability >= 0.1

def test_clamping_lower_limit(engine):
    # Ability near limit, incorrect answer
    new_ability = engine.update_ability(0.11, 0.9, False)
    assert new_ability >= 0.1
    assert new_ability <= 1.0

def test_select_next_question_closest_difficulty(engine):
    class MockQuestion:
        def __init__(self, id, difficulty):
            self.id = id
            self.difficulty = difficulty

    pool = [
        MockQuestion("1", 0.2),
        MockQuestion("2", 0.5),
        MockQuestion("3", 0.8)
    ]
    
    # ability = 0.4, closest is 0.5 (ID 2)
    selected = engine.select_next_question(pool, 0.4, [])
    assert selected.id == "2"

    # ability = 0.9, closest is 0.8 (ID 3)
    selected = engine.select_next_question(pool, 0.9, [])
    assert selected.id == "3"

def test_exclude_already_answered(engine):
    class MockQuestion:
        def __init__(self, id, difficulty):
            self.id = id
            self.difficulty = difficulty

    pool = [
        MockQuestion("1", 0.5),
        MockQuestion("2", 0.6)
    ]
    
    # ability = 0.48, ID 1 is closest, but excluded
    selected = engine.select_next_question(pool, 0.48, ["1"])
    assert selected.id == "2"
