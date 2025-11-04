import logging
import random
from typing import get_args  # <-- IMPORT THIS

from rock_paper_scissors.config import settings
from rock_paper_scissors.game import CHOICES, get_winner
from rock_paper_scissors.logging_setup import setup_logging

logger = logging.getLogger(__name__)  # <-- CORRECT WAY TO GET LOGGER

setup_logging(logger_type=settings.LOG_TYPE)


def main() -> None:
    """Start the application."""
    player_choice: CHOICES = "rock"

    computer_choice: CHOICES = random.choice(get_args(CHOICES))  # <-- THE FIX

    logging.info(f"Player chose: {player_choice}, Computer chose: {computer_choice}")

    winner = get_winner(player_choice, computer_choice)

    if winner == "player":
        logging.info("🎉 Player wins!")
    elif winner == "computer":
        logging.info("🤖 Computer wins!")
    else:
        logging.info("🤝 It's a draw!")


if __name__ == "__main__":
    main()
