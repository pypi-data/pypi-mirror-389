from __future__ import annotations
import random
from typing import Optional, TypedDict, Literal


class CoinflipResult(TypedDict):
    game: Literal["coinflip"]
    guess: Literal["heads", "tails"]
    flip: Literal["heads", "tails"]
    win: bool
    payout: int
    prob_heads: float


def coinflip(
    guess: str,
    bet: int = 1,
    rng: Optional[random.Random] = None,
    bias: float = 0.5,
) -> CoinflipResult:
    if not isinstance(guess, str):
        raise ValueError("guess must be a string 'heads' or 'tails'.")
    g = guess.strip().lower()
    if g not in {"heads", "tails"}:
        raise ValueError("guess must be 'heads' or 'tails'.")
    if not isinstance(bet, int) or bet <= 0:
        raise ValueError("bet must be a positive integer.")
    if not (0.0 <= bias <= 1.0):
        raise ValueError("bias must be between 0.0 and 1.0 inclusive.")

    r = rng if rng is not None else random.Random()
    x = r.random()
    flip = "heads" if x < bias else "tails"
    win = (flip == g)
    payout = bet if win else -bet

    return CoinflipResult(
        game="coinflip",
        guess=g,
        flip=flip,
        win=win,
        payout=payout,
        prob_heads=bias,
    )
