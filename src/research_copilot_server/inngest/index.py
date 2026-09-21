import logging
import inngest

from research_copilot_server.config.db import SessionLocal
from research_copilot_server.models.research import ResearchStatus
from research_copilot_server.models.research_reports import ResearchReport
from research_copilot_server.repository import research as research_repository
from research_copilot_server.services.workflow import workflow


# Create an Inngest client
inngest_client = inngest.Inngest(
    app_id="fast_api_example",
    logger=logging.getLogger("uvicorn"),
)

async def _mark_processing(research_id: int) -> dict[str, int | str]:
    db = SessionLocal()
    try:
        research = research_repository.get_research_by_id(db, research_id)
        if research is None:
            raise inngest.NonRetriableError(f"Research {research_id} was not found")

        research.status = ResearchStatus.PROCESSING
        db.commit()
        return {"id": research.id, "query": research.query}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def _run_workflow(query: str) -> dict[str, str]:
    
    report_data = await workflow.ainvoke(
        {
            "query": query,
            "messages": [],
            "search_count": 0,
        }
    )

    return {
        "title": report_data["title"],
        "summary": report_data["summary"],
        "content": report_data["content"],
    }


async def _mark_failed(research_id: int, error: str) -> str:
    db = SessionLocal()
    try:
        research = research_repository.get_research_by_id(db, research_id)
        if research is None:
            raise inngest.NonRetriableError(f"Research {research_id} was not found")

        research.status = ResearchStatus.FAILED
        research.error_message = error
        db.commit()
        return f"Research {research_id} failed"
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def _save_report(research_id: int, report_data: dict[str, str]) -> str:
    db = SessionLocal()
    try:
        research = research_repository.get_research_by_id(db, research_id)
        if research is None:
            raise inngest.NonRetriableError(f"Research {research_id} was not found")

        research.report = ResearchReport(
            title=report_data["title"],
            summary=report_data["summary"],
            content=report_data["content"],
        )
        research.status = ResearchStatus.COMPLETED
        db.commit()
        return f"Research {research_id} completed"
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def _handle_failure(ctx: inngest.Context) -> None:
    failure_data = ctx.event.data
    original_event = failure_data["event"]
    error = failure_data["error"]
    error_message = error.get("message", str(error)) if isinstance(error, dict) else str(error)

    await ctx.step.run(
        "mark-research-failed",
        _mark_failed,
        int(original_event["data"]["research_id"]),
        error_message,
    )


@inngest_client.create_function(
    fn_id="process_research",
    trigger=inngest.TriggerEvent(event="research/requested"),
    on_failure=_handle_failure,
    retries=2,
)
async def process_research(ctx: inngest.Context) -> str:
    research_id = int(ctx.event.data["research_id"])

    research = await ctx.step.run(
        "mark-processing",
        _mark_processing,
        research_id,
    )
    report_data = await ctx.step.run(
        "run-research-workflow",
        _run_workflow,
        research["query"],
    )

    return await ctx.step.run(
        "save-research-report",
        _save_report,
        research["id"],
        report_data,
    )


