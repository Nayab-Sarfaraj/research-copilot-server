from research_copilot_server.schema.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
    token_response,
    user_login_body,
    user_register_body,
    user_register_response,
    user_response,
)
from research_copilot_server.schema.document import (
    DocumentChunkResponse,
    DocumentResponse,
)
from research_copilot_server.schema.report import (
    ResearchReportResponse,
    SourceResponse,
    model_output,
    research_report_response,
)
from research_copilot_server.schema.research import (
    PaginatedResearchResponse,
    ResearchListResponse,
    ResearchResponse,
    create_research_response,
    paginated_research_response,
    update_research_body,
    user_query_body,
    user_query_response,
)

__all__ = [
    # Auth
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "UserRegisterResponse",
    "user_register_body",
    "user_login_body",
    "user_response",
    "token_response",
    "user_register_response",
    # Document
    "DocumentResponse",
    "DocumentChunkResponse",
    # Research
    "ResearchResponse",
    "ResearchListResponse",
    "user_query_body",
    "update_research_body",
    "user_query_response",
    "create_research_response",
    "paginated_research_response",
    "PaginatedResearchResponse",
    # Report & Source
    "ResearchReportResponse",
    "SourceResponse",
    "model_output",
    "research_report_response",
]
