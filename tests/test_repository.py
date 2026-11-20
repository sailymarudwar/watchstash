from app.repositories import stash


def test_add_entries_counts_only_new_titles(session, make_entry):
    assert stash.add_entries(session, "alice", [make_entry()]) == 1
    assert stash.add_entries(session, "alice", [make_entry()]) == 0


def test_stashes_are_separate_per_user(session, make_entry):
    stash.add_entries(session, "alice", [make_entry()])
    assert stash.list_items(session, "bob") == []


def test_watched_mark_is_per_user(session, make_entry):
    stash.add_entries(session, "alice", [make_entry()])
    stash.add_entries(session, "bob", [make_entry()])
    stash.set_watched(session, "alice", "tv-1", True)
    assert stash.list_items(session, "alice")[0].watched is True
    assert stash.list_items(session, "bob")[0].watched is False


def test_set_watched_on_missing_title_returns_false(session):
    assert stash.set_watched(session, "alice", "nope", True) is False


def test_remove_item(session, make_entry):
    stash.add_entries(session, "alice", [make_entry()])
    assert stash.remove_item(session, "alice", "tv-1") is True
    assert stash.list_items(session, "alice") == []
    assert stash.remove_item(session, "alice", "tv-1") is False