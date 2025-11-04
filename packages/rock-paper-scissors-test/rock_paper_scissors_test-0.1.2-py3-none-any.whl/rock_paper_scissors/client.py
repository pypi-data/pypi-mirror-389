import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class RockPaperScissors:
    """A Game Of Rps."""

    def __init__(self) -> None:
        """Initialize the RockPaperScissors instance."""
        logger.info("RockPaperScissors instance has been initialized.")
