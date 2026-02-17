from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finanças Cristãs API"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    DATABASE_URL: str = "postgresql://financas_user:financas_pass@localhost:5432/financas_db"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
