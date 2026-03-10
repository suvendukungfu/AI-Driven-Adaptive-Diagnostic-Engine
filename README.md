# AI-Driven Adaptive Diagnostic Engine

A production-grade backend for a **1-D adaptive testing system** that determines a student's ability level by dynamically selecting questions based on previous answers. Built with **FastAPI**, **MongoDB**, and **OpenAI**.

---

## Project Overview

This engine implements a **Computer Adaptive Test (CAT)** using:

- **Item Response Theory (IRT)** to estimate student ability in real-time.
- **OpenAI GPT** to generate personalized study plans after test completion.

The test adapts after every answer — correct responses increase difficulty, incorrect responses decrease it — converging on the student's true ability level.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Swagger / Frontend)          │
└──────────────────────────────┬──────────────────────────────┘
                               │  REST API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  /start-     │  │ /next-question/  │  │ /submit-     │  │
│  │   session    │  │  {session_id}    │  │   answer     │  │
│  └──────┬───────┘  └────────┬─────────┘  └──────┬───────┘  │
│         │                   │                    │          │
│         ▼                   ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SERVICES LAYER                          │   │
│  │                                                      │   │
│  │  ┌─────────────────────┐  ┌───────────────────────┐ │   │
│  │  │  Adaptive Engine    │  │   AI Insights Service  │ │   │
│  │  │  (IRT Algorithm)    │  │   (OpenAI GPT API)     │ │   │
│  │  └─────────┬───────────┘  └──────────┬────────────┘ │   │
│  └────────────┼─────────────────────────┼──────────────┘   │
│               │                         │                   │
│               ▼                         ▼                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                MongoDB (Motor Async)                  │   │
│  │   ┌────────────────┐    ┌────────────────────────┐   │   │
│  │   │   questions    │    │    user_sessions        │   │   │
│  │   └────────────────┘    └────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Adaptive Algorithm Explanation

The engine uses the **1-Parameter Logistic (1PL) IRT Model**.

### Probability of Correct Response

```
P(correct) = 1 / (1 + e^-(θ - β))
```

| Symbol | Meaning                         |
| ------ | ------------------------------- |
| θ      | Student ability estimate        |
| β      | Question difficulty             |
| P      | Probability of a correct answer |

### Ability Update Rule

```
θ_new = θ_old + α × (result − P)
```

| Symbol | Meaning                      |
| ------ | ---------------------------- |
| α      | Learning rate (0.1)          |
| result | 1 if correct, 0 if incorrect |

**Clamped** to `[0.1, 1.0]`.

### Intuition

- ✅ Correct on a **hard** item → large ability increase
- ✅ Correct on an **easy** item → small ability increase
- ❌ Wrong on an **easy** item → large ability decrease
- ❌ Wrong on a **hard** item → small ability decrease

---

## MongoDB Schema

### `questions` Collection

| Field          | Type     | Description               |
| -------------- | -------- | ------------------------- |
| question       | String   | Question text             |
| options        | [String] | 4 multiple-choice options |
| correct_answer | String   | Correct option text       |
| difficulty     | Float    | 0.1 – 1.0                 |
| topic          | String   | Subject area              |
| tags           | [String] | Descriptive labels        |

### `user_sessions` Collection

| Field              | Type     | Description                  |
| ------------------ | -------- | ---------------------------- |
| user_id            | String   | Student identifier           |
| ability_score      | Float    | Current IRT estimate (0.5)   |
| correct_count      | Integer  | Total correct                |
| wrong_count        | Integer  | Total incorrect              |
| answered_questions | [String] | Answered question IDs        |
| topics_missed      | [String] | Topics with wrong answers    |
| current_question   | String   | Currently active question ID |
| status             | String   | "active" or "completed"      |

---

## API Endpoints

| Method | Path                          | Description                           |
| ------ | ----------------------------- | ------------------------------------- |
| POST   | `/start-session`              | Create session (ability = 0.5)        |
| GET    | `/next-question/{session_id}` | Get next IRT-selected question        |
| POST   | `/submit-answer`              | Submit answer, update ability via IRT |
| GET    | `/study-plan/{session_id}`    | AI-generated 3-step study plan        |
| GET    | `/questions/`                 | List all questions                    |
| POST   | `/questions/`                 | Create a new question                 |

---

## How to Run the Project

```bash
# 1. Clone
git clone https://github.com/suvendukungfu/AI-Driven-Adaptive-Diagnostic-Engine.git
cd AI-Driven-Adaptive-Diagnostic-Engine

# 2. Virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure .env
cp .env.example .env
# Edit .env → set your OPENAI_API_KEY

# 5. Seed the database (MongoDB must be running)
python seed/seed_questions.py

# 6. Start the server
uvicorn app.main:app --reload

# 7. Open docs
# http://localhost:8000/docs
```

---

## Example API Flow

```
1. POST /start-session          → { session_id: "abc123", ability_score: 0.5 }
2. GET  /next-question/abc123   → { question: "What is 2+2?", difficulty: 0.5 }
3. POST /submit-answer          → { is_correct: true, new_ability_score: 0.55 }
4. GET  /next-question/abc123   → { question: "Solve x²-5x+6=0", difficulty: 0.6 }
   ... repeat until 10 questions ...
5. POST /submit-answer          → { message: "test completed" }
6. GET  /study-plan/abc123      → { three_step_plan: [...] }
```

---

## AI Log

This project was built with the assistance of **Antigravity** (Google DeepMind's agentic AI coding assistant).

| Phase            | What AI Did                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------- |
| **Architecture** | Scaffolded the modular project structure with clean separation of concerns.                 |
| **IRT Engine**   | Implemented and documented the 1PL logistic model with step-by-step mathematical comments.  |
| **Database**     | Designed MongoDB schemas with Pydantic validation and `pymongo` JSON Schema enforcement.    |
| **API Design**   | Generated all FastAPI endpoints with proper response models and Swagger documentation.      |
| **Dataset**      | Created 20 GRE-style questions across 4 topics with balanced difficulty distribution.       |
| **Testing**      | Wrote comprehensive unit tests verifying IRT correctness, clamping, and question selection. |
| **Study Plan**   | Integrated OpenAI GPT to generate personalized 3-step learning plans from session data.     |
| **Deployment**   | Configured structured logging, global error handling, and pushed to GitHub.                 |
