import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import current_user
from app.database import get_session
from app.models import StashItem
from app.repositories import stash as repo
from app.schemas import ExtractRequest, StashOut, TitleOut, WatchedRequest
from app.services.catalog import lookup_title
from app.services.extraction import ExtractionError, extract_titles

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

MAX_TITLES = 15  # per request, to cap lookups and cost


def _to_out(item: StashItem) -> TitleOut:
    e = item.entry
    return TitleOut(
        key=e.key,
        title=e.title,
        year=e.year,
        type=e.type,
        genres=e.genres,
        imdb_rating=e.imdb_rating,
        streaming=e.streaming,
        watched=item.watched,
    )


def _stash_out(session: Session, user: str, added: int = 0) -> StashOut:
    items = repo.list_items(session, user)
    return StashOut(results=[_to_out(i) for i in items], added=added)


@router.get("/stash", response_model=StashOut)
def get_stash(
    user: str = Depends(current_user),
    session: Session = Depends(get_session),
):
    return _stash_out(session, user)


@router.post("/extract", response_model=StashOut)
def extract(
    body: ExtractRequest,
    user: str = Depends(current_user),
    session: Session = Depends(get_session),
):
    try:
        titles = extract_titles(body.text)
    except ExtractionError:
        logger.exception("Title extraction failed")
        raise HTTPException(
            status_code=502, detail="Could not read titles from that text. Try again."
        )

    with ThreadPoolExecutor(max_workers=5) as pool:
        looked_up = pool.map(lookup_title, titles[:MAX_TITLES])
        entries = [e for e in looked_up if e is not None]

    added = repo.add_entries(session, user, entries)
    return _stash_out(session, user, added)


@router.put("/stash/{key}/watched")
def set_watched(
    key: str,
    body: WatchedRequest,
    user: str = Depends(current_user),
    session: Session = Depends(get_session),
):
    if not repo.set_watched(session, user, key, body.watched):
        raise HTTPException(status_code=404, detail="Title not in your stash")
    return {"ok": True}


@router.delete("/stash/{key}")
def remove(
    key: str,
    user: str = Depends(current_user),
    session: Session = Depends(get_session),
):
    if not repo.remove_item(session, user, key):
        raise HTTPException(status_code=404, detail="Title not in your stash")
    return {"ok": True}