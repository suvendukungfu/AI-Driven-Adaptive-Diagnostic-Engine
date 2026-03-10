import math
from typing import List, Optional
from ..models.question_model import Question

class AdaptiveEngine:
    """
    Implements an adaptive testing algorithm using Item Response Theory (IRT).
    """

    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate

    def update_ability(self, current_ability: float, question_difficulty: float, is_correct: bool) -> float:
        """
        Calculates new ability using the logistic IRT model.
        P = 1 / (1 + e^-(ability - difficulty))
        new_ability = ability + learning_rate * (result - probability)
        """
        # P = 1 / (1 + e^-(ability - difficulty))
        probability = 1 / (1 + math.exp(-(current_ability - question_difficulty)))

        # result: 1 if correct, 0 if incorrect
        result = 1.0 if is_correct else 0.0

        # new_ability = ability + learning_rate * (result - probability)
        new_ability = current_ability + self.learning_rate * (result - probability)

        # Return ability clamped between 0.1 and 1.0
        return max(0.1, min(1.0, new_ability))

    def select_next_question(self, pool: List[Question], current_ability: float, excluded_ids: List[str]) -> Optional[Question]:
        """
        Selects the next question from the pool whose difficulty is closest to the user's ability score.
        """
        available_questions = [q for q in pool if str(q.id) not in excluded_ids]
        if not available_questions:
            return None

        # Find the question with difficulty closest to current ability score
        next_q = min(available_questions, key=lambda q: abs(q.difficulty - current_ability))
        return next_q

adaptive_engine = AdaptiveEngine()
