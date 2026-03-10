from pymongo import MongoClient
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "adaptive_test_db")

def setup_mongodb_schemas():
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    # Questions Collection with JSON Schema Validation
    questions_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["question", "options", "correct_answer", "difficulty", "topic"],
            "properties": {
                "question": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "options": {
                    "bsonType": "array",
                    "minItems": 2,
                    "items": {"bsonType": "string"},
                    "description": "must be an array of strings and is required"
                },
                "correct_answer": {
                    "bsonType": "string",
                    "description": "must match one of the options"
                },
                "difficulty": {
                    "bsonType": "double",
                    "minimum": 0.1,
                    "maximum": 1.0,
                    "description": "must be a double between 0.1 and 1.0"
                },
                "topic": {
                    "bsonType": "string",
                    "description": "must be a string"
                },
                "tags": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                }
            }
        }
    }

    # User Sessions Collection with JSON Schema Validation
    user_sessions_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id", "ability_score", "correct_count", "wrong_count", "answered_questions"],
            "properties": {
                "user_id": {
                    "bsonType": "string"
                },
                "ability_score": {
                    "bsonType": "double",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "correct_count": {
                    "bsonType": "int"
                },
                "wrong_count": {
                    "bsonType": "int"
                },
                "answered_questions": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "topics_missed": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "status": {
                    "enum": ["active", "completed"]
                }
            }
        }
    }

    # Create/Update collections with validators
    collections = {
        "questions": questions_schema,
        "user_sessions": user_sessions_schema
    }

    for coll_name, schema in collections.items():
        if coll_name in db.list_collection_names():
            print(f"Updating validation for {coll_name}...")
            db.command("collMod", coll_name, validator=schema)
        else:
            print(f"Creating collection {coll_name} with validation...")
            db.create_collection(coll_name, validator=schema)

    print("MongoDB Schema Refinement complete.")
    client.close()

if __name__ == "__main__":
    setup_mongodb_schemas()
