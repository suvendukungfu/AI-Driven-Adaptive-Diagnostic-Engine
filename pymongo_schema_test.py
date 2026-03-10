import asyncio
import os
from pymongo import MongoClient
from pydantic import ValidationError
from app.models.question_model import QuestionCreate
from app.models.session_model import UserSession

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "adaptive_test_db")

def test_pymongo_integration():
    """
    Demonstrates using pymongo with updated Pydantic models and schema validation.
    """
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("--- Question Validation Test ---")
    valid_q = {
        "question": "What is 10 + 10?",
        "options": ["10", "20", "30"],
        "correct_answer": "20",
        "difficulty": 0.1,
        "topic": "Math"
    }
    
    try:
        q_model = QuestionCreate(**valid_q)
        print("Pydantic validation passed for Question.")
        # Insert using pymongo
        res = db.questions.insert_one(q_model.model_dump())
        print(f"Inserted question with ID: {res.inserted_id}")
    except ValidationError as e:
        print(f"Pydantic validation failed: {e}")

    print("\n--- User Session Validation Test ---")
    valid_session = {
        "user_id": "user_123",
        "ability_score": 0.7,
        "correct_count": 5,
        "wrong_count": 2,
        "answered_questions": [str(ObjectId()) for _ in range(7)],
        "topics_missed": ["History"]
    }
    
    try:
        s_model = UserSession(**valid_session)
        print("Pydantic validation passed for UserSession.")
        res = db.user_sessions.insert_one(s_model.model_dump(by_alias=True))
        print(f"Inserted session with ID: {res.inserted_id}")
    except ValidationError as e:
        print(f"Pydantic validation failed: {e}")

    print("\n--- Failed Validation Test (Invalid Difficulty) ---")
    invalid_q = valid_q.copy()
    invalid_q["difficulty"] = 5.0 # Should be <= 1.0
    
    try:
        QuestionCreate(**invalid_q)
    except ValidationError as e:
        print(f"Caught expected validation error: {e.errors()[0]['msg']}")

    client.close()

if __name__ == "__main__":
    test_pymongo_integration()
