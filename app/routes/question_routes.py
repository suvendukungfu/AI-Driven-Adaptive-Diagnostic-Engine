"""
Routes for question management.

Endpoints:
  GET  /questions/        — List all questions
  POST /questions/        — Create a new question
  GET  /questions/{id}    — Get a single question
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from ..database import get_database
from ..models.question_model import Question, QuestionCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/", response_model=Question)
async def create_question(
    question: QuestionCreate,
    db=Depends(get_database),
) -> Question:
    """Insert a new question into MongoDB."""
    doc = question.model_dump(by_alias=True)
    result = await db.questions.insert_one(doc)
    created = await db.questions.find_one({"_id": result.inserted_id})
    logger.info("Created question id=%s", result.inserted_id)
    return created


@router.get("/", response_model=List[Question])
async def list_questions(db=Depends(get_database)) -> List[Question]:
    """Return all questions from the database."""
    questions = await db.questions.find().to_list(1000)
    return questions


@router.get("/{question_id}", response_model=Question)
async def get_question(
    question_id: str,
    db=Depends(get_database),
) -> Question:
    """Return a single question by its ID."""
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="Invalid question ID format")
    question = await db.questions.find_one({"_id": ObjectId(question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question
