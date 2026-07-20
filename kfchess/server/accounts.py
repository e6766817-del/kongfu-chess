"""AccountStore: sqlite3-backed player accounts -- username, salted/
hashed password, and ELO rating. A username is created the first time
it's seen at login (rating starts at 1200); after that, login just
verifies the password against the stored hash.

Plain stdlib (sqlite3 + hashlib pbkdf2_hmac) rather than an ORM or
bcrypt dependency, matching the rest of the project's minimal-
dependency style (see requirements.txt).
"""

import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass
from typing import Optional

from kfchess.server.elo import update_ratings

DEFAULT_RATING = 1200
PBKDF2_ITERATIONS = 200_000


@dataclass
class AuthResult:
    ok: bool
    rating: Optional[int] = None
    reason: Optional[str] = None


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS).hex()


class AccountStore:
    def __init__(self, path):
        self._connection = sqlite3.connect(path)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 1200
            )
            """
        )
        self._connection.commit()

    def login(self, username, password):
        row = self._connection.execute(
            "SELECT salt, password_hash, rating FROM players WHERE username = ?", (username,)
        ).fetchone()

        if row is None:
            salt = secrets.token_hex(16)
            password_hash = _hash_password(password, salt)
            self._connection.execute(
                "INSERT INTO players (username, salt, password_hash, rating) VALUES (?, ?, ?, ?)",
                (username, salt, password_hash, DEFAULT_RATING),
            )
            self._connection.commit()
            return AuthResult(ok=True, rating=DEFAULT_RATING)

        salt, stored_hash, rating = row
        if not hmac.compare_digest(_hash_password(password, salt), stored_hash):
            return AuthResult(ok=False, reason="wrong password")
        return AuthResult(ok=True, rating=rating)

    def get_rating(self, username):
        row = self._connection.execute("SELECT rating FROM players WHERE username = ?", (username,)).fetchone()
        return row[0] if row is not None else None

    def record_result(self, winner_username, loser_username):
        winner_rating = self.get_rating(winner_username)
        loser_rating = self.get_rating(loser_username)
        new_winner_rating, new_loser_rating = update_ratings(winner_rating, loser_rating)

        self._connection.execute(
            "UPDATE players SET rating = ? WHERE username = ?", (new_winner_rating, winner_username)
        )
        self._connection.execute(
            "UPDATE players SET rating = ? WHERE username = ?", (new_loser_rating, loser_username)
        )
        self._connection.commit()
        return new_winner_rating, new_loser_rating

    def close(self):
        self._connection.close()
