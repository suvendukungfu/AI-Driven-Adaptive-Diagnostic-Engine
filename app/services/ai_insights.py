import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from ..database import settings

# Configure logging
logger = logging.getLogger(__name__)

class StudyStep(BaseModel):
    step_number: int
    title: str
    description: str
    resources: List[str]

class StudyPlan(BaseModel):
    user_id: str
    summary: str
    weak_areas: List[str]
    three_step_plan: List[StudyStep] = Field(..., max_length=3, min_length=3)
    estimated_time: str

class AIInsightsService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set in environment variables.")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_study_plan(
        self, 
        user_id: str,
        topics_missed: List[str],
        ability_score: float,
        correct_answers: int,
        wrong_answers: int
    ) -> Dict[str, Any]:
        """
        Generates a personalized 3-step study plan using OpenAI based on student performance.
        """
        if not self.api_key:
            return {
                "error": "OpenAI API key not configured",
                "message": "Please set OPENAI_API_KEY in your .env file."
            }

        prompt = f"""
        Generate a personalized 3-step study plan for a student based on their performance data:
        - User ID: {user_id}
        - Topics Missed: {', '.join(topics_missed) if topics_missed else 'None'}
        - Ability Score Reached: {ability_score:.2f}
        - Total Correct: {correct_answers}
        - Total Wrong: {wrong_answers}

        The plan must focus on improving the specific weak areas identified in 'Topics Missed'.
        
        Return the result as a structured JSON object with the following keys:
        - user_id: string
        - summary: a brief overview of performance
        - weak_areas: list of strings
        - three_step_plan: a list of exactly 3 steps, each with 'step_number', 'title', 'description', and 'resources' (list of suggested links or materials)
        - estimated_time: string (e.g., '5 hours per week')
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview", # or gpt-3.5-turbo-0125
                messages=[
                    {"role": "system", "content": "You are an expert AI educational tutor specializing in adaptive learning and personalized study plans."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            plan_data = json.loads(response.choices[0].message.content)
            
            # Basic validation check for 3 steps
            if "three_step_plan" in plan_data and len(plan_data["three_step_plan"]) != 3:
                logger.warning(f"AI generated {len(plan_data['three_step_plan'])} steps instead of 3. Adjusting...")
                plan_data["three_step_plan"] = plan_data["three_step_plan"][:3]

            return plan_data

        except Exception as e:
            logger.error(f"Error generating AI study plan: {str(e)}")
            return {
                "error": "AI service failure",
                "message": str(e),
                "fallback_plan": "Review the following topics: " + ", ".join(topics_missed)
            }

ai_insights_service = AIInsightsService()
