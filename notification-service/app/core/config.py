from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Notification Service"
    APP_VERSION: str = "1.0.0"

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672"

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@ecommerce.local"

    class Config:
        env_file = ".env"


settings = Settings()
