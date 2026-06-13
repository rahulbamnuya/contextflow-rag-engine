"""
Retriever setup, hybrid search, and vector store configuration.
"""

import os
from typing import List, Any
from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_qdrant import QdrantVectorStore

from src.core.config import settings

# Check if running with mock credentials (e.g., in CI pipelines)
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
if not openai_api_key or openai_api_key.startswith("mock"):
    print("Detected mock/missing OpenAI API key. Using MockOpenAIEmbeddings for environment compatibility.")
    from langchain_core.embeddings import Embeddings
    class MockOpenAIEmbeddings(Embeddings):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return [[0.0] * 1536 for _ in texts]
        def embed_query(self, text: str) -> List[float]:
            return [0.0] * 1536
    embeddings = MockOpenAIEmbeddings()
else:
    embeddings = OpenAIEmbeddings()

# Global variables to store retriever components for reuse
_semantic_vectorstore = None
_bm25_retriever = None
_ranker = None
_retriever_tool = None


class HybridReRankRetriever(BaseRetriever):
    """Custom retriever that merges semantic + BM25 results and reranks using Flashrank."""
    semantic_retriever: Any
    bm25_retriever: Any

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str, *, run_manager: Any = None) -> List[Document]:
        # 1. Fetch documents from both retrievers
        try:
            semantic_docs = self.semantic_retriever.invoke(query)
        except Exception as e:
            print(f"Semantic retrieval failed: {e}")
            semantic_docs = []

        try:
            bm25_docs = self.bm25_retriever.invoke(query)
        except Exception as e:
            print(f"BM25 retrieval failed: {e}")
            bm25_docs = []

        # 2. Merge and deduplicate by content to prevent duplicates
        seen = set()
        merged_docs = []
        for doc in semantic_docs + bm25_docs:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                merged_docs.append(doc)

        if not merged_docs:
            return []

        # 3. Apply Flashrank Reranking
        try:
            from flashrank import RankRequest, Ranker
            global _ranker
            if _ranker is None:
                print("Initializing Flashrank Ranker...")
                # Initialize ranker with a light CPU-friendly model
                _ranker = Ranker(model_name="ms-marco-MiniLM-L-6-v2")
                print("Flashrank Ranker loaded successfully.")

            passages = [
                {"id": i, "text": doc.page_content, "meta": doc.metadata}
                for i, doc in enumerate(merged_docs)
            ]

            rank_request = RankRequest(query=query, passages=passages)
            results = _ranker.rerank(rank_request)

            # Re-order the original documents based on re-ranker scores
            reranked_docs = []
            for item in results[:5]:  # Take top 5 most relevant chunks
                idx = item["id"]
                reranked_docs.append(merged_docs[idx])

            print(f"Reranking completed. Returned {len(reranked_docs)} top documents.")
            return reranked_docs

        except Exception as e:
            print(f"Reranking failed (falling back to raw merge): {e}")
            return merged_docs[:5]


def retriever_chain(chunks: List[Document]) -> bool:
    """
    Initialize and store document chunks in the selected vector database (Qdrant or FAISS).
    Also builds the BM25 keyword index.
    """
    global _semantic_vectorstore, _bm25_retriever, _retriever_tool

    try:
        # Invalidate cached retriever tool to force reconstruction with new documents
        _retriever_tool = None
        try:
            from src.rag.reAct_agent import reset_agent_executor
            reset_agent_executor()
        except ImportError:
            pass

        # 1. Initialize BM25 Keyword Retriever
        _bm25_retriever = BM25Retriever.from_documents(chunks)
        _bm25_retriever.k = 10  # Retrieve top 10 candidates

        # 2. Initialize Semantic Vectorstore
        if settings.QDRANT_URL:
            print(f"Connecting to Qdrant Cloud at: {settings.QDRANT_URL}")
            _semantic_vectorstore = QdrantVectorStore.from_documents(
                documents=chunks,
                embedding=embeddings,
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                collection_name=settings.CODE_COLLECTION,
            )
            print("Successfully initialized Qdrant vector database.")
        else:
            print("No QDRANT_URL provided. Falling back to local in-memory FAISS.")
            _semantic_vectorstore = FAISS.from_documents(
                documents=chunks,
                embedding=embeddings
            )
            print("Successfully initialized local FAISS index.")

        return True
    except Exception as e:
        print(f"Error initializing retriever chain: {e}")
        return False


def get_retriever() -> Any:
    """
    Constructs and returns the custom HybridReRankRetriever tool.
    Creates dummy indices if no documents have been uploaded yet to prevent graph crashes.
    """
    global _semantic_vectorstore, _bm25_retriever, _retriever_tool

    try:
        # Return the cached tool instance if it has already been initialized
        if _retriever_tool is not None:
            return _retriever_tool

        # If no documents are uploaded, initialize dummy structures
        if _semantic_vectorstore is None or _bm25_retriever is None:
            print("No documents indexed. Constructing dummy retriever...")
            dummy_doc = Document(
                page_content="No documents have been uploaded yet. Please upload a document first.",
                metadata={"source": "system"}
            )
            
            _bm25_retriever = BM25Retriever.from_documents([dummy_doc])
            _bm25_retriever.k = 1

            if settings.QDRANT_URL:
                # Initialize empty Qdrant instance
                _semantic_vectorstore = QdrantVectorStore.from_documents(
                    documents=[],
                    embedding=embeddings,
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                    collection_name=settings.CODE_COLLECTION,
                )
            else:
                _semantic_vectorstore = FAISS.from_documents([dummy_doc], embedding=embeddings)

        # Build custom hybrid retriever
        semantic_retriever = _semantic_vectorstore.as_retriever(search_kwargs={"k": 10})
        
        hybrid_retriever = HybridReRankRetriever(
            semantic_retriever=semantic_retriever,
            bm25_retriever=_bm25_retriever
        )

        # Load description metadata if present
        description = None
        if os.path.exists("description.txt"):
            try:
                with open("description.txt", "r", encoding="utf-8") as f:
                    description = f.read().strip()
            except Exception:
                pass
        
        if not description:
            description = "customer uploaded documents"

        # Wrap in LangChain retriever tool
        _retriever_tool = create_retriever_tool(
            hybrid_retriever,
            "retriever_customer_uploaded_documents",
            f"Use this tool **only** to answer questions about: {description}\n"
            "Don't use this tool to answer anything else."
        )

        return _retriever_tool

    except Exception as e:
        print(f"Error getting retriever: {e}")
        raise e
