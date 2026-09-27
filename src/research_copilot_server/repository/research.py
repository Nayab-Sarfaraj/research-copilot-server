from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import selectinload

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


def get_paginated_research(db, page: int = 1, limit: int = 10, user_id: int | None = None):
    page = max(1, page)
    limit = max(1, limit)
    offset = (page - 1) * limit

    count_stmt = select(func.count(Research.id))
    query_stmt = (
        select(Research)
        .options(selectinload(Research.report), selectinload(Research.sources))
        .order_by(Research.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    if user_id is not None:
        count_stmt = count_stmt.where(Research.user_id == user_id)
        query_stmt = query_stmt.where(Research.user_id == user_id)

    total = db.scalar(count_stmt) or 0
    items = db.scalars(query_stmt).all()
    return items, total


def get_all_research(db, page: int | None = None, limit: int | None = None, user_id: int | None = None):
    if page is not None and limit is not None:
        return get_paginated_research(db, page=page, limit=limit, user_id=user_id)
    stmt = (
        select(Research)
        .options(selectinload(Research.report), selectinload(Research.sources))
        .order_by(Research.created_at.desc())
    )
    if user_id is not None:
        stmt = stmt.where(Research.user_id == user_id)
    researches = db.scalars(stmt).all()
    return researches


def get_research_by_id(db, research_id: int, user_id: int | None = None):
    stmt = (
        select(Research)
        .options(selectinload(Research.report), selectinload(Research.sources))
        .where(Research.id == research_id)
    )
    if user_id is not None:
        stmt = stmt.where(Research.user_id == user_id)
    research = db.scalar(stmt)
    return research


def update_research(db, research_id: int, data, user_id: int | None = None):
    stmt = (
        update(Research)
        .where(Research.id == research_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    if user_id is not None:
        stmt = stmt.where(Research.user_id == user_id)

    result = db.execute(stmt)

    if result.rowcount == 0:
        return None

    db.commit()

    select_stmt = (
        select(Research)
        .options(selectinload(Research.report), selectinload(Research.sources))
        .where(Research.id == research_id)
    )
    if user_id is not None:
        select_stmt = select_stmt.where(Research.user_id == user_id)
    return db.scalar(select_stmt)


def delete_research(db, research_id: int, user_id: int | None = None):
    stmt = delete(Research).where(Research.id == research_id)
    if user_id is not None:
        stmt = stmt.where(Research.user_id == user_id)

    result = db.execute(stmt)

    if result.rowcount == 0:
        return None

    db.commit()

    return True

