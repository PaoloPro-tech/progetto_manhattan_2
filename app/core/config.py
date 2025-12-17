# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Mana"
    DEBUG_MODE: bool = True

    # API KEYS (Le leggerà dal file .env)
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str

    # RAG (Repo-based)
    RAG_PERSIST_DIR: str = "./app/data/.rag/chroma"
    RAG_COLLECTION_NAME: str = "internal_repo"
    RAG_TOP_K: int = 4
    RAG_REPO_ROOT: str = "."

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

settings = Settings()
