from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .question_model import PyObjectId

class UserSessionBase(BaseModel):
    ability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    correct_count: int = 0
    wrong_count: int = 0
    answered_questions: List[str] = []  # List of question IDs
    topics_missed: List[str] = []
    status: str = "active"
    start_time: datetime = Field(default_factory=datetime.utcnow)

class UserSessionCreate(BaseModel):
    user_id: str

class UserSession(UserSessionBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    end_time: Optional[datetime] = None

    @property
    def session_id(self) -> str:
        return str(self.id) if self.id else None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True
    }
