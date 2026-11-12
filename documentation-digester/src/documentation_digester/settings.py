from pathlib import Path

from pydantic import BaseModel
from dotenv import load_dotenv
import os

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)


class Settings(BaseModel):
    ENV: str = "development"
    DEBUG: bool = False
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"


settings = Settings(
    OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY", ""),
    OPENROUTER_MODEL=os.getenv("OPENROUTER_MODEL", "openrouter/free"),
    OPENROUTER_BASE_URL=os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    ),
    CHROMA_PERSIST_DIRECTORY=os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        "./data/chroma",
    ),
)
