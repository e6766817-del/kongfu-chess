"""Standard ELO rating update for a single decisive (win/loss) game.

Kept as a pure function so it's trivial to unit test in isolation from
sqlite/networking -- kfchess.server.accounts.AccountStore.record_result
is the only caller.
"""

K_FACTOR = 32


def update_ratings(winner_rating, loser_rating, k=K_FACTOR):
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    new_winner_rating = round(winner_rating + k * (1 - expected_winner))
    new_loser_rating = round(loser_rating + k * (0 - (1 - expected_winner)))
    return new_winner_rating, new_loser_rating
