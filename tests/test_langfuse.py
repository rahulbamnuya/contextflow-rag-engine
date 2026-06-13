import os
from dotenv import load_dotenv
from langfuse import Langfuse

# Load keys from .env
load_dotenv(override=True)

public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")


def test_langfuse_connectivity():
    print("--- Testing Langfuse Cloud Integration ---")
    if not public_key or not secret_key:
        print("FAIL: Langfuse credentials missing in .env")
        return False
        
    print(f"Host: {host}")
    print(f"Public Key: {public_key[:10]}...")
    
    try:
        # Initialize client
        langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        
        # Create a test trace
        print("Sending test trace...")
        trace = langfuse.trace(
            name="ContextFlow RAG Connectivity Test",
            user_id="test_user_1",
            metadata={"environment": "development"}
        )
        
        # Add a generation step to the trace
        trace.generation(
            name="Test Node Generation",
            model="qwen/qwen-2.5-72b-instruct",
            input="Ping",
            output="Pong",
            usage={"prompt_tokens": 1, "completion_tokens": 1}
        )
        
        # Flush the logs to ensure they are sent immediately
        langfuse.flush()
        print("SUCCESS: Trace successfully pushed and flushed to Langfuse Cloud!")
        print("Check your dashboard at https://cloud.langfuse.com to see the trace 'ContextFlow RAG Connectivity Test'.")
        return True
    except Exception as e:
        print(f"FAIL: Langfuse trace delivery failed: {e}")
        return False


if __name__ == "__main__":
    test_langfuse_connectivity()
