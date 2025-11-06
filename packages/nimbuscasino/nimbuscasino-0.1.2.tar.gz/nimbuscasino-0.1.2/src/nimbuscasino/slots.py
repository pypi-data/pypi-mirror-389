# src/nimbuscasino/slots.py
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Optional, Dict, List, TypedDict

class SlotsLineInfo(TypedDict):
    symbol: str
    count: int
    payout: int

@dataclass(frozen=True)
class SpinResult:
    grid: List[List[str]]
    lines: Dict[str, Dict[str, int]]
    total_payout: int

DEFAULT_SYMBOLS = ["🍒", "🍋", "🔔", "⭐", "7"]
DEFAULT_WEIGHTS = [30, 25, 20, 15, 10]
DEFAULT_PAYTABLE: Dict[str, Dict[int, int]] = {
    "🍒": {3: 5},
    "🍋": {3: 6},
    "🔔": {3: 12},
    "⭐":  {3: 20},
    "7":   {2: 5, 3: 50},
}

LINES = {
    "top":        [(0, 0), (0, 1), (0, 2)],
    "middle":     [(1, 0), (1, 1), (1, 2)],
    "bottom":     [(2, 0), (2, 1), (2, 2)],
    "diag_down":  [(0, 0), (1, 1), (2, 2)],
    "diag_up":    [(2, 0), (1, 1), (0, 2)],
}

def spin_slots(
    bet: int = 1,
    rng: Optional[random.Random] = None,
    symbols: Optional[List[str]] = None,
    weights: Optional[List[int]] = None,
    paytable: Optional[Dict[str, Dict[int, int]]] = None,
    rows: int = 3,
    cols: int = 3,
) -> SpinResult:
    if not isinstance(bet, int) or bet <= 0:
        raise ValueError("bet must be positive")
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive")

    r = rng or random.Random()
    syms = symbols or DEFAULT_SYMBOLS
    wts = weights or DEFAULT_WEIGHTS
    pt = paytable or DEFAULT_PAYTABLE
    if len(syms) != len(wts):
        raise ValueError("symbols and weights must be same length")

    grid: List[List[str]] = [[None] * cols for _ in range(rows)]  # type: ignore
    for c in range(cols):
        for rr in range(rows):
            grid[rr][c] = r.choices(syms, wts, k=1)[0]

    lines_out: Dict[str, Dict[str, int]] = {}
    total = 0
    for name, coords in LINES.items():
        if any(rr >= rows or cc >= cols for rr, cc in coords):
            continue
        seq = [grid[rr][cc] for rr, cc in coords]

        if seq[0] == seq[1] == seq[2]:
            sym = seq[0]
            mult = pt.get(sym, {}).get(3, 0)
            payout = bet * mult
            if payout:
                lines_out[name] = {"symbol": sym, "count": 3, "payout": payout}
                total += payout
        elif seq.count("7") == 2:
            mult = pt.get("7", {}).get(2, 0)
            payout = bet * mult
            if payout:
                lines_out[name] = {"symbol": "7", "count": 2, "payout": payout}
                total += payout

    return SpinResult(grid=grid, lines=lines_out, total_payout=total)
