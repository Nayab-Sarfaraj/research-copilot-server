from fastapi import FastAPI
import inngest.fast_api
from research_copilot_server.config.db import engine,Base,get_db
from research_copilot_server.api.routes.document import router as document_router
from research_copilot_server.api.routes.health import router as health_router
from research_copilot_server.api.routes.research import router as research_router
from research_copilot_server.inngest.index import inngest,inngest_client,process_research

app = FastAPI()

app.include_router(health_router)
app.include_router(document_router, prefix="/document")
app.include_router(research_router,prefix="/research")

Base.metadata.create_all(bind=engine)



inngest.fast_api.serve(app, inngest_client, [process_research])



