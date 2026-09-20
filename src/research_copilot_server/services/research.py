from fastapi import HTTPException, status
from research_copilot_server.models.research import ResearchStatus
from research_copilot_server.models.research import Research
from research_copilot_server.models.research_reports import ResearchReport
from research_copilot_server.repository import research as research_repository
from research_copilot_server.services import llm
from research_copilot_server.schema.research import update_research_body

async def create_research(db, data):

    research = Research(
        query=data.query,
        status=ResearchStatus.PROCESSING,
    )

    research = research_repository.create_research(db, research)

    try:
        report_data = await llm.generate_response(data.query)

        research.report = ResearchReport(
            title=report_data.title,
            summary=report_data.summary,
            content=report_data.content,
        )

        research.status = ResearchStatus.COMPLETED

        return research_repository.update_research(
            db,
            research.id,
            {"status": ResearchStatus.COMPLETED}
        )

    except Exception:
        research.status = ResearchStatus.FAILED

        return research_repository.update_research(
            db,
            research.id,
            update_research_body(status=ResearchStatus.FAILED)
        )



def get_all_research(db):
    return research_repository.get_all_research(db)


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

