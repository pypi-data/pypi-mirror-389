from pathlib import Path
from typing import Literal

from platformdirs import user_log_dir
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Load and validate application settings from the environment or a .env file."""

    # Application Behaviour
    APP_MODE: Literal["development", "production"] = "development"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_TYPE: str = "standard"
    LOG_BACKUP_COUNT: int = 7  # 7 Days
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB

    _default_log_dir: Path = Path(user_log_dir("rock_paper_scissors", "Filming"))
    LOG_PATH: Path = _default_log_dir / "rock_paper_scissors.log"

    # Pydantic Model Configuration
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
