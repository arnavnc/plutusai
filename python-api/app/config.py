from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openalex_api_url: str = "https://api.openalex.org/works"
    contact_email: str  # Add this for OpenAlex API polite pool
    discord_bot_token: str
    discord_guild_id: str
    discord_channel_id: str
    discord_client_id: str  # Application ID from Discord Developer Portal

    class Config:
        env_file = ".env"

settings = Settings() 