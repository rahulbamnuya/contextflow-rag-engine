import os
import requests
import json
from dotenv import load_dotenv

# Load configurations from .env
load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_ENDPOINT = os.getenv("QDRANT_URL")
MONGO_URI = os.getenv("MONGO_URI")


def test_openrouter():
    print("\n--- Testing OpenRouter API Key ---")
    if not OPENROUTER_API_KEY:
        print("SKIP: OPENAI_API_KEY is not defined in .env")
        return False
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost:8501",
        "X-OpenRouter-Title": "Test Client"
    }
    payload = {
        "model": "qwen/qwen-2.5-72b-instruct",
        "messages": [{"role": "user", "content": "Say hello in one word."}]
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            if "choices" in data:
                content = data["choices"][0]["message"]["content"].strip()
                print(f"SUCCESS: OpenRouter response: '{content}'")
                return True
            else:
                print(f"FAIL: OpenRouter response missing 'choices': {json.dumps(data)}")
                return False
        else:
            print(f"FAIL: OpenRouter: {json.dumps(data)}")
            return False
    except Exception as e:
        print(f"ERROR: OpenRouter Exception: {e}")
        return False


def test_groq():
    print("\n--- Testing Groq API Key ---")
    if not GROQ_API_KEY:
        print("SKIP: GROQ_API_KEY is not defined in .env")
        return False
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Say hello in one word."}]
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            if "choices" in data:
                content = data["choices"][0]["message"]["content"].strip()
                print(f"SUCCESS: Groq response: '{content}'")
                return True
            else:
                print(f"FAIL: Groq response missing 'choices': {json.dumps(data)}")
                return False
        else:
            print(f"FAIL: Groq: {json.dumps(data)}")
            return False
    except Exception as e:
        print(f"ERROR: Groq Exception: {e}")
        return False


def test_gemini():
    print("\n--- Testing Google Gemini API Key ---")
    if not GOOGLE_API_KEY:
        print("SKIP: GOOGLE_API_KEY is not defined in .env")
        return False
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{
            "parts": [{"text": "Say hello in one word."}]
        }]
    }
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            if "candidates" in data:
                content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"SUCCESS: Gemini response: '{content}'")
                return True
            else:
                print(f"FAIL: Gemini response missing 'candidates': {json.dumps(data)}")
                return False
        else:
            print(f"FAIL: Gemini: {json.dumps(data)}")
            return False
    except Exception as e:
        print(f"ERROR: Gemini Exception: {e}")
        return False


def test_tavily():
    print("\n--- Testing Tavily API Key ---")
    if not TAVILY_API_KEY:
        print("SKIP: TAVILY_API_KEY is not defined in .env")
        return False
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": "What is the capital of France?",
        "search_depth": "basic"
    }
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            if "results" in data and len(data["results"]) > 0:
                snippet = data["results"][0]["content"][:60]
                print(f"SUCCESS: Tavily returned results. First match: '{snippet}...'")
                return True
            else:
                print(f"FAIL: Tavily response missing 'results': {json.dumps(data)}")
                return False
        else:
            print(f"FAIL: Tavily: {json.dumps(data)}")
            return False
    except Exception as e:
        print(f"ERROR: Tavily Exception: {e}")
        return False


def test_mongodb():
    print("\n--- Testing MongoDB Atlas Connection ---")
    if not MONGO_URI:
        print("SKIP: MONGO_URI is not defined in .env")
        return False
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("SUCCESS: MongoDB Atlas connection verified successfully!")
        
        db = client["test_db"]
        col = db["test_connectivity"]
        res = col.insert_one({"ping": "pong"})
        print(f"SUCCESS: Wrote test document. ID: {res.inserted_id}")
        
        col.delete_one({"_id": res.inserted_id})
        print("SUCCESS: Cleaned up test document. Read/Write permissions are verified.")
        return True
    except Exception as e:
        print(f"FAIL: MongoDB Atlas connection failed: {e}")
        return False


def test_qdrant():
    print("\n--- Testing Qdrant Cloud Cluster ---")
    if not QDRANT_ENDPOINT or not QDRANT_API_KEY:
        print("SKIP: QDRANT_URL or QDRANT_API_KEY is not defined in .env")
        return False
    headers = {
        "api-key": QDRANT_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(
            f"{QDRANT_ENDPOINT}/collections",
            headers=headers,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            collections = [c["name"] for c in data.get("result", {}).get("collections", [])]
            print(f"SUCCESS: Qdrant Cloud reachable! Collections list: {collections}")
            return True
        else:
            print(f"FAIL: Qdrant Cloud: {json.dumps(data)}")
            return False
    except Exception as e:
        print(f"ERROR: Qdrant Cloud Exception: {e}")
        return False


if __name__ == "__main__":
    test_openrouter()
    test_groq()
    test_gemini()
    test_tavily()
    test_mongodb()
    test_qdrant()
