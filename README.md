# 🌊 ContextFlow RAG Engine v2.0

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.5.4-orange.svg)](https://python.langchain.com/langgraph/)
[![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-purple.svg)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

**ContextFlow RAG Engine** is an advanced, production-grade agentic Retrieval-Augmented Generation (RAG) system. Powered by **FastAPI** and **LangGraph**, it dynamically routes user questions, retrieves context from cloud vector databases, and performs real-time self-checking to deliver reliable answers. 

The system adapts its workflow dynamically, choosing between custom document retrieval, common-knowledge LLM reasoning, or live web search.

---

## 🏗️ Architecture Workflow

```mermaid
graph TD
    classDef security fill:#f8d7da,stroke:#f5c6cb,stroke-width:2px,color:#721c24;
    classDef router fill:#d1ecf1,stroke:#bee5eb,stroke-width:2px,color:#0c5460;
    classDef search fill:#fff3cd,stroke:#ffeeba,stroke-width:2px,color:#856404;
    classDef eval fill:#d4edda,stroke:#c3e6cb,stroke-width:2px,color:#155724;
    
    User([User Prompt]) --> Gateway[FastAPI Endpoints]
    Gateway --> Limiter{SlowAPI Rate Limiter}:::security
    Limiter -->|Pass| Sanitizer{Prompt Injection Shield}:::security
    Sanitizer -->|Safe| Auth[HMAC JWT Authentication]:::security
    Auth --> MongoDB[(MongoDB Atlas: isolated user chat history)]
    
    MongoDB --> Router{LangGraph Query Classifier}:::router
    
    Router -->|Conversational| GenLLM[General LLM Route]
    Router -->|Index / Retrieval| Retrieve[Hybrid Retrieval: BM25 + Qdrant Cloud]
    Router -->|Web Search| WebSearch[Tavily Search Agent]:::search
    
    Retrieve --> Reranker[Flashrank Reranker]
    Reranker --> Grader{Context Grader}:::eval
    
    Grader -->|Relevant Context| Generator[Response Generator]
    Grader -->|Irrelevant Context| Rewriter[Query Rewriter]:::router --> Retrieve
    
    WebSearch --> Generator
    Generator --> Citation[Source Citations & Footnotes]
    Citation --> Judge{LLM-as-a-Judge Hallucination Checker}:::eval
    
    Judge -->|Faithful Output| Output([Verified Response])
    Judge -->|Hallucination Detected| Warning([Response with Hallucination Warning])
    GenLLM --> Output
    
    Output -.-> Langfuse[Langfuse Observability Tracing]:::search
    Warning -.-> Langfuse
```

---

## 🚀 Key Features

*   **🔒 Security & Defense**:
    *   **HMAC Session Tokens**: Secure session generation and signing preventing token forgery.
    *   **User Isolation**: Chat histories are stored individually per user in MongoDB Atlas.
    *   **Input Sanitization**: Detects and blocks prompt injection and jailbreak attacks.
*   **🔍 High-Performance Retrieval**:
    *   **Hybrid Search**: Matches documents using both semantic vector embeddings and sparse keyword matching (`rank-bm25`).
    *   **Flashrank Reranking**: Locally evaluates and re-orders document chunks to ensure only top contexts are fed to the model.
*   **🤖 Hallucination Verification Agent**: Built-in LangGraph node verifying output compliance against retrieved sources, warning users if unfaithful statements are present.
*   **📝 Citation Formatting**: System instructions force inline sources and footnotes (e.g. `[Source: employee_handbook.pdf]`).
*   **🔌 Resilient Multi-Provider Fallback**: Chained model execution (OpenRouter $\rightarrow$ Groq $\rightarrow$ Gemini) to prevent query failures during rate-limiting or downtime.
*   **⚡ Singleton Caching & Memory Protection**: Employs a global Singleton caching pattern for retriever and database client instances. This prevents memory leaks and query degradation by avoiding repeated class allocations on every request, automatically invalidating cache handles only when new files are ingested.
*   **🐳 Dockerized**: Fully containerized environment with database and model-engine orchestrations.
*   **🛡️ SlowAPI Rate Limiter**: Rate limits core API routes to prevent server overloading and API key abuse.

---

## ⚙️ Environment Configuration (`.env`)

Configure your keys in the `.env` file (copied from `.env.example`):
```env
# LLM Endpoint Config
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_MODEL_NAME=qwen/qwen-2.5-72b-instruct

# Tavily Search API Config
TAVILY_API_KEY=your_tavily_key_here

# MongoDB Connection (Cloud Atlas or Local Docker)
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
MONGO_DB_NAME=adaptive_rag

# Langfuse Observability Tracing settings
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

---

## 🛠️ Quick Start & Setup

### Option 1: Automation Tool (Windows)
Run the setup batch script in your terminal:
```bash
setup_dev.bat
```
*   Select `[1]` to install dependencies and configure the virtual environment.
*   Select `[2]` to run the PyTest suite (including the **LLM-as-a-Judge** evaluations).
*   Select `[3]` and `[4]` to launch the FastAPI backend and Streamlit frontend.

### Option 2: Using Make (Linux / macOS)
1.  **Initialize Environment**:
    ```bash
    make setup
    ```
2.  **Run Tests**:
    ```bash
    make test
    ```
3.  **Run Services**:
    ```bash
    make run-backend
    make run-frontend
    ```

### Option 3: Running via Docker Compose
Build and run the entire stack (FastAPI, Streamlit, MongoDB, Qdrant) in one command:
```bash
docker compose up --build
```
*   **FastAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Streamlit Web Interface**: [http://localhost:8501](http://localhost:8501)
*   **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
