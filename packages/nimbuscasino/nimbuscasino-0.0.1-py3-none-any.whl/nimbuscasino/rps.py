import random

def rps(player, bet=1):
    """
    Plays a Rock-Paper-Scissors round against the computer.
    
    Parameters:
    -----------
    player : str
        Player's choice: "rock", "paper", or "scissors".
    bet : int or float, optional
        Amount of money wagered for the round. Default = 1.
    
    Returns:
    --------
    tuple (result, payout)
        result: "win", "lose", or "tie"
        payout: numeric value of the win/loss based on bet
    """
    
    # Normalize input
    player = player.lower()
    valid_choices = ["rock", "paper", "scissors"]
    
    if player not in valid_choices:
        raise ValueError(f"Invalid choice '{player}'. Choose from {valid_choices}.")
    
    # Computer randomly chooses
    computer = random.choice(valid_choices)
    
    # Determine outcome
    if player == computer:
        result = "tie"
        payout = 0
    elif (
        (player == "rock" and computer == "scissors") or
        (player == "scissors" and computer == "paper") or
        (player == "paper" and computer == "rock")
    ):
        result = "win"
        payout = bet
    else:
        result = "lose"
        payout = -bet
    
    print(f"You chose {player}, computer chose {computer} → {result.upper()}")
    return result, payout
