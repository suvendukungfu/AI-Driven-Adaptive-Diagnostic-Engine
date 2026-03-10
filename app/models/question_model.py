from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}

class QuestionBase(BaseModel):
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., min_length=2)
    correct_answer: str = Field(..., description="The exact text of the correct answer")
    difficulty: float = Field(..., ge=0.1, le=1.0, description="Difficulty level from 0.1 to 1.0")
    topic: str
    tags: List[str] = []

    @field_validator('correct_answer')
    @classmethod
    def validate_correct_answer(cls, v, info):
        if 'options' in info.data and v not in info.data['options']:
            raise ValueError("correct_answer must be one of the options")
        return v

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True
    }
