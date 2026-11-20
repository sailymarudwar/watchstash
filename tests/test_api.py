import pytest

from app.routes import stash as routes
from app.services.extraction import ExtractionError
from app.services.instagram import CaptionError

ALICE = {"X-Access-Code": "code-alice"}
BOB = {"X-Access-Code": "code-bob"}


@pytest.fixture
def fake_services(monkeypatch, make_entry):
    entries = {
        "Dark": make_entry("tv-1", "Dark"),
        "Parasite": make_entry("movie-2", "Parasite"),
    }
    monkeypatch.setattr(routes, "extract_titles", lambda text: ["Dark", "Parasite", "Unknown"])
    monkeypatch.setattr(routes, "lookup_title", lambda name: entries.get(name))


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_requires_access_code(client):
    assert client.get("/api/stash").status_code == 401


def test_rejects_wrong_access_code(client):
    r = client.get("/api/stash", headers={"X-Access-Code": "wrong"})
    assert r.status_code == 401


def test_extract_saves_titles_and_skips_unknown(client, fake_services):
    r = client.post("/api/extract", json={"text": "anything"}, headers=ALICE)
    assert r.status_code == 200
    body = r.json()
    assert body["added"] == 2
    assert [t["title"] for t in body["results"]] == ["Dark", "Parasite"]


def test_watched_and_remove_flow(client, fake_services):
    client.post("/api/extract", json={"text": "x"}, headers=ALICE)

    r = client.put("/api/stash/tv-1/watched", json={"watched": True}, headers=ALICE)
    assert r.status_code == 200
    items = client.get("/api/stash", headers=ALICE).json()["results"]
    assert {i["key"]: i["watched"] for i in items} == {"tv-1": True, "movie-2": False}

    assert client.delete("/api/stash/tv-1", headers=ALICE).status_code == 200
    items = client.get("/api/stash", headers=ALICE).json()["results"]
    assert [i["key"] for i in items] == ["movie-2"]


def test_users_cannot_see_each_others_stash(client, fake_services):
    client.post("/api/extract", json={"text": "x"}, headers=ALICE)
    assert client.get("/api/stash", headers=BOB).json()["results"] == []


def test_cannot_change_a_title_that_is_not_in_your_stash(client, fake_services):
    client.post("/api/extract", json={"text": "x"}, headers=ALICE)
    r = client.put("/api/stash/tv-1/watched", json={"watched": True}, headers=BOB)
    assert r.status_code == 404


def test_extraction_failure_returns_502(client, monkeypatch):
    def boom(text):
        raise ExtractionError("simulated failure")

    monkeypatch.setattr(routes, "extract_titles", boom)
    r = client.post("/api/extract", json={"text": "x"}, headers=ALICE)
    assert r.status_code == 502


def test_rejects_oversized_text(client):
    r = client.post("/api/extract", json={"text": "a" * 5001}, headers=ALICE)
    assert r.status_code == 422

def test_reel_link_without_readable_caption_returns_notice(client, monkeypatch):
    def fail(url):
        raise CaptionError("nope")

    monkeypatch.setattr(routes, "fetch_caption", fail)
    r = client.post(
        "/api/extract",
        json={"text": "https://www.instagram.com/reel/abc123/"},
        headers=ALICE,
    )
    assert r.status_code == 200
    assert r.json()["added"] == 0
    assert "caption" in r.json()["notice"]


def test_reel_link_caption_is_used_for_extraction(client, monkeypatch, make_entry):
    seen = {}
    monkeypatch.setattr(routes, "fetch_caption", lambda url: "Top picks: Dark")

    def fake_extract(text):
        seen["text"] = text
        return ["Dark"]

    monkeypatch.setattr(routes, "extract_titles", fake_extract)
    monkeypatch.setattr(routes, "lookup_title", lambda name: make_entry("tv-1", "Dark"))
    r = client.post(
        "/api/extract",
        json={"text": "https://www.instagram.com/reel/abc123/"},
        headers=ALICE,
    )
    assert r.json()["added"] == 1
    assert "Top picks: Dark" in seen["text"]