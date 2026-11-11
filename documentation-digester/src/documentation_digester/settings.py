from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    ENV: str = "development"
    DEBUG: bool = False
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"


settings = Settings(
    OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
    OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    CHROMA_PERSIST_DIRECTORY=os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        "./data/chroma",
    ),
)