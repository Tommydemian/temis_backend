from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"

    db_user: str = "postgres"
    db_password: str
    db_database: str
    db_host: str = "127.0.0.1"
    db_port: str = "5432"

    SECRET_KEY: str

    TIENDANUBE_APP_ID: str
    TIENDANUBE_CLIENT_SECRET: str
    TIENDANUBE_REDIRECT_URI: str

    FRONTEND_URL: str

    CUIT: str

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
