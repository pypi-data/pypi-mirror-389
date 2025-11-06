"""
Test suite for the roulette_color function in nimbuscasino package.

Tests basic functionality including winning, losing, and edge cases.
"""

import pytest # type: ignore
from unittest.mock import Mock
from nimbuscasino.roulette import roulette_color


# Assuming the function signature:
# roulette_color(color, bet=1, rng=None)
# Returns: dict with {'result': 'win'/'loss', 'spin': 'red'/'black'/'green', 'payout': int}


def test_roulette_wins_on_matching_color():
    """Test that betting on a color and spinning that color results in a win."""
    # Mock the RNG to return red
    mock_rng = Mock()
    mock_rng.choice = Mock(return_value="red")
    
    result = roulette_color("red", bet=10, rng=mock_rng)
    
    assert result['result'] is True
    assert result['spin'] == 'red'
    assert result['payout'] == 10


def test_roulette_loses_on_opposite_color():
    """Test that betting on a color and spinning the opposite color results in a loss."""
    # Mock the RNG to return black
    mock_rng = Mock()
    mock_rng.choice = Mock(return_value="black")
    
    result = roulette_color("red", bet=10, rng=mock_rng)
    
    assert result['result'] is False
    assert result['spin'] == 'black'
    assert result['payout'] == -10


def test_roulette_loses_on_green():
    """Test that any bet loses when green hits (house wins)."""
    # Mock the RNG to return green
    mock_rng = Mock()
    mock_rng.choice = Mock(return_value="green")
    
    result = roulette_color("red", bet=15, rng=mock_rng)
    
    assert result['result'] is False
    assert result['spin'] == 'green'
    assert result['payout'] == -15


def test_roulette_default_bet():
    """Test that the default bet is 1 when not specified."""
    mock_rng = Mock()
    mock_rng.choice = Mock(return_value="red")
    
    result = roulette_color("red", rng=mock_rng)
    
    assert result['payout'] == 1


def test_roulette_different_bet_amounts():
    """Test that payout scales correctly with different bet amounts."""
    mock_rng = Mock()
    mock_rng.choice = Mock(return_value="black")
    
    # Test a few different bet amounts
    result1 = roulette_color("black", bet=5, rng=mock_rng)
    assert result1['payout'] == 5
    
    result2 = roulette_color("black", bet=100, rng=mock_rng)
    assert result2['payout'] == 100


def test_roulette_invalid_color():
    """Test that invalid color inputs raise a ValueError."""
    mock_rng = Mock()
    mock_rng.choice = Mock(return_value="red")
    
    with pytest.raises(ValueError):
        roulette_color("blue", bet=10, rng=mock_rng)


def test_roulette_probability_distribution():
    """
    Test that over many spins, outcomes roughly match expected probabilities.
    In American roulette: ~47% red, ~47% black, ~5% green.
    """
    n_trials = 1000
    outcomes = {'red': 0, 'black': 0, 'green': 0}
    
    for _ in range(n_trials):
        result = roulette_color("red", bet=1)
        outcomes[result['spin']] += 1
    
    # Check that we get reasonable distribution (generous ranges for randomness)
    assert 400 <= outcomes['red'] <= 550
    assert 400 <= outcomes['black'] <= 550
    assert 10 <= outcomes['green'] <= 100