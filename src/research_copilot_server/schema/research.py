from datetime import datetime

from pydantic import BaseModel, Field

from research_copilot_server.models.research import ResearchStatus
from research_copilot_server.schema.report import research_report_response


class user_query_body(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="User's research query")


class user_query_response(BaseModel):
    id: int
    query: str
    status: ResearchStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class create_research_response(user_query_response):
    report: research_report_response


class update_research_body(BaseModel):
    status: ResearchStatus


class paginated_research_response(BaseModel):
    items: list[user_query_response]
    page: int
    limit: int
    total: int

    model_config = {"from_attributes": True}


PaginatedResearchResponse = paginated_research_response
