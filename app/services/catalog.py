import logging
from dataclasses import dataclass

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

TMDB_URL = "https://api.themoviedb.org/3"
OMDB_URL = "https://www.omdbapi.com/"


@dataclass
class CatalogEntry:
    key: str
    title: str
    year: str
    type: str
    genres: list[str]
    imdb_rating: str | None
    streaming: list[str]


def _get_json(url: str, params: dict) -> dict | None:
    """GET a URL and return JSON, or None on any failure.

    We never log the exception message: it can contain the full URL,
    including our API key.
    """
    try:
        response = requests.get(
            url, params=params, timeout=get_settings().http_timeout_seconds
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        logger.warning("HTTP %s from %s", exc.response.status_code, url)
    except requests.RequestException as exc:
        logger.warning("Request to %s failed: %s", url, type(exc).__name__)
    return None


def _fetch_imdb_rating(imdb_id: str | None) -> str | None:
    if not imdb_id:
        return None
    data = _get_json(
        OMDB_URL, {"apikey": get_settings().omdb_api_key, "i": imdb_id}
    )
    rating = (data or {}).get("imdbRating")
    return None if rating in (None, "N/A") else rating

def _pick_best(matches: list[dict], title: str) -> dict:
    wanted = title.strip().lower()

    def name(result: dict) -> str:
        return (result.get("title") or result.get("name") or "").strip().lower()

    exact = [r for r in matches if name(r) == wanted]
    pool = exact or matches
    return max(pool, key=lambda r: r.get("popularity", 0))


def lookup_title(title: str) -> CatalogEntry | None:
    settings = get_settings()

    search = _get_json(
        f"{TMDB_URL}/search/multi",
        {"api_key": settings.tmdb_api_key, "query": title},
    )
    if not search:
        return None
    matches = [
        r for r in search.get("results", [])
        if r.get("media_type") in ("movie", "tv")
    ]
    if not matches:
        logger.info("No catalog match for %r", title)
        return None

    best = _pick_best(matches, title)
    kind = best["media_type"]
    details = _get_json(
        f"{TMDB_URL}/{kind}/{best['id']}",
        {
            "api_key": settings.tmdb_api_key,
            "append_to_response": "external_ids,watch/providers",
        },
    )
    if not details:
        return None

    providers = (
        details.get("watch/providers", {}).get("results", {}).get(settings.region, {})
    )
    imdb_id = details.get("imdb_id") or details.get("external_ids", {}).get("imdb_id")

    return CatalogEntry(
        key=f"{kind}-{best['id']}",
        title=details.get("title") or details.get("name") or title,
        year=(details.get("release_date") or details.get("first_air_date") or "")[:4],
        type="Movie" if kind == "movie" else "TV Series",
        genres=[g["name"] for g in details.get("genres", [])],
        imdb_rating=_fetch_imdb_rating(imdb_id),
        streaming=[p["provider_name"] for p in providers.get("flatrate", [])],
    )