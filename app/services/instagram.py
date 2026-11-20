import html
import logging
import re

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

OEMBED_URL = "https://graph.facebook.com/v25.0/instagram_oembed"
REEL_URL = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:[\w.]+/)?(?:reels?|p|tv)/[\w-]+/?(?:\?[^\s]*)?",
    re.IGNORECASE,
)
TAGS = re.compile(r"<[^>]+>")
MAX_CAPTION_CHARS = 5000


class CaptionError(Exception):
    """Raised when a reel's caption cannot be read."""


def find_reel_url(text: str) -> str | None:
    match = REEL_URL.search(text)
    return match.group(0) if match else None


def _html_to_text(markup: str) -> str:
    text = html.unescape(TAGS.sub(" ", markup))
    return re.sub(r"\s+", " ", text).strip()


def fetch_caption(url: str) -> str:
    try:
        response = requests.get(
            OEMBED_URL,
            params={"url": url},
            timeout=get_settings().http_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.warning("Instagram oEmbed request failed: %s", type(exc).__name__)
        raise CaptionError("Could not reach Instagram") from exc
    except ValueError as exc:
        raise CaptionError("Unexpected response from Instagram") from exc

    text = (data.get("title") or "").strip() or _html_to_text(data.get("html", ""))
    if not text:
        raise CaptionError("No caption in the response")
    return text[:MAX_CAPTION_CHARS]