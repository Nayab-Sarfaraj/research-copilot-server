from pydantic import BaseModel, Field
from datetime import datetime

class model_output(BaseModel):
    content:str=Field(description="Relevant response of the user query")
    title: str
    summary: str


class research_report_response(BaseModel):
    id: int
    title: str
    summary: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}