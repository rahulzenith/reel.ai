from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Both locations work; backend/.env wins if both exist
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure OpenAI — chat deployment (separate resource/key from embeddings)
    azure_openai_chat_endpoint: str = ""
    azure_openai_chat_api_key: str = ""
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_chat_api_version: str = "2024-10-21"

    # Azure OpenAI — embedding deployment (separate endpoint + key)
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_api_key: str = ""
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_embedding_api_version: str = "2024-10-21"
    embedding_dim: int = 1536

    # Cartesia (primary TTS)
    cartesia_api_key: str = ""
    cartesia_model_id: str = "sonic-2"
    cartesia_voice_id: str = ""

    # ElevenLabs (secondary TTS)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_model_id: str = "eleven_turbo_v2_5"

    # Optional services
    tavily_api_key: str = ""
    pexels_api_key: str = ""
    langsmith_tracing: bool = True
    langsmith_api_key: str = ""
    langsmith_project: str = "shorts-factory"
    langsmith_endpoint: str = "https://api.smith.langchain.com"  # EU: https://eu.api.smith.langchain.com

    # YouTube (live publish only)
    youtube_client_secret_file: str = "client_secret.json"
    youtube_token_file: str = "token.json"

    publish_mode: str = "dry_run"  # dry_run | live

    database_url: str = "postgresql://postgres:postgres@localhost:5432/shortsfactory"

    # Pipeline tuning
    hook_score_threshold: float = 0.7
    max_script_retries: int = 2
    target_duration_seconds: int = 50
    max_video_seconds: int = 59  # hard ceiling — audio is tempo-adjusted to fit
    niche: str = "ai and technology"
    caption_font_path: str = "assets/fonts/Anton-Regular.ttf"
    topic_dedup_distance: float = 0.25
    topic_dedup_days: int = 30

    # Scheduler
    schedule_hour: int = 8
    schedule_minute: int = 0
    tz: str = "Asia/Kolkata"
    scheduler_enabled: bool = True

    output_dir: str = "../outputs"

    @property
    def has_cartesia(self) -> bool:
        return bool(self.cartesia_api_key and self.cartesia_voice_id)

    @property
    def has_tavily(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def has_pexels(self) -> bool:
        return bool(self.pexels_api_key)

    @property
    def has_youtube_creds(self) -> bool:
        return (BACKEND_DIR / self.youtube_client_secret_file).exists()

    @property
    def caption_font(self) -> Path:
        p = Path(self.caption_font_path)
        return p if p.is_absolute() else BACKEND_DIR / p

    @property
    def outputs_path(self) -> Path:
        p = Path(self.output_dir)
        return (p if p.is_absolute() else BACKEND_DIR / p).resolve()


settings = Settings()
