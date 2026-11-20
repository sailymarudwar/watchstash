import json
import logging
from functools import lru_cache

from anthropic import Anthropic, APIError

from app.config import get_settings

logger = logging.getLogger(__name__)

PROMPT = (
    "Extract every movie and TV show title from the text below. "
    "Reply with ONLY a JSON list of title strings, nothing else.\n\n"
    "Text:\n{text}"
)


class ExtractionError(Exception):
    """Raised when titles cannot be extracted from the text."""


@lru_cache
def _client() -> Anthropic:
    settings = get_settings()
    return Anthropic(
        api_key=settings.anthropic_api_key,
        timeout=settings.http_timeout_seconds * 3,
    )


def _parse_titles(raw: str) -> list[str]:
    cleaned = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ExtractionError("Model returned invalid JSON") from exc
    if not isinstance(data, list):
        raise ExtractionError("Model did not return a list")
    titles = [t.strip() for t in data if isinstance(t, str) and t.strip()]
    return list(dict.fromkeys(titles))  # remove duplicates, keep order


def extract_titles(text: str) -> list[str]:
    settings = get_settings()
    try:
        response = _client().messages.create(
            model=settings.claude_model,
            max_tokens=1000,
            messages=[{"role": "user", "content": PROMPT.format(text=text)}],
        )
    except APIError as exc:
        logger.error("Claude API call failed: %s", type(exc).__name__)
        raise ExtractionError("Claude API call failed") from exc
    return _parse_titles(response.content[0].text)