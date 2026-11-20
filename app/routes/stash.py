import logging
import re
import traceback
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
from app.services.instagram import CaptionError, fetch_caption, find_reel_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

MAX_TITLES = 15  # per request, to cap lookups and cost

# Patterns scrubbed from error messages before they are logged.
_SECRET_PATTERNS = (
    (re.compile(r"(api_?key=)[^&\s'\"]+", re.IGNORECASE), r"\1***"),
    (re.compile(r"postgres(?:ql)?(?:\+\w+)?://\S+", re.IGNORECASE), "postgres://***"),
    (re.compile(r"sk-[A-Za-z0-9_-]{10,}"), "sk-***"),
)


def _describe_crash(exc: Exception) -> str:
    """One log line for an unexpected error: its type, the innermost line of
    our own code it passed through, and a shortened message with secrets removed."""
    message = str(exc)[:300]
    for pattern, replacement in _SECRET_PATTERNS:
        message = pattern.sub(replacement, message)

    where = "unknown"
    for frame in traceback.extract_tb(exc.__traceback__):
        path = frame.filename.replace("\\", "/")
        if "/app/" in path:
            where = f"app/{path.split('/app/')[-1]}:{frame.lineno} in {frame.name}"
    return f"{type(exc).__name__} at {where}: {message}"


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


def _stash_out(
    session: Session, user: str, added: int = 0, notice: str | None = None
) -> StashOut:
    items = repo.list_items(session, user)
    return StashOut(results=[_to_out(i) for i in items], added=added, notice=notice)


@router.get("/stash", response_model=StashOut)
def get_stash(
    user: str = Depends(current_user),
    session: Session = Depends(get_session),
):
    return _stash_out(session, user)


def _extract_and_save(text: str, user: str, session: Session) -> StashOut:
    notice = None

    reel_url = find_reel_url(text)
    if reel_url:
        try:
            text = f"{text}\n\n{fetch_caption(reel_url)}"
        except CaptionError:
            notice = "Couldn’t read that reel’s caption. Paste the caption text instead."
            if not text.replace(reel_url, " ").strip():
                return _stash_out(session, user, 0, notice)

    try:
        titles = extract_titles(text)
    except ExtractionError:
        logger.exception("Title extraction failed")
        raise HTTPException(
            status_code=502, detail="Could not read titles from that text. Try again."
        )

    with ThreadPoolExecutor(max_workers=5) as pool:
        looked_up = pool.map(lookup_title, titles[:MAX_TITLES])
        entries = [e for e in looked_up if e is not None]

    added = repo.add_entries(session, user, entries)
    if not entries and notice is None:
        notice = "No titles found in that text."
    return _stash_out(session, user, added, notice)


@router.post("/extract", response_model=StashOut)
def extract(
    body: ExtractRequest,
    user: str = Depends(current_user),
    session: Session = Depends(get_session),
):
    try:
        return _extract_and_save(body.text, user, session)
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        logger.error("Extract crashed: %s", _describe_crash(exc))
        raise HTTPException(
            status_code=500, detail="Something went wrong on our side. Please try again."
        )


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