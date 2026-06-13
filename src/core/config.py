"""
Core configuration and environment settings.
"""

import os

from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    """Application settings loaded from environment variables."""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
    
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    CODE_COLLECTION: str = os.getenv("QDRANT_CODE_COLLECTION", "codebase")
    DOCS_COLLECTION: str = os.getenv("QDRANT_DOCS_COLLECTION", "guidelines")
    
    # MongoDB configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "adaptive_rag")


settings = Settings()

# Set env variables for LangChain integrations
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.OPENAI_API_BASE:
    os.environ["OPENAI_API_BASE"] = settings.OPENAI_API_BASE
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
