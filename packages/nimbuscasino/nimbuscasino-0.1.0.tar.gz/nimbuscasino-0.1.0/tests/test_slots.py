import random
from nimbuscasino import spin_slots, SpinResult


def test_spin_slots_shapes_and_types():
    rng = random.Random(123)
    res = spin_slots(bet=2, rng=rng)
    assert isinstance(res, SpinResult)
    assert len(res.grid) == 3
    assert all(len(row) == 3 for row in res.grid)


def test_spin_slots_deterministic_with_seed():
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    a = spin_slots(bet=1, rng=rng1)
    b = spin_slots(bet=1, rng=rng2)
    assert a.grid == b.grid
    assert a.total_payout == b.total_payout


def test_invalid_bet_raises_error():
    import pytest
    with pytest.raises(ValueError):
        spin_slots(bet=0)
    with pytest.raises(ValueError):
        spin_slots(bet=-10)
