"""
Seed script — loads the 20 GRE-style questions from gre_questions.json
into the MongoDB 'questions' collection.

Usage:
    python seed/seed_questions.py
"""

import asyncio
import json
import os
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "adaptive_test_db")

# Path to the JSON dataset (relative to this script)
DATA_FILE = Path(__file__).parent / "gre_questions.json"


async def seed_db() -> None:
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print(f"Connecting to '{DATABASE_NAME}'...")

    # Load dataset
    with open(DATA_FILE, "r") as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions from {DATA_FILE.name}")

    # Clear old data
    await db.questions.delete_many({})
    await db.user_sessions.delete_many({})
    print("Old data deleted.")

    # Insert
    result = await db.questions.insert_many(questions)
    print(f"✓ Seeded {len(result.inserted_ids)} questions successfully.")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_db())
