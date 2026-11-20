from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class WatchedRequest(BaseModel):
    watched: bool


class TitleOut(BaseModel):
    key: str
    title: str
    year: str
    type: str
    genres: list[str]
    imdb_rating: str | None
    streaming: list[str]
    watched: bool


class StashOut(BaseModel):
    results: list[TitleOut]
    added: int = 0
    notice: str | None = None