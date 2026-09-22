from datetime import datetime, timezone
from typing import Any

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from research_copilot_server.config.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
