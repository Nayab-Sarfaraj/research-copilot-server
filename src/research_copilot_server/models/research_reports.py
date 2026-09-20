from research_copilot_server.config.db import Base  
from datetime import datetime,timezone
from sqlalchemy.orm import mapped_column,Mapped
from sqlalchemy import String,Enum as SqlEnum,ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum

def utc_now():
    return datetime.now(timezone.utc)



class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    content: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)

    research_id: Mapped[int] = mapped_column(
        ForeignKey("research.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        nullable=False
    )

    research: Mapped["Research"] = relationship(
        "Research",
        back_populates="report"
    )