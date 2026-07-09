"""A board cell as a real value type, used everywhere a (row, col) pair
crossed module boundaries as bare ints in the old flat modules.

Frozen so it's hashable/comparable by value -- Board keys its storage
dict by Position, so two Position(2, 3) instances must be equal and
hash identically or lookups would silently miss.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def translated(self, delta_row, delta_col):
        return Position(self.row + delta_row, self.col + delta_col)

    def delta_to(self, other):
        return other.row - self.row, other.col - self.col
