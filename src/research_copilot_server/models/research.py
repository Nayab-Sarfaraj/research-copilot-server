from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Enum as SqlEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_copilot_server.config.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class ResearchStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class Research(Base):
    __tablename__ = "research"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ResearchStatus] = mapped_column(
        SqlEnum(ResearchStatus),
        default=ResearchStatus.QUEUED,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    report: Mapped["ResearchReport"] = relationship(
        "ResearchReport",
        back_populates="research",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sources: Mapped[list["ResearchSource"]] = relationship(
        "ResearchSource",
        back_populates="research",
        cascade="all, delete-orphan",
    )