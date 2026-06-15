from pydantic import computed_field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base de datos (PostgreSQL)
    postgres_user: str = "postgres"
    postgres_password: str = "shina"
    postgres_db: str = "parcial_prog_4"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return(
        f"postgresql://{self.postgres_user}:{self.postgres_password}"
        f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # JWT
    SECRET_KEY: str = "dev-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MercadoPago
    mp_access_token: str = ""
    mp_public_key: str = ""
    mp_webhook_secret: str = ""
    mp_ngrok_url: str = "https://gesture-fame-idealize.ngrok-free.dev"
    frontend_url: str = "http://localhost:5173"
    frontend_admin_url: str = "http://localhost:5174" 

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()
