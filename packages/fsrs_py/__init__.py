# FSRS v4 stub — replace with reference implementation.
from dataclasses import dataclass

@dataclass
class CardState:
    stability: float = 3.0
    difficulty: float = 0.3

def update(state: CardState, rating: int) -> tuple[float, float, int]:
    from math import floor
    s, d = state.stability, state.difficulty
    if rating == 1:
        s = max(1.0, s * 0.5); d = min(0.9, d + 0.05)
    elif rating == 2:
        s = max(1.5, s * 0.9); d = min(0.85, d + 0.02)
    elif rating == 3:
        s = max(2.0, s * 1.2); d = max(0.15, d - 0.01)
    else:
        s = max(3.0, s * 1.4); d = max(0.1, d - 0.02)
    return s, d, max(1, floor(s))
