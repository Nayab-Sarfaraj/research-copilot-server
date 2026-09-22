from sqlalchemy import select

from research_copilot_server.models.documents import Document


def create_documents(db, documents: list[Document]):
    db.add_all(documents)
    db.commit()

    for document in documents:
        db.refresh(document)

    return documents


def search_documents(db, embedding: list[float], limit: int = 5) -> list[tuple[Document, float]]:
    distance = Document.embedding.cosine_distance(embedding).label("distance")
    statement = (
        select(Document, distance)
        .where(Document.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    return list(db.execute(statement).all())
