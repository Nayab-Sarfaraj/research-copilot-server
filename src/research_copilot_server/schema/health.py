from pydantic import BaseModel


class ApiInfoResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str