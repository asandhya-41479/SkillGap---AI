from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    frontend_origin: str

    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str
    github_frontend_redirect: str

    gemini_api_key: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()