from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_copilot_server.config.db import Base

if TYPE_CHECKING:
	from research_copilot_server.models.research import Research


def utc_now():
	return datetime.now(timezone.utc)


class SourceType(str, Enum):
	WEB = "web"
	DOCUMENT = "document"


class ResearchSource(Base):
	__tablename__ = "research_sources"

	id: Mapped[int] = mapped_column(primary_key=True)
	research_id: Mapped[int] = mapped_column(
		ForeignKey("research.id", ondelete="CASCADE"),
		nullable=False,
	)
	title: Mapped[str] = mapped_column(String, nullable=False)
	url: Mapped[str | None] = mapped_column(Text, nullable=True)
	source_type: Mapped[SourceType] = mapped_column(
		SqlEnum(
			SourceType,
			name="sourcetype",
			values_callable=lambda enum: [item.value for item in enum],
		),
		nullable=False,
	)
	source_metadata: Mapped[dict[str, Any]] = mapped_column(
		"metadata",
		JSON,
		nullable=False,
		default=dict,
	)
	created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
	research: Mapped["Research"] = relationship(
		"Research",
		back_populates="sources",
	)
