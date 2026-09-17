from pydantic import BaseModel,Field
from typing import Literal

class UserQueryBody(BaseModel):
    query:str=Field(...,min_length=3,max_length=500,description="User's research query")

class UserQueryResponse(BaseModel):
    id:int
    query:str
    status:Literal["created","processing","failed","completed"]