import pytest
import requests

from app.services import instagram
from app.services.instagram import CaptionError, fetch_caption, find_reel_url


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_finds_reel_link_in_shared_text():
    text = "Check this out https://www.instagram.com/reel/DXabc123/?igsh=xyz"
    assert find_reel_url(text) == "https://www.instagram.com/reel/DXabc123/?igsh=xyz"


def test_ignores_non_instagram_links():
    assert find_reel_url("https://example.com/reel/abc") is None


def test_fetch_caption_uses_title_when_present(monkeypatch):
    monkeypatch.setattr(
        instagram.requests, "get",
        lambda *a, **k: FakeResponse({"title": "Top 5 thrillers: Dark, Parasite"}),
    )
    assert "Dark" in fetch_caption("https://www.instagram.com/reel/abc/")


def test_fetch_caption_falls_back_to_embed_html(monkeypatch):
    markup = "<blockquote><a>View post</a><p>Watch Gone Girl &amp; Prisoners</p></blockquote>"
    monkeypatch.setattr(
        instagram.requests, "get", lambda *a, **k: FakeResponse({"html": markup})
    )
    assert "Gone Girl & Prisoners" in fetch_caption("https://www.instagram.com/reel/abc/")


def test_fetch_caption_raises_on_network_error(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(instagram.requests, "get", boom)
    with pytest.raises(CaptionError):
        fetch_caption("https://www.instagram.com/reel/abc/")