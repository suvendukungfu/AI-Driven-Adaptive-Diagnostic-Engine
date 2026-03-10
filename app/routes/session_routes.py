from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..database import get_database
from ..models.session_model import UserSession, UserSessionCreate
from ..models.question_model import Question
from ..services.adaptive_engine import adaptive_engine

router = APIRouter(tags=["Adaptive Testing"])

@router.post("/start-session", response_model=UserSession)
async def start_session(session_data: UserSessionCreate, db = Depends(get_database)):
    """
    Creates a new test session and initializes ability score to 0.5.
    """
    new_session = UserSession(
        user_id=session_data.user_id,
        ability_score=0.5  # Initial ability score = 0.5
    ).model_dump(by_alias=True)
    
    result = await db.user_sessions.insert_one(new_session)
    created_session = await db.user_sessions.find_one({"_id": result.inserted_id})
    return created_session

@router.get("/next-question/{session_id}", response_model=Question)
async def get_next_question(session_id: str, db = Depends(get_database)):
    """
    Returns the next question based on the user's ability score.
    """
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session_data = await db.user_sessions.find_one({"_id": ObjectId(session_id)})
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = UserSession(**session_data)
    
    # Check for completion (10 questions)
    if len(session.answered_questions) >= 10:
        raise HTTPException(status_code=400, detail="test completed")
        
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Get all questions
    all_questions_data = await db.questions.find().to_list(1000)
    all_questions = [Question(**q) for q in all_questions_data]

    next_q = adaptive_engine.select_next_question(all_questions, session.ability_score, session.answered_questions)

    if not next_q:
        await db.user_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"status": "completed", "end_time": datetime.utcnow()}}
        )
        raise HTTPException(status_code=404, detail="No more questions available.")

    return next_q

@router.post("/submit-answer", response_model=UserSession)
async def submit_answer(
    session_id: str = Body(...),
    question_id: str = Body(...),
    answer: str = Body(...),
    db = Depends(get_database)
):
    """
    Submits an answer, updates ability score, and increments counts.
    """
    if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="Invalid ID")

    session_data = await db.user_sessions.find_one({"_id": ObjectId(session_id)})
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    session = UserSession(**session_data)

    if len(session.answered_questions) >= 10:
         return {"message": "test completed", "session": session}

    question_data = await db.questions.find_one({"_id": ObjectId(question_id)})
    if not question_data:
        raise HTTPException(status_code=404, detail="Question not found")
    question = Question(**question_data)

    # Check if answer is correct
    is_correct = (answer == question.correct_answer)

    # Update ability score using IRT formula (via service)
    new_ability = adaptive_engine.update_ability(
        session.ability_score,
        question.difficulty,
        is_correct
    )

    update_query = {
        "$push": {"answered_questions": question_id},
        "$set": {"ability_score": new_ability}
    }

    if is_correct:
        update_query["$inc"] = {"correct_count": 1}
    else:
        update_query["$inc"] = {"wrong_count": 1}
        update_query["$addToSet"] = {"topics_missed": question.topic}

    # Check for completion after this answer
    if len(session.answered_questions) + 1 >= 10:
        update_query["$set"]["status"] = "completed"
        update_query["$set"]["end_time"] = datetime.utcnow()

    updated_session = await db.user_sessions.find_one_and_update(
        {"_id": ObjectId(session_id)},
        update_query,
        return_document=True
    )
    
    if len(session.answered_questions) + 1 >= 10:
        # Return special message if completed
        result_session = UserSession(**updated_session)
        # We can't easily return a union type with response_model=UserSession 
        # so we'll just return the session and let the user see the status.
        # But for strictly following "return test completed", we can raise a 200 exception-like or just return it.
        # Let's return the session and mention completion in the response.
        return result_session

    return updated_session
