"""JobFit AI — Application Configuration (Singleton Pattern).

Loads all environment variables via pydantic-settings. Provides computed
properties for environment-specific behavior (CORS, log level, etc.).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    app_env: str = "development"
    max_upload_size_mb: int = 10

    # --- Database ---
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@postgres:5432/jobfit_dev"
    )

    # --- Redis ---
    redis_url: str = "redis://redis:6379/0"

    # --- Authentication ---
    jwt_secret_key: str = "dev-secret-key-not-for-production"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # --- LLM ---
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    llm_provider: str = "openai"
    # JD Analyzer agent (optimization pipeline)
    jd_analyzer_model: str = "gpt-4o-mini"
    jd_analyzer_temperature: float = 0.0
    # RAG Retriever agent (optimization pipeline — vector search only, no LLM)
    rag_retriever_top_k: int = 10
    rag_retriever_relevance_threshold: float = 0.3

    # --- Vector Store ---
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # --- Object Storage ---
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "jobfit-uploads-dev"

    # --- Stripe ---
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # --- Logging ---
    log_level: str = "DEBUG"
    uvicorn_workers: int = 1

    # --- Computed Properties ---
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    @property
    def cors_origins(self) -> list[str]:
        """Return allowed CORS origins based on environment."""
        if self.is_production:
            return ["https://jobfit.ai"]
        return ["*"]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance (Singleton)."""
    return Settings()
