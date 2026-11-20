import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import init_db
from app.routes import stash
from pathlib import Path

from fastapi.responses import FileResponse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not get_settings().users:
        raise RuntimeError(
            "ACCESS_CODES is not set. Add e.g. ACCESS_CODES=yourname:some-long-code to .env"
        )
    init_db()
    yield


app = FastAPI(title="WatchStash", lifespan=lifespan)
app.include_router(stash.router)


@app.get("/health")
def health():
    return {"status": "ok"}

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")