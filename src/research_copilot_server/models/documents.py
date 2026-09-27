from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_copilot_server.config.db import Base

if TYPE_CHECKING:
    from research_copilot_server.models.user import User


def utc_now():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
    )
