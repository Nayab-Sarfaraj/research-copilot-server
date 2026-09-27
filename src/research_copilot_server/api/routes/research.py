from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from research_copilot_server.config.db import get_db
from research_copilot_server.dependencies.auth import get_current_user
from research_copilot_server.models.user import User
from research_copilot_server.schema.report import ResearchReportResponse, SourceResponse
from research_copilot_server.schema.research import (
    ResearchListResponse,
    ResearchResponse,
    create_research_response,
    paginated_research_response,
    update_research_body,
    user_query_body,
    user_query_response,
)
from research_copilot_server.services import research as research_service

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ResearchResponse, include_in_schema=False)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ResearchResponse)
async def register_user_query(
    user_query: user_query_body,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    research = await research_service.create_research(db, user_query, user_id=current_user.id)
    return research


@router.get("", status_code=status.HTTP_200_OK, response_model=ResearchListResponse, include_in_schema=False)
@router.get("/", status_code=status.HTTP_200_OK, response_model=ResearchListResponse)
def get_all_research(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return research_service.get_paginated_research(db, page=page, limit=limit, user_id=current_user.id)


@router.get("/{research_id}", status_code=status.HTTP_200_OK, response_model=ResearchResponse)
def get_research_by_id(
    research_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return research_service.get_research_by_id(db, research_id, user_id=current_user.id)


@router.get("/{research_id}/report", status_code=status.HTTP_200_OK, response_model=ResearchReportResponse)
def get_research_report(
    research_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return research_service.get_research_report(db, research_id, user_id=current_user.id)


@router.get("/{research_id}/sources", status_code=status.HTTP_200_OK, response_model=list[SourceResponse])
def get_research_sources(
    research_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    research = research_service.get_research_by_id(db, research_id, user_id=current_user.id)
    return research.sources


@router.delete("/{research_id}", status_code=status.HTTP_200_OK)
def delete_research(
    research_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return research_service.delete_research(db, research_id, user_id=current_user.id)


@router.put("/{research_id}", status_code=status.HTTP_200_OK, response_model=ResearchResponse)
def update_research(
    research_id: int,
    update_body: update_research_body,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return research_service.update_research(db, research_id, update_body, user_id=current_user.id)



