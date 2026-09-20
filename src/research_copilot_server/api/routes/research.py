from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from research_copilot_server.config.db import get_db
from research_copilot_server.schema.research import (
    create_research_response,
    update_research_body,
    user_query_body,
    user_query_response,
)
from research_copilot_server.services import research as research_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=user_query_response)
async def register_user_query(user_query: user_query_body, db: Session = Depends(get_db)):
    research = await research_service.create_research(db, user_query)
    return research


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[user_query_response])
def get_all_research(db: Session = Depends(get_db)):
    return research_service.get_all_research(db)


@router.get("/{research_id}", status_code=status.HTTP_200_OK, response_model=user_query_response)
def get_research_by_id(research_id: int, db: Session = Depends(get_db)):
    return research_service.get_research_by_id(db, research_id)


@router.delete("/{research_id}", status_code=status.HTTP_200_OK)
def delete_research(research_id: int, db: Session = Depends(get_db)):
    return research_service.delete_research(db, research_id)


@router.put("/{research_id}", status_code=status.HTTP_200_OK, response_model=user_query_response)
def update_research(research_id: int, update_body: update_research_body, db: Session = Depends(get_db)):
    return research_service.update_research(db, research_id, update_body)


