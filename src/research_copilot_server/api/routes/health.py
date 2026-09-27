from fastapi import APIRouter

from research_copilot_server.schema.health import ApiInfoResponse, HealthResponse

router = APIRouter()


@router.get("/", response_model=ApiInfoResponse)
def home() -> ApiInfoResponse:
    return ApiInfoResponse(message="Research Copilot API")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")

