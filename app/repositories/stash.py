from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StashItem, Title
from app.services.catalog import CatalogEntry


def add_entries(session: Session, user_id: str, entries: list[CatalogEntry]) -> int:
    """Save titles and add them to a user's stash. Returns how many were new."""
    unique = {e.key: e for e in entries}
    existing = set(
        session.scalars(
            select(StashItem.title_key).where(StashItem.user_id == user_id)
        )
    )
    now = datetime.now(timezone.utc)
    added = 0

    for key, entry in unique.items():
        title = session.get(Title, key)
        if title is None:
            title = Title(key=key)
            session.add(title)
        title.title = entry.title
        title.year = entry.year
        title.type = entry.type
        title.genres = entry.genres
        title.imdb_rating = entry.imdb_rating
        title.streaming = entry.streaming

        if key not in existing:
            session.add(StashItem(user_id=user_id, title_key=key, added_at=now))
            added += 1

    session.commit()
    return added


def list_items(session: Session, user_id: str) -> list[StashItem]:
    stmt = (
        select(StashItem)
        .where(StashItem.user_id == user_id)
        .order_by(StashItem.added_at.desc(), StashItem.id.asc())
    )
    return list(session.scalars(stmt))


def _get_item(session: Session, user_id: str, key: str) -> StashItem | None:
    stmt = select(StashItem).where(
        StashItem.user_id == user_id, StashItem.title_key == key
    )
    return session.scalars(stmt).first()


def set_watched(session: Session, user_id: str, key: str, watched: bool) -> bool:
    item = _get_item(session, user_id, key)
    if item is None:
        return False
    item.watched = watched
    session.commit()
    return True


def remove_item(session: Session, user_id: str, key: str) -> bool:
    item = _get_item(session, user_id, key)
    if item is None:
        return False
    session.delete(item)
    session.commit()
    return True