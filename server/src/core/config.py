from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agent Studio"
    DESCRIPTION: str = "Real-time debugger and visualizer for LangGraph"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    DEBUG: bool = True

    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./database.db"


settings = Settings()
