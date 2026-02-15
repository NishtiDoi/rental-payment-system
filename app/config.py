from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USER: str = "nishti"   # change from "postgres"
    DB_PASSWORD: str = "1234"     # leave blank if no password
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str = "rental_payment_system"

    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"

settings = Settings()   # <- this must exist at the bottom