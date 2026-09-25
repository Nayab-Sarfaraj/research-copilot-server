from fastapi import HTTPException, status
import inngest

from research_copilot_server.models.research import Research, ResearchStatus
from research_copilot_server.inngest.index import inngest_client
from research_copilot_server.repository import research as research_repository
from research_copilot_server.schema.research import update_research_body

async def create_research(db, data):

    research = Research(
        query=data.query,
        status=ResearchStatus.QUEUED,
    )

    research = research_repository.create_research(db, research)
    await inngest_client.send(
        inngest.Event(
            name="research/requested",
            data={"research_id": research.id},
        )
    )

    return research


def get_paginated_research(db, page: int = 1, limit: int = 10):
    items, total = research_repository.get_paginated_research(db, page=page, limit=limit)
    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
    }


def get_all_research(db, page: int = 1, limit: int = 10):
    return get_paginated_research(db, page=page, limit=limit)


def get_research_by_id(db, research_id):
    research = research_repository.get_research_by_id(db, research_id)
    if not research:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research with ID {research_id} does not exist")
    return research


def update_research(db, research_id, data):
    research = research_repository.update_research(db, research_id, data)
    if not research:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research with ID {research_id} does not exist")
    return research


def delete_research(db, research_id):
    is_deleted = research_repository.delete_research(db, research_id)
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research with ID {research_id} does not exist")
    return {"message": "Research deleted successfully"}

