from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Payment Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/payment_db"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672"
    STRIPE_SECRET_KEY: str = "sk_test_your_key_here"
    STRIPE_WEBHOOK_SECRET: str = "whsec_your_webhook_secret_here"

    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
