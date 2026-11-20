from app.services.catalog import _pick_best


def test_prefers_exact_name_match_over_more_popular_result():
    matches = [
        {"title": "Dark Shadows", "popularity": 90},
        {"name": "Dark", "popularity": 40},
    ]
    assert _pick_best(matches, "Dark")["name"] == "Dark"


def test_exact_match_ignores_case():
    matches = [
        {"title": "DARK", "popularity": 1},
        {"title": "Dark Shadows", "popularity": 99},
    ]
    assert _pick_best(matches, "Dark")["title"] == "DARK"


def test_picks_most_popular_among_exact_matches():
    matches = [
        {"title": "Dark", "popularity": 5},
        {"name": "Dark", "popularity": 50},
    ]
    assert _pick_best(matches, "Dark")["popularity"] == 50


def test_falls_back_to_most_popular_when_no_exact_match():
    matches = [
        {"title": "Alpha One", "popularity": 5},
        {"title": "Alpha Two", "popularity": 50},
    ]
    assert _pick_best(matches, "Alpha")["title"] == "Alpha Two"