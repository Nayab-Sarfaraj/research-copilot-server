from datetime import datetime

from pydantic import BaseModel, Field

from research_copilot_server.models.research import ResearchStatus


class user_query_body(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="User's research query")


class user_query_response(BaseModel):
    id: int
    query: str
    status: ResearchStatus
    created_at: datetime
    updated_at: datetime


class update_research_body(BaseModel):
    status: ResearchStatus
