from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./resume_analyzer.db"
    JWT_SECRET: str
    ENV: str = "development"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None
    TRUSTED_PROXY: bool = False
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_MB: int = 5
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_MODEL_FALLBACKS: str = "gemini-3.5-flash,gemini-3.1-flash-lite,gemini-2.5-flash"
    CORS_ORIGIN: str = "http://localhost:5173"
    USE_EMBEDDINGS: bool = False

    @field_validator("GEMINI_API_KEY", mode="before")
    @classmethod
    def _validate_gemini_key(cls, v: Optional[str]) -> Optional[str]:
        if not v or str(v).strip() in ("", "your_gemini_api_key_here"):
            return None
        return str(v).strip()

    @property
    def candidate_gemini_models(self) -> List[str]:
        candidates = [self.GEMINI_MODEL.strip()]
        if self.GEMINI_MODEL_FALLBACKS:
            for item in self.GEMINI_MODEL_FALLBACKS.split(","):
                m = item.strip()
                if m and m not in candidates:
                    candidates.append(m)
        return candidates

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
