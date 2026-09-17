from sqlalchemy import delete, select, update

from research_copilot_server.models.research import Research


def create_research(db, research):
    db.add(research)
    db.commit()
    db.refresh(research)
    return research


def get_all_research(db):
    researches = db.scalars(select(Research)).all()
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

