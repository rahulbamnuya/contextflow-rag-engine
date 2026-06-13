"""
Unit tests for user authentication and session security.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Mock environment variables for testing before imports
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DB_NAME"] = "test_auth_db"
os.environ["OPENAI_API_KEY"] = "mock_openai_key"

from src.main import app
from src.api.routes import hash_password, generate_signed_token, verify_token

client = TestClient(app)


def test_password_hashing():
    """Verify that password hashing uses SHA-256 and is deterministic."""
    pwd = "securepassword123"
    hashed = hash_password(pwd)
    
    assert hashed != pwd
    assert len(hashed) == 64  # SHA-256 yields 64 character hex string
    assert hash_password(pwd) == hashed


def test_token_signing_and_verification():
    """Verify that user sessions are signed securely using HMAC."""
    username = "alice"
    token = generate_signed_token(username)
    
    assert token.startswith(f"{username}.")
    
    # Verification should succeed with original token
    verified_user = verify_token(token)
    assert verified_user == username

    # Verification should fail if token is tampered
    tampered_token = token + "1"
    assert verify_token(tampered_token) is None

    # Verification should fail with invalid tokens
    assert verify_token("invalid_token") is None
    assert verify_token("alice.invalidsignature123") is None


def test_auth_routes():
    """Test API endpoint flows for signup and login."""
    # Start with a clean slate (use random suffix to avoid collection collisions)
    import random
    rand_id = random.randint(1000, 9999)
    username = f"testuser_{rand_id}"
    password = "secretpassword"

    # 1. Register a new user
    signup_res = client.post(
        "/auth/create_user",
        json={"username": username, "password": password}
    )
    assert signup_res.status_code == 200
    assert signup_res.json() == {"status": "success"}

    # 2. Try to register same user again (should fail)
    duplicate_res = client.post(
        "/auth/create_user",
        json={"username": username, "password": password}
    )
    assert duplicate_res.status_code == 400

    # 3. Log in with wrong credentials (should fail)
    bad_login = client.post(
        "/auth/login",
        json={"username": username, "password": "wrongpassword"}
    )
    assert bad_login.status_code == 401

    # 4. Log in with correct credentials (should succeed)
    good_login = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )
    assert good_login.status_code == 200
    assert "jwt" in good_login.json()
    
    # 5. Verify the token returned
    jwt_token = good_login.json()["jwt"]
    assert verify_token(jwt_token) == username
