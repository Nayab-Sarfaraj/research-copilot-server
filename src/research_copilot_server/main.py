import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import inngest.fast_api
from research_copilot_server.config.db import engine,Base,get_db
from research_copilot_server.api.routes.auth import router as auth_router
from research_copilot_server.api.routes.document import router as document_router
from research_copilot_server.api.routes.health import router as health_router
from research_copilot_server.api.routes.research import router as research_router
import research_copilot_server.models
from research_copilot_server.inngest.index import inngest,inngest_client,process_research

app = FastAPI()
logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8288"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(document_router, prefix="/document")
app.include_router(document_router, prefix="/documents")
app.include_router(research_router,prefix="/research")

Base.metadata.create_all(bind=engine)



inngest.fast_api.serve(app, inngest_client, [process_research])



