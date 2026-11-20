from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Title(Base):
    """A movie or show. Shared by everyone, saved once."""

    __tablename__ = "titles"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[str] = mapped_column(String(4), default="")
    type: Mapped[str] = mapped_column(String(16))
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    imdb_rating: Mapped[str | None] = mapped_column(String(8), nullable=True)
    streaming: Mapped[list[str]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class StashItem(Base):
    """One person's saved title, with their own watched mark."""

    __tablename__ = "stash_items"
    __table_args__ = (UniqueConstraint("user_id", "title_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    title_key: Mapped[str] = mapped_column(ForeignKey("titles.key"))
    watched: Mapped[bool] = mapped_column(Boolean, default=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    entry: Mapped[Title] = relationship(lazy="joined")