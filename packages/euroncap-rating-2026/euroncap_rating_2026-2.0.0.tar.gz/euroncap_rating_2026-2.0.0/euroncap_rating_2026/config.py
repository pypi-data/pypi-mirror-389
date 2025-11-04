from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
import logging

# Suppress debug/info logs from PIL and matplotlib
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)


class Settings(BaseSettings):
    log_level: str = Field(
        default="INFO",
        description="Logging level for the application (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    model_config = SettingsConfigDict(env_prefix="euroncap_rating_2026_")


def logging_config():
    settings = Settings()

    # Set log level from settings
    level = getattr(logging, settings.log_level.upper(), logging.DEBUG)
    log_file = os.path.join(os.getcwd(), "euroncap_rating_2026.log")

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter("[%(asctime)s] %(name)s %(levelname)s: %(message)s")

    # Clear old handlers to prevent duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, mode="w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    logging.debug("Logging initialized for all modules.")
