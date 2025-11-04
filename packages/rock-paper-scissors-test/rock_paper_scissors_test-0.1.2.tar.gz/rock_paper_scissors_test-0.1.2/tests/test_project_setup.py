from rock_paper_scissors import RockPaperScissors, RockPaperScissorsError, __version__


def test_version_is_a_string() -> None:
    """Test that the __version__ attribute exists and is a string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_core_components_are_importable() -> None:
    """Check that the main public components of the package can be imported."""
    """
    The imports at the top of this file already prove this works,
    but this test makes the intent explicit and provides a clear
    failure point if the public API changes unexpectedly.
    """
    try:
        assert callable(RockPaperScissors)
        assert issubclass(RockPaperScissorsError, Exception)
    except NameError as e:
        raise AssertionError("Core components could not be imported.") from e


def test_can_instantiate_client() -> None:
    """Test that the main client class can be instantiated without errors."""
    try:
        client = RockPaperScissors()
        assert isinstance(client, RockPaperScissors)
    except Exception as e:
        raise AssertionError(f"Failed to instantiate the main client class: {e}") from e
