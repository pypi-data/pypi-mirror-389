# example_function_usage.py
"""
Demo script for the nimbuscasino package.
It showcases:
  1) coinflip.coinflip(...)
  2) roulette.roulette(...)
  3) rps.rps(...)
  
Run:
  python example_function_usage.py
  python example_function_usage.py --rounds 5 --bet 2
"""

import argparse
from nimbuscasino import coinflip, roulette, rps


def demo_coinflip(rounds: int = 3, bet: int = 1) -> None:
    """
    Demo coinflip: place a bet on 'heads' or 'tails' and show the result.
    Assumes coinflip.coinflip(side: str, bet: int = 1) -> tuple[str, int]
      where the first return is 'win'/'lose' and the second is +bet/-bet.
    """
    print("\n=== Coinflip demo ===")
    
    for side in ["heads", "tails"]:
        for i in range(rounds):
            result = coinflip.coinflip(side, bet=bet)
    #     return CoinflipResult(
    #     game="coinflip",
    #     guess=g,
    #     flip=flip,
    #     win=win,
    #     payout=payout,
    #     prob_heads=bias,
    # )
            print(f"Round {i+1:>2} bet={bet:>2} on {side:<5} -> {result["win"]:>4}, payout={result["payout"]:+d}")


def demo_roulette(rounds: int = 3, bet: int = 1) -> None:
    """
    Demo roulette: bet on a color ('red' / 'black').
    Assumes roulette.roulette(color: str, bet: int = 1) -> tuple[str, int]
      returns 'win'/'lose' and +/-bet (green loses).
    """
    print("\n=== Roulette demo ===")
    for color in ["red", "black"]:  
        for i in range(rounds):
            spin, result,payout = roulette.roulette_color(color, bet=bet)
    #     return {
    #     'result': result,
    #     'spin': spin_result,
    #     'payout': payout
    # }
            print(f"Round {i+1:>2} bet={bet:>2} on {color:<5} -> {result:>4}, payout={payout}")


def demo_rps(rounds: int = 3) -> None:
    """
    Demo RPS: play rock-paper-scissors by passing 'rock'/'paper'/'scissors'.
    Assumes rps.rps(move: str) -> tuple[str, int]
      where return is 'win'/'lose'/'tie' and bet is 1/-1/0 accordingly.
    """
    print("\n=== Rock-Paper-Scissors demo ===")
    for move in ["rock", "paper", "scissors"]:
        for i in range(rounds):
            # return result, payout
            result, payout = rps.rps(move)
            print(f"Round {i+1:>2} move={move:<9} -> {result:>4}, score_delta={payout:+d}")


def demo_all(rounds: int, bet: int) -> None:
    demo_coinflip(rounds=rounds, bet=bet)
    demo_roulette(rounds=rounds, bet=bet)
    demo_rps(rounds=rounds)

    


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Demonstrate all functions of nimbuscasino")
    p.add_argument("--rounds", type=int, default=3, help="number of demo rounds per game")
    p.add_argument("--bet", type=int, default=1, help="bet amount for coinflip/roulette demos")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    demo_all(rounds=args.rounds, bet=args.bet)

