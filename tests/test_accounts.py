import pytest

from kfchess.server.accounts import DEFAULT_RATING, AccountStore


@pytest.fixture
def store(tmp_path):
    return AccountStore(str(tmp_path / "accounts.db"))


def test_first_login_creates_account_at_default_rating(store):
    result = store.login("alice", "hunter2")
    assert result.ok
    assert result.rating == DEFAULT_RATING


def test_second_login_with_correct_password_succeeds(store):
    store.login("alice", "hunter2")
    result = store.login("alice", "hunter2")
    assert result.ok
    assert result.rating == DEFAULT_RATING


def test_login_with_wrong_password_is_rejected(store):
    store.login("alice", "hunter2")
    result = store.login("alice", "wrong-password")
    assert not result.ok
    assert result.reason is not None


def test_record_result_updates_both_ratings(store):
    store.login("alice", "pw")
    store.login("bob", "pw")

    new_winner_rating, new_loser_rating = store.record_result("alice", "bob")

    assert new_winner_rating == 1216
    assert new_loser_rating == 1184
    assert store.get_rating("alice") == 1216
    assert store.get_rating("bob") == 1184
