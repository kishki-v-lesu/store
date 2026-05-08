from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Order Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/order_db"
    REDIS_URL: str = "redis://localhost:6379/2"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672"
    PRODUCT_SERVICE_URL: str = "http://product-service:8000"
    PAYMENT_SERVICE_URL: str = "http://payment-service:8000"

    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
