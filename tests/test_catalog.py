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


def test_year_picks_the_film_from_that_year_over_a_more_popular_namesake():
    matches = [
        {"title": "The Game", "release_date": "2021-05-01", "popularity": 90},
        {"title": "The Game", "release_date": "1997-09-12", "popularity": 20},
    ]
    assert _pick_best(matches, "The Game", 1997)["release_date"] == "1997-09-12"


def test_year_allows_one_year_of_difference():
    matches = [
        {"title": "Saw", "release_date": "2005-01-01", "popularity": 5},
        {"title": "Saw", "release_date": "2015-01-01", "popularity": 50},
    ]
    assert _pick_best(matches, "Saw", 2004)["release_date"] == "2005-01-01"


def test_year_is_ignored_when_no_result_is_near_it():
    matches = [
        {"title": "Alpha", "release_date": "2010-01-01", "popularity": 5},
        {"title": "Alpha", "release_date": "2020-01-01", "popularity": 50},
    ]
    assert _pick_best(matches, "Alpha", 1950)["popularity"] == 50


def test_year_works_for_tv_first_air_date():
    matches = [
        {"name": "Dark", "first_air_date": "2017-12-01", "popularity": 5},
        {"name": "Dark", "first_air_date": "1990-01-01", "popularity": 50},
    ]
    assert _pick_best(matches, "Dark", 2017)["first_air_date"] == "2017-12-01"