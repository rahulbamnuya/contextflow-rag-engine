"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from src.api.routes import router
from src.core.limiter import limiter

app = FastAPI(title="ContextFlow RAG API")

# Register rate limiting components
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router)
app.state.description_ = ""


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "ContextFlow RAG API is running"}
