import pytest

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