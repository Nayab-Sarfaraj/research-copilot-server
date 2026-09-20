from research_copilot_server.config.db import Base  
from datetime import datetime,timezone
from sqlalchemy.orm import mapped_column,Mapped
from sqlalchemy import String,Enum as SqlEnum,ForeignKey
from enum import Enum
from sqlalchemy.orm import relationship

def utc_now():
    return datetime.now(timezone.utc)

class ResearchStatus(str,Enum):
    QUEUED="queued"
    CREATED="created"
    PROCESSING="processing"
    FAILED="failed"
    COMPLETED="completed"

class Research(Base):
    __tablename__ = "research"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ResearchStatus] = mapped_column(
        SqlEnum(ResearchStatus),
        default=ResearchStatus.CREATED,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
    default=utc_now,
    nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    report: Mapped["ResearchReport"] = relationship(
        "ResearchReport",
        back_populates="research",
        uselist=False,
        cascade="all, delete-orphan"

    )