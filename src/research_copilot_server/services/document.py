from __future__ import annotations

from typing import Any

import fitz
from fastapi import HTTPException, status
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from research_copilot_server.models.documents import Document
from research_copilot_server.repository import document as document_repository

model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def process_pdf_document(db, file_name: str, contents: bytes, user_id: int | None = None) -> list[Document]:
    try:
        doc = fitz.open(stream=contents, filetype="pdf")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read PDF file: {str(exc)}",
        ) from exc

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    documents: list[Document] = []
    for page_number in range(doc.page_count):
        page = doc[page_number]
        text = page.get_text("text").strip()
        if not text:
            continue

        chunks = splitter.split_text(text)
        for chunk in chunks:
            embedding = model.encode(chunk)
            documents.append(
                Document(
                    user_id=user_id,
                    content=chunk,
                    document_metadata={
                        "source": file_name,
                        "page": page_number + 1,
                    },
                    embedding=embedding.tolist(),
                )
            )

    if not documents:
        return []

    return document_repository.create_documents(db, documents)
