"""
rag_pipeline.py
---------------
Simple RAG pipeline: retrieves relevant document chunks
from the knowledge base and feeds them to the LLM for answering.
"""

import json
import os
import re
from groq import Groq

DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "documents.json")
RAG_MODEL = "openai/gpt-oss-20b"


def load_documents() -> list:
    """Load all documents from the knowledge base."""
    with open(DOCS_PATH, "r") as f:
        data = json.load(f)
    return data["documents"]


def simple_retrieve(query: str, documents: list, top_k: int = 3) -> list:
    """
    Keyword-based retrieval — finds documents most relevant to the query.
    In production this would use vector embeddings (FAISS, Pinecone, etc.)
    For this project we use TF-IDF style keyword matching.
    """
    query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
    scored = []

    for doc in documents:
        content = f"{doc.get('title','')} {doc.get('content','')} {' '.join(doc.get('tags', []))}".lower()
        doc_words = set(re.findall(r'\b\w{3,}\b', content))
        overlap = len(query_words & doc_words)
        if overlap > 0:
            scored.append((overlap, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def build_rag_prompt(query: str, retrieved_docs: list) -> str:
    """Build the prompt that combines retrieved context with the user query."""
    context_parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        context_parts.append(
            f"[Document {i}: {doc.get('title', 'Unknown')}]\n{doc.get('content', '')}"
        )

    context = "\n\n".join(context_parts)

    return f"""You are a helpful corporate assistant. Answer the user's question using ONLY the information in the provided documents. If the answer is not in the documents, say so clearly.

RETRIEVED DOCUMENTS:
{context}

USER QUESTION: {query}

ANSWER:"""


def query_rag(query: str, safe_documents: list, api_key: str) -> dict:
    """
    Full RAG pipeline: retrieve → build prompt → LLM answer.
    Only uses documents that passed the security scan.
    """
    retrieved = simple_retrieve(query, safe_documents)

    if not retrieved:
        return {
            "answer": "No relevant documents found in the knowledge base.",
            "retrieved_docs": [],
            "retrieved_titles": [],
            "success": True
        }

    rag_prompt = build_rag_prompt(query, retrieved)

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": rag_prompt}],
            max_tokens=500,
            temperature=0.3
        )
        answer = response.choices[0].message.content or ""

        return {
            "answer": answer,
            "retrieved_docs": retrieved,
            "retrieved_titles": [d.get("title", "") for d in retrieved],
            "success": True,
            "tokens_used": response.usage.total_tokens
        }
    except Exception as e:
        return {
            "answer": f"LLM Error: {str(e)}",
            "retrieved_docs": retrieved,
            "retrieved_titles": [d.get("title", "") for d in retrieved],
            "success": False
        }
