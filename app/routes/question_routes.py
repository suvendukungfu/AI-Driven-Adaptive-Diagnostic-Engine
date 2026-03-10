from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..database import get_database
from ..models.question_model import Question, QuestionCreate
from bson import ObjectId

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/", response_model=Question)
async def create_question(question: QuestionCreate, db = Depends(get_database)):
    new_question = question.model_dump(by_alias=True)
    result = await db.questions.insert_one(new_question)
    created_question = await db.questions.find_one({"_id": result.inserted_id})
    return created_question

@router.get("/", response_model=List[Question])
async def get_questions(db = Depends(get_database)):
    questions = await db.questions.find().to_list(100)
    return questions

@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str, db = Depends(get_database)):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    question = await db.questions.find_one({"_id": ObjectId(question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question
