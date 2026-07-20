from kfchess.server.elo import update_ratings


def test_equal_ratings_split_evenly_at_k32():
    new_winner, new_loser = update_ratings(1200, 1200)
    assert new_winner == 1216
    assert new_loser == 1184


def test_expected_win_gains_less_than_upset_win():
    favorite_winner, favorite_loser = update_ratings(1600, 1200)
    underdog_winner, underdog_loser = update_ratings(1200, 1600)

    assert favorite_winner - 1600 < underdog_winner - 1200
    assert 1200 - favorite_loser < 1600 - underdog_loser


def test_winner_always_gains_and_loser_always_loses():
    new_winner, new_loser = update_ratings(1000, 1400)
    assert new_winner > 1000
    assert new_loser < 1400
