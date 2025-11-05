import pytest
# tests/test_coinflip.py
from nimbuscasino.coinflip import coinflip



class FakeRNG:
    def __init__(self, values):
        self.values = list(values)
        self.i = 0

    def random(self):
        if self.i < len(self.values):
            v = self.values[self.i]
            self.i += 1
            return v
        return self.values[-1]


def test_coinflip_win_heads_with_fair_bias():
    rng = FakeRNG([0.2])
    res = coinflip("heads", bet=3, rng=rng, bias=0.5)
    assert res["flip"] == "heads"
    assert res["win"] is True
    assert res["payout"] == 3
    assert res["game"] == "coinflip"

def test_coinflip_lose_heads_with_fair_bias():
    rng = FakeRNG([0.9])
    res = coinflip("heads", bet=2, rng=rng, bias=0.5)
    assert res["flip"] == "tails"
    assert res["win"] is False
    assert res["payout"] == -2

def test_bias_edge_cases_always_heads_at_1():
    rng = FakeRNG([0.9999])
    res = coinflip("heads", bet=5, rng=rng, bias=1.0)
    assert res["flip"] == "heads"
    assert res["win"] is True
    assert res["payout"] == 5
