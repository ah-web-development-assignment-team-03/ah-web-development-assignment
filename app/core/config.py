from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_PATH: str = "./ai_health.db"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
