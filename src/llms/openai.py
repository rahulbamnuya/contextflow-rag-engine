"""
OpenAI LLM initialization and configuration with resilient multi-provider fallbacks.
"""

from langchain_openai import ChatOpenAI
from src.core.config import settings

# 1. Main LLM Client (e.g., OpenRouter or standard OpenAI)
main_llm = ChatOpenAI(
    model=settings.OPENAI_MODEL_NAME,
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE else None,
    temperature=0
)

fallbacks = []

# 2. Resilient Fallback 1: Groq Cloud (using llama-3.1-8b-instant)
if settings.GROQ_API_KEY:
    groq_llm = ChatOpenAI(
        model="llama-3.1-8b-instant",
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        temperature=0
    )
    fallbacks.append(groq_llm)

# 3. Resilient Fallback 2: Google Gemini (using gemini-2.5-flash)
if settings.GOOGLE_API_KEY:
    gemini_llm = ChatOpenAI(
        model="gemini-2.5-flash",
        api_key=settings.GOOGLE_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0
    )
    fallbacks.append(gemini_llm)

# Wrap with fallbacks for high availability and automatic rate-limit recovery
if fallbacks:
    llm = main_llm.with_fallbacks(fallbacks)
else:
    llm = main_llm