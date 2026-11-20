import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings

_header = APIKeyHeader(name="X-Access-Code", auto_error=False)


def current_user(code: str | None = Security(_header)) -> str:
    """Return the person's name for a valid access code, or reject the request."""
    if code:
        for known_code, name in get_settings().users.items():
            if secrets.compare_digest(code.encode(), known_code.encode()):
                return name
    raise HTTPException(status_code=401, detail="Invalid or missing access code")