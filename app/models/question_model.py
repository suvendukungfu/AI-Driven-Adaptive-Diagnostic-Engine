"""
Pydantic models for the 'questions' MongoDB collection.

Fields:
  - question:        The question text
  - options:         4 multiple-choice options
  - correct_answer:  The correct option text
  - difficulty:      Float 0.1 – 1.0
  - topic:           Subject area
  - tags:            List of labels
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2 compatibility."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}


class QuestionCreate(BaseModel):
    """Schema for creating a new question."""
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., min_length=2, max_length=6, description="Multiple-choice options")
    correct_answer: str = Field(..., description="The correct option (must match one of 'options')")
    difficulty: float = Field(..., ge=0.1, le=1.0, description="Difficulty level 0.1–1.0")
    topic: str = Field(..., description="Subject category")
    tags: List[str] = Field(default=[], description="Labels for filtering")

    @field_validator("correct_answer")
    @classmethod
    def correct_answer_must_be_in_options(cls, v, info):
        if "options" in info.data and v not in info.data["options"]:
            raise ValueError("correct_answer must be one of the options")
        return v


class Question(QuestionCreate):
    """Full question document returned from MongoDB."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True,
    }


# ---------------------------------------------------------------------------
# Response models for Swagger documentation
# ---------------------------------------------------------------------------

class QuestionResponse(BaseModel):
    """Serialized question returned in API responses."""
    id: str = Field(..., description="MongoDB document ID")
    question: str
    options: List[str]
    correct_answer: str
    difficulty: float
    topic: str
    tags: List[str] = []
