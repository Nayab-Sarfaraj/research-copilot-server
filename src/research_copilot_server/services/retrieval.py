from __future__ import annotations

import json

from sentence_transformers import SentenceTransformer

from research_copilot_server.config.db import SessionLocal
from research_copilot_server.repository import document as document_repository

model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def knowledge_search(query: str, limit: int = 5) -> str:
    """Find the most relevant stored document chunks for a query."""
    query_embedding = model.encode(query, normalize_embeddings=True).tolist()

    db = SessionLocal()
    try:
        matches = document_repository.search_documents(db, query_embedding, limit)
        results = [
            {
                "content": document.content,
                "metadata": document.document_metadata,
                "similarity": round(1 - float(distance), 4),
            }
            for document, distance in matches
        ]
        return json.dumps(results)
    finally:
        db.close()
