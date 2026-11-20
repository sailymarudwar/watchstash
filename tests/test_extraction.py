from types import SimpleNamespace

import pytest

from app.services import extraction
from app.services.extraction import ExtractionError, _parse_titles


def test_parses_plain_json_list():
    assert _parse_titles('["Dark", "Parasite"]') == ["Dark", "Parasite"]


def test_strips_markdown_code_fences():
    assert _parse_titles('```json\n["Dark"]\n```') == ["Dark"]


def test_removes_duplicates_and_blanks_keeping_order():
    assert _parse_titles('["Dark", "", "Dark", "Parasite", 5]') == ["Dark", "Parasite"]


def test_invalid_json_raises():
    with pytest.raises(ExtractionError):
        _parse_titles("not json")


def test_non_list_raises():
    with pytest.raises(ExtractionError):
        _parse_titles('{"title": "Dark"}')


def test_parses_list_surrounded_by_other_words():
    raw = 'Here are the titles:\n["Dark", "Parasite"]\nLet me know if you need more.'
    assert _parse_titles(raw) == ["Dark", "Parasite"]


def test_parses_an_empty_list():
    assert _parse_titles("[]") == []


def test_reply_with_words_only_raises():
    with pytest.raises(ExtractionError):
        _parse_titles("I could not find any titles in that text.")


def test_unfinished_list_raises():
    with pytest.raises(ExtractionError):
        _parse_titles('["Dark", ')


def _fake_client(blocks, seen=None):
    class Messages:
        def create(self, **kwargs):
            if seen is not None:
                seen.update(kwargs)
            return SimpleNamespace(content=blocks)

    return SimpleNamespace(messages=Messages())


def test_skips_thinking_blocks_before_the_text(monkeypatch):
    blocks = [
        SimpleNamespace(type="thinking", thinking=""),
        SimpleNamespace(type="text", text='["Dark", "Parasite"]'),
    ]
    monkeypatch.setattr(extraction, "_client", lambda: _fake_client(blocks))
    assert extraction.extract_titles("anything") == ["Dark", "Parasite"]


def test_reply_without_a_text_block_raises(monkeypatch):
    blocks = [SimpleNamespace(type="thinking", thinking="")]
    monkeypatch.setattr(extraction, "_client", lambda: _fake_client(blocks))
    with pytest.raises(ExtractionError):
        extraction.extract_titles("anything")


def test_request_turns_thinking_off(monkeypatch):
    seen = {}
    blocks = [SimpleNamespace(type="text", text='["Dark"]')]
    monkeypatch.setattr(extraction, "_client", lambda: _fake_client(blocks, seen))
    extraction.extract_titles("anything")
    assert seen["thinking"] == {"type": "disabled"}