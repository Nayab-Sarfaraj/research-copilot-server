from fastapi import FastAPI
from research_copilot_server.config.db import create_engine,Base,get_db

app = FastAPI()

Base.metadata.create_all(bind=engine)



