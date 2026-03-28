from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str
    github_webhook_secret: str = ""
    github_token: str = ""
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    wandb_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()