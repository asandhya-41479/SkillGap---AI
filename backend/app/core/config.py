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

    # Password-reset emails (optional). Sent through Brevo's HTTPS API because Render's free plan
    # blocks SMTP ports. When BREVO_API_KEY is empty, no email is sent (see email_service.py).
    brevo_api_key: str = ""
    email_from: str = ""
    email_from_name: str = "SkillGap AI"
    password_reset_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()