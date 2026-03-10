import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "adaptive_test_db")

questions = [
    {
        "question": "What is the result of 2 + 2?",
        "options": ["3", "4", "5", "6"],
        "correct_answer": "4",
        "difficulty": 0.1,
        "topic": "Mathematics",
        "tags": ["basic", "arithmetic"]
    },
    {
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "correct_answer": "Paris",
        "difficulty": 0.2,
        "topic": "Geography",
        "tags": ["capitals", "europe"]
    },
    {
        "question": "Which element has the atomic number 1?",
        "options": ["Helium", "Oxygen", "Hydrogen", "Carbon"],
        "correct_answer": "Hydrogen",
        "difficulty": 0.3,
        "topic": "Science",
        "tags": ["chemistry", "elements"]
    },
    {
        "question": "Solve: 15 * 12",
        "options": ["150", "170", "180", "200"],
        "correct_answer": "180",
        "difficulty": 0.4,
        "topic": "Mathematics",
        "tags": ["arithmetic", "intermediate"]
    }
]

async def seed_db():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print(f"Connecting to {DATABASE_NAME}...")

    # Clear existing questions
    await db.questions.delete_many({})
    await db.user_sessions.delete_many({})
    print("Old data deleted.")

    # Insert new questions
    result = await db.questions.insert_many(questions)
    print(f"Successfully seeded {len(result.inserted_ids)} questions.")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed_db())
