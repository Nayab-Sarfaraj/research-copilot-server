from fastapi import HTTPException, status
import inngest

from research_copilot_server.models.research import Research, ResearchStatus
from research_copilot_server.inngest.index import inngest_client
from research_copilot_server.repository import research as research_repository
from research_copilot_server.schema.research import update_research_body

async def create_research(db, data, user_id: int | None = None):

    research = Research(
        query=data.query,
        status=ResearchStatus.QUEUED,
        user_id=user_id,
    )

    research = research_repository.create_research(db, research)
    await inngest_client.send(
        inngest.Event(
            name="research/requested",
            data={"research_id": research.id},
        )
    )

    return research


def get_paginated_research(db, page: int = 1, limit: int = 10, user_id: int | None = None):
    items, total = research_repository.get_paginated_research(db, page=page, limit=limit, user_id=user_id)
    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
    }


def get_all_research(db, page: int = 1, limit: int = 10, user_id: int | None = None):
    return get_paginated_research(db, page=page, limit=limit, user_id=user_id)


def get_research_by_id(db, research_id: int, user_id: int | None = None):
    research = research_repository.get_research_by_id(db, research_id)
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research with ID {research_id} does not exist",
        )
    if user_id is not None and research.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access this resource",
        )
    return research


def get_research_report(db, research_id: int, user_id: int | None = None):
    research = get_research_by_id(db, research_id, user_id=user_id)
    if not research.report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for research ID {research_id} does not exist",
        )
    return research.report



def update_research(db, research_id: int, data, user_id: int | None = None):
    research = research_repository.get_research_by_id(db, research_id)
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research with ID {research_id} does not exist",
        )
    if user_id is not None and research.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to modify this resource",
        )
    return research_repository.update_research(db, research_id, data)


def delete_research(db, research_id: int, user_id: int | None = None):
    research = research_repository.get_research_by_id(db, research_id)
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research with ID {research_id} does not exist",
        )
    if user_id is not None and research.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to delete this resource",
        )
    research_repository.delete_research(db, research_id)
    return {"message": "Research deleted successfully"}

