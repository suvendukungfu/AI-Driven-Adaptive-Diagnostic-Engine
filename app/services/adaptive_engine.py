"""
Adaptive Testing Engine using Item Response Theory (IRT).

IRT is a psychometric framework used to model the interaction between a
test-taker's latent ability (θ) and an item's properties (difficulty β).

──────────────────────────────────────────────────────────────────────────
1-PARAMETER LOGISTIC MODEL (1PL / RASCH MODEL)
──────────────────────────────────────────────────────────────────────────

The probability that a student with ability θ answers a question with
difficulty β correctly is given by the logistic function:

    P(correct) = 1 / (1 + e^{-(θ - β)})

  • When θ = β  → P = 0.50  (50% chance — maximum information)
  • When θ > β  → P > 0.50  (easy question for this student)
  • When θ < β  → P < 0.50  (hard question for this student)

──────────────────────────────────────────────────────────────────────────
ABILITY UPDATE RULE
──────────────────────────────────────────────────────────────────────────

After each response we update the ability estimate:

    θ_new = θ_old + α × (result − P)

Where:
  • α   = learning rate (0.1 by default)
  • result = 1.0 if correct, 0.0 if incorrect
  • P   = probability from the logistic model above

Intuition:
  → Correct on a hard item  (P low)  → large positive push
  → Correct on an easy item (P high) → small positive push
  → Wrong on a hard item    (P low)  → small negative push
  → Wrong on an easy item   (P high) → large negative push

The ability is clamped to [0.1, 1.0] to stay within the difficulty range.

──────────────────────────────────────────────────────────────────────────
NEXT-QUESTION SELECTION
──────────────────────────────────────────────────────────────────────────

We select the question whose difficulty is closest to the current ability
estimate. This maximises the Fisher information of the item, giving the
most precise measurement of the student's true ability.
"""

import math
import logging
from typing import List, Optional

from ..models.question_model import Question

logger = logging.getLogger(__name__)


class AdaptiveEngine:
    """Core adaptive testing engine powered by IRT."""

    def __init__(self, learning_rate: float = 0.1) -> None:
        """
        Args:
            learning_rate: Step-size for ability updates (α).
        """
        self.learning_rate = learning_rate

    # ── IRT probability ────────────────────────────────────────────────
    @staticmethod
    def _irt_probability(ability: float, difficulty: float) -> float:
        """
        Compute the probability of a correct response using the
        1PL logistic IRT model.

        Formula:  P = 1 / (1 + e^{-(ability - difficulty)})
        """
        return 1.0 / (1.0 + math.exp(-(ability - difficulty)))

    # ── Ability update ─────────────────────────────────────────────────
    def update_ability(
        self,
        current_ability: float,
        question_difficulty: float,
        is_correct: bool,
    ) -> float:
        """
        Update the student's ability estimate after answering a question.

        Steps:
          1. Compute P(correct) via the IRT logistic model.
          2. Determine the result (1 if correct, 0 if wrong).
          3. Apply:  θ_new = θ_old + α × (result − P)
          4. Clamp to [0.1, 1.0].
        """
        # Step 1 — IRT probability
        probability = self._irt_probability(current_ability, question_difficulty)

        # Step 2 — Actual result
        result = 1.0 if is_correct else 0.0

        # Step 3 — Update rule
        new_ability = current_ability + self.learning_rate * (result - probability)

        # Step 4 — Clamp between 0.1 and 1.0
        clamped = max(0.1, min(1.0, new_ability))

        logger.info(
            "IRT update: ability=%.3f difficulty=%.2f correct=%s "
            "P=%.3f → new_ability=%.3f",
            current_ability, question_difficulty, is_correct,
            probability, clamped,
        )
        return clamped

    # ── Question selection ─────────────────────────────────────────────
    def select_next_question(
        self,
        pool: List[Question],
        current_ability: float,
        excluded_ids: List[str],
    ) -> Optional[Question]:
        """
        Select the next question using the Maximum Information Criterion.
        
        Requirements met:
        1. Do not repeat questions already answered (filtered via excluded_ids).
        2. Choose the question whose difficulty is closest to the user's ability score.
        3. Query MongoDB excluding answered questions (handled before parameter passing).

        Why this improves adaptive testing accuracy:
        In Item Response Theory (IRT), an item provides the maximum statistical 
        information (precision) about a student's ability when the item's difficulty 
        (β) exactly matches the student's current ability estimate (θ). 
        
        By selecting the question where |difficulty - ability| is minimized, 
        we ensure that the test converges quickly onto the student's true ability 
        level with the fewest number of questions.
        """
        available = [q for q in pool if str(q.id) not in excluded_ids]
        if not available:
            logger.warning("No available questions left in pool.")
            return None

        # Compute absolute difference between ability and difficulty
        # Return the question with the smallest difference
        best = min(available, key=lambda q: abs(q.difficulty - current_ability))
        logger.info(
            "Selected question difficulty=%.2f for ability=%.3f",
            best.difficulty, current_ability,
        )
        return best


# Singleton instance used across the application
adaptive_engine = AdaptiveEngine()
