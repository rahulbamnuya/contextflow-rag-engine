"""
API routes for RAG operations and User Authentication.
"""

import hashlib
import hmac
import os
import re
import secrets
from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Request
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel

from src.db.mongo_client import db
from src.memory.chat_history_mongo import ChatHistory
from src.models.query_request import QueryRequest
from src.rag.document_upload import documents
from src.rag.graph_builder import builder
from src.core.limiter import limiter

router = APIRouter()
users_collection = db["users"]

# HMAC signing secret (In production, load this from settings/environment)
SECRET_KEY = "contextflow_rag_production_ready_secret_key"


class UserAuth(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generate_signed_token(username: str) -> str:
    """Create a signed token for user session."""
    signature = hmac.new(
        SECRET_KEY.encode(), username.encode(), hashlib.sha256
    ).hexdigest()
    return f"{username}.{signature}"


def verify_token(token: str) -> str | None:
    """Verify signed token signature and return username if valid."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        username, signature = parts[0], parts[1]
        expected_sig = hmac.new(
            SECRET_KEY.encode(), username.encode(), hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(signature, expected_sig):
            return username
    except Exception:
        pass
    return None


def detect_prompt_injection(text: str) -> bool:
    """Simple regex-based check for common prompt injection patterns."""
    patterns = [
        r"(ignore|bypass|override)\s+(the\s+)?(previous|prior|above|system)\s+(instructions|prompt|directives)",
        r"you\s+are\s+now\s+a\s+",
        r"new\s+system\s+prompt",
        r"jailbreak",
        r"dan\s+mode",
        r"do\s+anything\s+now",
        r"system\s+override"
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


@router.post("/auth/init")
async def auth_init():
    """Generate a temporary API token for session start."""
    token = secrets.token_hex(16)
    return {"api_token": token}


@router.post("/auth/create_user")
@limiter.limit("5/minute")
async def create_user_route(auth: UserAuth, request: Request):
    """Create a new user account in MongoDB (Rate limited)."""
    existing_user = await users_collection.find_one({"username": auth.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    await users_collection.insert_one({
        "username": auth.username,
        "password_hash": hash_password(auth.password)
    })
    return {"status": "success"}


@router.post("/auth/login")
@limiter.limit("10/minute")
async def login_user_route(auth: UserAuth, request: Request):
    """Authenticate credentials and return a signed session token (Rate limited)."""
    user = await users_collection.find_one({"username": auth.username})
    if not user or user["password_hash"] != hash_password(auth.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = generate_signed_token(auth.username)
    return {"jwt": token}


@router.post("/rag/query")
@limiter.limit("30/minute")
async def rag_query(req: QueryRequest, request: Request):
    """
    Process a RAG query and return the result (Rate limited).
    Isolates chat history dynamically using verified username.
    """
    # 1. Prompt Injection Defense
    if detect_prompt_injection(req.query):
        raise HTTPException(status_code=400, detail="Potential prompt injection detected. Query blocked.")

    # 2. Token verification & user isolation
    username = verify_token(req.session_id)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    # Isolate history per user using username prefix
    chat_history = ChatHistory.get_session_history(f"user_{username}")
    await chat_history.add_message(HumanMessage(content=req.query))

    # Fetch full history
    messages = await chat_history.get_messages()

    # Setup Langfuse tracing callbacks
    callbacks = []
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        try:
            from langfuse.callback import CallbackHandler
            langfuse_handler = CallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
            )
            callbacks.append(langfuse_handler)
            print("Langfuse tracing successfully initialized.")
        except Exception as e:
            print(f"Failed to load Langfuse callback: {e}")

    result = builder.invoke({
        "messages": messages
    }, config={"callbacks": callbacks})
    output_text = result["messages"][-1].content

    # Save assistant message
    await chat_history.add_message(AIMessage(content=output_text))

    return {"result": result["messages"][-1]}


@router.post("/rag/documents/upload")
@limiter.limit("5/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    description: str = Header(..., alias="X-Description"),
    authorization: str = Header(None)
):
    """
    Upload a document for RAG processing (Rate limited).
    Requires Authorization bearer token header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    status_upload = documents(description, file)
    return {"status": status_upload}
