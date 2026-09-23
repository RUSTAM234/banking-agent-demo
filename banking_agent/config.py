import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env.example")

DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "banking.db"
LOG_PATH = DATA_DIR / "banking_agent.log"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def configure_logging() -> None:
    """Initialize the app-wide logging config so messages are captured in both console and file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[console_handler, file_handler],
        force=True,
    )
