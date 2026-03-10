"""
Routes for adaptive testing session management.

Endpoints:
  POST /start-session                — Start a new adaptive test session
  GET  /next-question/{session_id}   — Get next question based on ability
  POST /submit-answer                — Submit an answer and update ability
  GET  /study-plan/{session_id}      — Get AI-generated study plan
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from ..database import get_database
from ..models.session_model import (
    UserSession,
    UserSessionCreate,
    SessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from ..models.question_model import Question
from ..services.adaptive_engine import adaptive_engine
from ..services.ai_insights import ai_insights_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Adaptive Testing"])

MAX_QUESTIONS = 10  # Test completes after this many answers


# ── Helpers ────────────────────────────────────────────────────────────

def _validate_object_id(value: str, name: str = "ID") -> ObjectId:
    """Validate and convert a string to ObjectId."""
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"Invalid {name} format")
    return ObjectId(value)


def _serialize_session(doc: dict) -> SessionResponse:
    """Convert a MongoDB session document to a SessionResponse."""
    return SessionResponse(
        session_id=str(doc["_id"]),
        user_id=doc["user_id"],
        ability_score=doc.get("ability_score", 0.5),
        correct_count=doc.get("correct_count", 0),
        wrong_count=doc.get("wrong_count", 0),
        answered_questions=doc.get("answered_questions", []),
        topics_missed=doc.get("topics_missed", []),
        current_question=doc.get("current_question"),
        status=doc.get("status", "active"),
    )


# ── POST /start-session ───────────────────────────────────────────────

@router.post("/start-session", response_model=SessionResponse)
async def start_session(
    body: UserSessionCreate,
    db=Depends(get_database),
) -> SessionResponse:
    """
    Create a new adaptive testing session.
    Ability score is initialized to **0.5**.
    """
    session = UserSession(user_id=body.user_id, ability_score=0.5)
    doc = session.model_dump(by_alias=True)
    result = await db.user_sessions.insert_one(doc)
    created = await db.user_sessions.find_one({"_id": result.inserted_id})
    logger.info("Session started: user_id=%s session_id=%s", body.user_id, result.inserted_id)
    return _serialize_session(created)


# ── GET /next-question/{session_id} ───────────────────────────────────

@router.get("/next-question/{session_id}", response_model=Question)
async def get_next_question(
    session_id: str,
    db=Depends(get_database),
) -> Question:
    """
    Return the next question whose difficulty is closest to the
    student's current ability score.
    """
    oid = _validate_object_id(session_id, "session_id")
    session_doc = await db.user_sessions.find_one({"_id": oid})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")

    session = UserSession(**session_doc)

    # Completion check
    if len(session.answered_questions) >= MAX_QUESTIONS:
        raise HTTPException(status_code=400, detail="test completed")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Fetch pool & select
    all_docs = await db.questions.find().to_list(1000)
    pool = [Question(**q) for q in all_docs]
    next_q = adaptive_engine.select_next_question(
        pool, session.ability_score, session.answered_questions,
    )

    if not next_q:
        await db.user_sessions.update_one(
            {"_id": oid},
            {"$set": {"status": "completed", "end_time": datetime.utcnow()}},
        )
        raise HTTPException(status_code=404, detail="No more questions available")

    # Track current question in session
    await db.user_sessions.update_one(
        {"_id": oid},
        {"$set": {"current_question": str(next_q.id)}},
    )

    logger.info("Next question: session=%s question=%s", session_id, next_q.id)
    return next_q


# ── POST /submit-answer ───────────────────────────────────────────────

@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    body: SubmitAnswerRequest,
    db=Depends(get_database),
) -> SubmitAnswerResponse:
    """
    Submit an answer.  The system will:
    1. Validate the answer.
    2. Update the ability score using the IRT formula.
    3. Update correct/wrong counts.
    4. Store the answered question.

    If 10 questions have been answered → return **"test completed"**.
    """
    s_oid = _validate_object_id(body.session_id, "session_id")
    q_oid = _validate_object_id(body.question_id, "question_id")

    # Fetch session
    session_doc = await db.user_sessions.find_one({"_id": s_oid})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    session = UserSession(**session_doc)

    if len(session.answered_questions) >= MAX_QUESTIONS:
        raise HTTPException(status_code=400, detail="test completed")

    # Fetch question
    question_doc = await db.questions.find_one({"_id": q_oid})
    if not question_doc:
        raise HTTPException(status_code=404, detail="Question not found")
    question = Question(**question_doc)

    # 1. Check correctness
    is_correct = body.answer == question.correct_answer

    # 2. IRT ability update
    new_ability = adaptive_engine.update_ability(
        session.ability_score, question.difficulty, is_correct,
    )

    # 3. Build update query
    new_correct = session.correct_count + (1 if is_correct else 0)
    new_wrong = session.wrong_count + (0 if is_correct else 1)
    answered = session.answered_questions + [body.question_id]

    update: Dict[str, Any] = {
        "$push": {"answered_questions": body.question_id},
        "$set": {
            "ability_score": new_ability,
            "current_question": None,
        },
    }

    if is_correct:
        update["$inc"] = {"correct_count": 1}
    else:
        update["$inc"] = {"wrong_count": 1}
        update.setdefault("$addToSet", {})["topics_missed"] = question.topic

    # 4. Completion check
    message = "Answer recorded"
    if len(answered) >= MAX_QUESTIONS:
        update["$set"]["status"] = "completed"
        update["$set"]["end_time"] = datetime.utcnow()
        message = "test completed"

    await db.user_sessions.update_one({"_id": s_oid}, update)

    logger.info(
        "Answer submitted: session=%s correct=%s ability=%.3f",
        body.session_id, is_correct, new_ability,
    )

    return SubmitAnswerResponse(
        is_correct=is_correct,
        new_ability_score=new_ability,
        correct_count=new_correct,
        wrong_count=new_wrong,
        message=message,
    )


# ── GET /study-plan/{session_id} ──────────────────────────────────────

@router.get("/study-plan/{session_id}")
async def get_study_plan(
    session_id: str,
    db=Depends(get_database),
) -> Dict[str, Any]:
    """
    Generate an AI-powered 3-step study plan based on the student's
    performance in the completed session.
    """
    oid = _validate_object_id(session_id, "session_id")
    session_doc = await db.user_sessions.find_one({"_id": oid})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")

    session = UserSession(**session_doc)

    if not session.answered_questions:
        raise HTTPException(status_code=400, detail="No answers submitted yet")

    plan = await ai_insights_service.generate_study_plan(
        user_id=session.user_id,
        topics_missed=session.topics_missed,
        ability_score=session.ability_score,
        correct_answers=session.correct_count,
        wrong_answers=session.wrong_count,
    )
    return plan
