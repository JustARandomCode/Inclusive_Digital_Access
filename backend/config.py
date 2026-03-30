import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    mongo_uri: str
    mongo_db_name: str = "ida"
    ollama_base_url: str
    api_port: int = 8000
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    supported_languages: str = "en,hi,mr"
    whisper_model: str = "base"

    model_config = SettingsConfigDict(env_file=None)

    # No default_password - authentication is per-user (see auth.py)

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_not_be_weak(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    @field_validator("mongo_uri")
    @classmethod
    def mongo_uri_must_not_be_localhost(cls, v: str) -> str:
        # Catch the common mistake of shipping the dev .env into containers
        if "localhost" in v and os.getenv("ALLOW_LOCALHOST_MONGO") != "true":
            raise ValueError(
                "MONGO_URI contains 'localhost'. "
                "In Docker use the service name e.g. mongodb://mongodb:27017/ida. "
                "Set ALLOW_LOCALHOST_MONGO=true to override for local dev."
            )
        return v

    class Config:
        # Do NOT load a .env file inside the container.
        # Configuration comes from the environment block in docker-compose.yml.
        # For local development outside Docker, export variables manually or
        # use 'source .env.local' before running uvicorn.
        env_file = None


settings = Settings()#type: ignore
