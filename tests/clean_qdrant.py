import os
import requests
import json
from dotenv import load_dotenv

# Load configuration from .env
load_dotenv(override=True)

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_ENDPOINT = os.getenv("QDRANT_URL")


def list_collections():
    if not QDRANT_ENDPOINT or not QDRANT_API_KEY:
        print("ERROR: QDRANT_URL or QDRANT_API_KEY is not defined in .env")
        return []
    headers = {"api-key": QDRANT_API_KEY}
    try:
        res = requests.get(f"{QDRANT_ENDPOINT}/collections", headers=headers, timeout=10)
        if res.status_code == 200:
            return [c["name"] for c in res.json().get("result", {}).get("collections", [])]
    except Exception as e:
        print(f"ERROR: Failed to connect to Qdrant: {e}")
    return []


def delete_collection(name):
    print(f"Deleting collection '{name}'...")
    headers = {"api-key": QDRANT_API_KEY}
    try:
        res = requests.delete(f"{QDRANT_ENDPOINT}/collections/{name}", headers=headers, timeout=10)
        if res.status_code == 200:
            print(f"SUCCESS: Deleted collection '{name}'.")
        else:
            print(f"FAIL: Could not delete collection '{name}': {res.text}")
    except Exception as e:
        print(f"ERROR: Exception while deleting collection: {e}")


if __name__ == "__main__":
    collections = list_collections()
    if not collections:
        print("No active collections found in Qdrant Cloud Cluster. Storage is empty.")
    else:
        print(f"Found collections: {collections}")
        confirm = input("Do you want to delete ALL collections to reset storage? (yes/no): ")
        if confirm.lower() == "yes":
            for name in collections:
                delete_collection(name)
        else:
            print("Operation cancelled.")
