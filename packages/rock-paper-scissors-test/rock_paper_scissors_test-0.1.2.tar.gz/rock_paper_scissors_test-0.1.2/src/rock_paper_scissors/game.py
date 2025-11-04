from typing import Literal

CHOICES = Literal["rock", "paper", "scissors"]


def get_winner(
    player_choice: CHOICES, computer_choice: CHOICES
) -> Literal["player", "computer", "draw"]:
    """Determine the winner of a Rock Paper Scissors round."""
    if player_choice == computer_choice:
        return "draw"

    winning_combinations = {
        "rock": "scissors",
        "paper": "rock",
        "scissors": "paper",
    }

    if winning_combinations[player_choice] == computer_choice:
        return "player"
    else:
        return "computer"
