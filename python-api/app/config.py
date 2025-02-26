from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openalex_api_url: str = "https://api.openalex.org/works"
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600  # 1 hour in seconds
    contact_email: str  # Add this for OpenAlex API polite pool

    class Config:
        env_file = ".env"

settings = Settings() 