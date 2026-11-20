from types import SimpleNamespace

import pytest

from app.services import extraction
from app.services.extraction import ExtractionError, TitleQuery, _parse_titles


def test_parses_plain_json_list():
    assert _parse_titles('["Dark", "Parasite"]') == [TitleQuery("Dark"), TitleQuery("Parasite")]


def test_strips_markdown_code_fences():
    assert _parse_titles('```json\n["Dark"]\n```') == [TitleQuery("Dark")]


def test_removes_duplicates_and_blanks_keeping_order():
    assert _parse_titles('["Dark", "", "Dark", "Parasite", 5]') == [TitleQuery("Dark"), TitleQuery("Parasite")]


def test_invalid_json_raises():
    with pytest.raises(ExtractionError):
        _parse_titles("not json")


def test_non_list_raises():
    with pytest.raises(ExtractionError):
        _parse_titles('{"title": "Dark"}')


def test_parses_list_surrounded_by_other_words():
    raw = 'Here are the titles:\n["Dark", "Parasite"]\nLet me know if you need more.'
    assert _parse_titles(raw) == [TitleQuery("Dark"), TitleQuery("Parasite")]


def test_parses_an_empty_list():
    assert _parse_titles("[]") == []


def test_reply_with_words_only_raises():
    with pytest.raises(ExtractionError):
        _parse_titles("I could not find any titles in that text.")


def test_unfinished_list_raises():
    with pytest.raises(ExtractionError):
        _parse_titles('["Dark", ')


def test_reads_titles_with_years():
    raw = '[{"title": "Oldboy", "year": 2003}, {"title": "Dark", "year": null}]'
    assert _parse_titles(raw) == [TitleQuery("Oldboy", 2003), TitleQuery("Dark")]


def test_ignores_implausible_years_and_bad_items():
    raw = '[{"title": "Saw", "year": "2004"}, {"title": "Up", "year": true}, {"year": 1999}, 7]'
    assert _parse_titles(raw) == [TitleQuery("Saw"), TitleQuery("Up")]


def test_same_title_with_different_years_is_kept_twice():
    raw = '[{"title": "The Thing", "year": 1982}, {"title": "The Thing", "year": 2011}]'
    assert _parse_titles(raw) == [TitleQuery("The Thing", 1982), TitleQuery("The Thing", 2011)]


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
    assert extraction.extract_titles("anything") == [
        TitleQuery("Dark"),
        TitleQuery("Parasite"),
    ]


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