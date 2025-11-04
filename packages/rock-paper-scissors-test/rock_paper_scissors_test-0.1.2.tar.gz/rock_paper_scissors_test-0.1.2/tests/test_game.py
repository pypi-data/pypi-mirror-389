# in tests/test_game.py
from rock_paper_scissors.game import get_winner


def test_get_winner_player_wins() -> None:
    """Test scenarios where the player should win."""
    assert get_winner(player_choice="rock", computer_choice="scissors") == "player"
    assert get_winner(player_choice="paper", computer_choice="rock") == "player"
    assert get_winner(player_choice="scissors", computer_choice="paper") == "player"


def test_get_winner_computer_wins() -> None:
    """Test scenarios where the computer should win."""
    assert get_winner(player_choice="scissors", computer_choice="rock") == "computer"
    assert get_winner(player_choice="paper", computer_choice="scissors") == "computer"
    assert get_winner(player_choice="rock", computer_choice="paper") == "computer"


def test_get_winner_is_a_draw() -> None:
    """Test scenarios that should result in a draw."""
    assert get_winner(player_choice="rock", computer_choice="rock") == "draw"
    assert get_winner(player_choice="paper", computer_choice="paper") == "draw"
    assert get_winner(player_choice="scissors", computer_choice="scissors") == "draw"
