import pytest
from unittest.mock import Mock
from nimbuscasino.rps import rps


    #
    # Test functions
    #


def test_tie_check():
    """
    Test debugging... making sure that we can run a simple test that always passes.
    Note the use of the example_fixture in the parameter list - any setup and teardown in that fixture will be run before and after this test function executes
    From the main project directory, run the `python3 -m pytest` command to run all tests.
    """
    
    for move in ["rock", "paper", "scissors"]:
        mock_rng = Mock()
        mock_rng.choice = Mock(return_value=move)

        res = rps(move, bet=10, rng=mock_rng)

        assert res["result"] == "tie"
        assert res["payout"] == 0
        assert res["player"] == move
        assert res["computer"] == move

def test_win_check():
    """
    Test debugging... making sure that we can run a simple test that always passes.
    Note the use of the example_fixture in the parameter list - any setup and teardown in that fixture will be run before and after this test function executes
    From the main project directory, run the `python3 -m pytest` command to run all tests.
    """
    cases = [
        ("rock", "scissors"),
        ("paper", "rock"),
        ("scissors", "paper"),
    ]
    for player, comp in cases:
        mock_rng = Mock()
        mock_rng.choice = Mock(return_value=comp)

        res = rps(player, bet=5, rng=mock_rng)

        assert res["result"] == "win"
        assert res["payout"] == 5
        assert res["player"] == player
        assert res["computer"] == comp

def test_lose_check():
    """
    Test debugging... making sure that we can run a simple test that always passes.
    Note the use of the example_fixture in the parameter list - any setup and teardown in that fixture will be run before and after this test function executes
    From the main project directory, run the `python3 -m pytest` command to run all tests.
    """
    cases = [
        ("rock", "paper"),
        ("paper", "scissors"),
        ("scissors", "rock"),
    ]
    for player, comp in cases:
        mock_rng = Mock()
        mock_rng.choice = Mock(return_value=comp)

        res = rps(player, bet=7, rng=mock_rng)

        assert res["result"] == "lose"
        assert res["payout"] == -7
        assert res["player"] == player
        assert res["computer"] == comp

def test_invalid_choice():
    """
    Test that an invalid choice raises a ValueError.
    """
    with pytest.raises(ValueError):
        rps('invalid_choice')    