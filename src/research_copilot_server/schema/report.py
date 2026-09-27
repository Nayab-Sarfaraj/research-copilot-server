from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from research_copilot_server.models.research_source import SourceType


class model_output(BaseModel):
    content: str = Field(description="Relevant response of the user query")
    title: str
    summary: str


class SourceResponse(BaseModel):
    id: int | None = None
    research_id: int | None = None
    title: str
    url: str | None = None
    source_type: SourceType | str = "web"
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ResearchReportResponse(BaseModel):
    id: int
    research_id: int | None = None
    title: str
    summary: str
    content: str
    created_at: datetime
    sources: list[SourceResponse] | None = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# Backward compatibility alias
research_report_response = ResearchReportResponse
