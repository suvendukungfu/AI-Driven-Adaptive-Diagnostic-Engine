"""
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from .routes import question_routes, session_routes
from .logging_conf import setup_logging
from .core.exceptions import global_exception_handler, validation_exception_handler
from .database import settings

# ── Logging setup ──────────────────────────────────────────────────────
setup_logging(log_level=settings.log_level)
logger = logging.getLogger("app")

# ── FastAPI app ────────────────────────────────────────────────────────
app = FastAPI(
    title="AI-Driven Adaptive Diagnostic Engine",
    description=(
        "A 1-D adaptive testing system that determines a student's ability "
        "level by dynamically selecting questions based on previous answers. "
        "Powered by Item Response Theory (IRT) and OpenAI."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Exception handlers ────────────────────────────────────────────────
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ── Routers ────────────────────────────────────────────────────────────
app.include_router(question_routes.router)
app.include_router(session_routes.router)


@app.get("/", tags=["Health"])
async def root():
    """Health-check / welcome endpoint."""
    return {
        "service": "AI-Driven Adaptive Diagnostic Engine",
        "version": "2.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
