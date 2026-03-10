"""
Pydantic models for the 'user_sessions' MongoDB collection.

Fields:
  - user_id:             Unique student identifier
  - ability_score:       IRT ability estimate (starts at 0.5)
  - correct_count:       Number of correct answers
  - wrong_count:         Number of wrong answers
  - answered_questions:  List of answered question IDs
  - topics_missed:       Unique topics where user answered incorrectly
  - current_question:    ID of the question currently being presented
  - status:              'active' or 'completed'
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .question_model import PyObjectId


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

class UserSessionCreate(BaseModel):
    """Request body for POST /start-session."""
    user_id: str = Field(..., description="Unique identifier for the student")


class UserSession(BaseModel):
    """Full session document stored in MongoDB."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    ability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    correct_count: int = 0
    wrong_count: int = 0
    answered_questions: List[str] = Field(default_factory=list)
    topics_missed: List[str] = Field(default_factory=list)
    current_question: Optional[str] = None
    status: str = "active"
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None

    @property
    def session_id(self) -> str:
        return str(self.id) if self.id else None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True,
    }


# ---------------------------------------------------------------------------
# Response models for Swagger documentation
# ---------------------------------------------------------------------------

class SessionResponse(BaseModel):
    """Serialized session returned in API responses."""
    session_id: str = Field(..., description="MongoDB document ID")
    user_id: str
    ability_score: float
    correct_count: int
    wrong_count: int
    answered_questions: List[str]
    topics_missed: List[str]
    current_question: Optional[str] = None
    status: str


class SessionSummaryResponse(BaseModel):
    """Bonus Feature - Response for GET /session-summary/{session_id}"""
    ability_score: float
    correct_answers: int
    wrong_answers: int
    weak_topics: List[str]


class SubmitAnswerRequest(BaseModel):

    """Request body for POST /submit-answer."""
    session_id: str
    question_id: str
    answer: str


class SubmitAnswerResponse(BaseModel):
    """Response for POST /submit-answer."""
    is_correct: bool
    new_ability_score: float
    correct_count: int
    wrong_count: int
    message: str
