from datetime import datetime

from pydantic import BaseModel, Field

from research_copilot_server.models.research import ResearchStatus
from research_copilot_server.schema.report import ResearchReportResponse, SourceResponse


class user_query_body(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="User's research query")


class update_research_body(BaseModel):
    status: ResearchStatus


class ResearchResponse(BaseModel):
    id: int
    user_id: int | None = None
    query: str
    status: ResearchStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    report: ResearchReportResponse | None = None
    sources: list[SourceResponse] = []

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ResearchListResponse(BaseModel):
    items: list[ResearchResponse]
    page: int
    limit: int
    total: int

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# Backward compatibility aliases
user_query_response = ResearchResponse
create_research_response = ResearchResponse
paginated_research_response = ResearchListResponse
PaginatedResearchResponse = ResearchListResponse
