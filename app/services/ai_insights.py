"""
AI Insights Service — OpenAI-powered study plan generator.

When a student completes the adaptive test (10 questions), this service
sends their performance data to OpenAI and receives a personalized
3-step learning plan in JSON format.
"""

import json
import logging
from typing import List, Dict, Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from ..database import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class StudyStep(BaseModel):
    """A single step in the 3-step study plan."""
    step_number: int
    title: str
    description: str
    resources: List[str]


class StudyPlanResponse(BaseModel):
    """Complete AI-generated study plan."""
    study_plan: List[str]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AIInsightsService:
    """Integrates with OpenAI to generate personalized study plans."""

    def __init__(self) -> None:
        self.api_key: str = settings.openai_api_key
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set. AI insights will be unavailable.")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_study_plan(
        self,
        user_id: str,
        topics_missed: List[str],
        ability_score: float,
        correct_answers: int,
        wrong_answers: int,
    ) -> Dict[str, Any]:
        """
        Generate a 3-step study plan by prompting GPT with the student's
        performance data.

        Returns:
            Structured JSON with summary, weak_areas, three_step_plan,
            and estimated_time.
        """
        if not self.api_key:
            logger.error("Cannot generate study plan — API key missing.")
            return {
                "error": "OpenAI API key not configured",
                "message": "Set OPENAI_API_KEY in your .env file.",
            }

        prompt = (
            "You are an expert GRE tutor. Based on the student's performance, "
            "generate a concise 3-step study plan to improve weak areas.\n\n"
            f"Performance Data:\n"
            f"  - Ability Score Reached: {ability_score:.2f}\n"
            f"  - Correct Answers: {correct_answers}\n"
            f"  - Wrong Answers: {wrong_answers}\n"
            f"  - Topics Missed: {', '.join(topics_missed) if topics_missed else 'None'}\n\n"
            "Ensure the function returns JSON strictly in this format:\n"
            "{\n"
            '  "study_plan": [\n'
            '    "step 1",\n'
            '    "step 2",\n'
            '    "step 3"\n'
            "  ]\n"
            "}"
        )

        try:
            logger.info("Calling OpenAI for study plan — user_id=%s", user_id)
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert educational psychologist. "
                            "Return only valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            plan_data = json.loads(response.choices[0].message.content)
            logger.info("Study plan generated successfully for user_id=%s", user_id)

            # Ensure exactly 3 steps if possible
            if "study_plan" in plan_data and isinstance(plan_data["study_plan"], list):
                plan_data["study_plan"] = plan_data["study_plan"][:3]

            return plan_data

        except Exception as e:
            logger.error("OpenAI call failed: %s", str(e))
            return {
                "error": "AI service failure",
                "message": str(e),
                "fallback_plan": (
                    f"Review these topics: {', '.join(topics_missed)}"
                ),
            }


# Singleton
ai_insights_service = AIInsightsService()
