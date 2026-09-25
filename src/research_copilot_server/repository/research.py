from sqlalchemy import delete, func, select, update

from research_copilot_server.models.research import Research, ResearchStatus


def update_status(db, research_id: int, status: ResearchStatus) -> None:
    research = db.scalar(select(Research).where(Research.id == research_id))
    if research and research.status != status:
        research.status = status
        db.commit()




def create_research(db, research):
    db.add(research)
    db.commit()
    db.refresh(research)
    return research


def get_paginated_research(db, page: int = 1, limit: int = 10):
    page = max(1, page)
    limit = max(1, limit)
    offset = (page - 1) * limit
    total = db.scalar(select(func.count(Research.id))) or 0
    items = db.scalars(
        select(Research)
        .order_by(Research.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return items, total


def get_all_research(db, page: int | None = None, limit: int | None = None):
    if page is not None and limit is not None:
        return get_paginated_research(db, page=page, limit=limit)
    researches = db.scalars(select(Research).order_by(Research.created_at.desc())).all()
    return researches


def get_research_by_id(db, research_id):
    research = db.scalar(select(Research).where(Research.id == research_id))
    return research


def update_research(db, research_id, data):
    stmt = (
        update(Research)
        .where(Research.id == research_id)
        .values(**data.model_dump(exclude_unset=True))
    )

    result = db.execute(stmt)

    if result.rowcount == 0:
        return None

    db.commit()

    return db.scalar(select(Research).where(Research.id == research_id))


def delete_research(db, research_id):
    stmt = delete(Research).where(Research.id == research_id)

    result = db.execute(stmt)

    if result.rowcount == 0:
        return None

    db.commit()

    return True

