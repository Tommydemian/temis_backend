from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    SECRET_KEY: str

    TIENDANUBE_APP_ID: str
    TIENDANUBE_CLIENT_SECRET: str
    TIENDANUBE_REDIRECT_URI: str

    FRONTEND_URL: str

    CUIT: str

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore
