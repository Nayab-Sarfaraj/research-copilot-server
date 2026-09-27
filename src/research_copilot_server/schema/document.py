from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class DocumentChunkResponse(BaseModel):
    id: int | None = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding_length: int | None = None
    created_at: datetime | None = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class DocumentResponse(BaseModel):
    filename: str
    saved_chunk_count: int
    chunks: list[DocumentChunkResponse] = []

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
