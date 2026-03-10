import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from .routes import question_routes, session_routes
from .logging_conf import setup_logging
from .core.exceptions import global_exception_handler, validation_exception_handler
from .database import settings

# Setup structured logging
setup_logging(log_level=settings.log_level)
logger = logging.getLogger("app")

app = FastAPI(
    title="AI-Driven Adaptive Testing Engine",
    description="Refined Adaptive Testing System using IRT.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include routers
app.include_router(question_routes.router)
app.include_router(session_routes.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Refined Adaptive Testing API",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
