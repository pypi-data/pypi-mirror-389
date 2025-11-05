"""
Roulette color betting game for nimbuscasino package.

Implements a simplified American roulette wheel (color bets only). 
"""

import random

def roulette_color(color, bet=1, rng=None):
    """
    Play a simplified roulette game by betting on red or black.
    
    American roulette has 38 slots:
    - 18 red numbers
    - 18 black numbers  
    - 2 green numbers (0 and 00)
    
    If the wheel lands on your color, you win an amount equal to your bet.
    If it lands on the opposite color or green, you lose your bet.
    
    Args:
        color (str): The color to bet on. Must be "red" or "black" (lowercase).
        bet (int or float, optional): The amount to bet. Must be positive. Defaults to 1.
        rng (optional): Random number generator with a choice() method. 
                       If None, uses Python's default random module.
    
    Returns:
        dict: A dictionary containing:
            - 'result' (str): Either "win" or "loss"
            - 'spin' (str): The color that came up ("red", "black", or "green")
            - 'payout' (int or float): Your winnings (positive) or losses (negative)
    
    Raises:
        ValueError: If color is not "red" or "black", or if bet is not positive.
        TypeError: If bet is not a number.
    """
    # Validate color input
    if not isinstance(color, str):
        raise TypeError("Color must be a string ('red' or 'black')")
    
    if color not in ["red", "black"]:
        raise ValueError(f"Invalid color '{color}'. Must be 'red' or 'black' (lowercase)")
    
    # Validate bet input
    if not isinstance(bet, (int, float)):
        raise TypeError("Bet must be a number (int or float)")
    
    if bet < 0:
        raise ValueError("Bet must be positive (greater than or equal to 0)")
    
    # Create the roulette wheel with proper American roulette distribution
    # 18 red slots, 18 black slots, 2 green slots (0 and 00)
    wheel = (
        ["red"] * 18 +
        ["black"] * 18 +
        ["green"] * 2
    )
    
    # Spin the wheel using provided RNG or default random
    if rng is not None:
        spin_result = rng.choice(wheel)
    else:
        spin_result = random.choice(wheel)
    
    # Determine win or loss
    result = (spin_result == color)
    payout = float((bet if result else -bet))
    
    return {
        'game': "roulette",
        'guess': color,
        'result': result,
        'spin': spin_result,
        'payout': payout
    }