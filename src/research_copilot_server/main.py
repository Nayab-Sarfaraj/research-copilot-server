from fastapi import FastAPI
from research_copilot_server.config.db import engine,Base,get_db
from research_copilot_server.api.routes.health import router as health_router
from research_copilot_server.api.routes.research import router as research_router

app = FastAPI()

app.include_router(health_router)
app.include_router(research_router,prefix="/research")

Base.metadata.create_all(bind=engine)



