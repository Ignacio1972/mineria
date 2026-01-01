from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    PROJECT_NAME: str = "Mineria Prefactibilidad Ambiental"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database (puerto 5433 externo para desarrollo local, Docker usa puerto interno)
    DATABASE_URL: str = "postgresql://mineria:mineria_dev_2024@localhost:5433/mineria"

    # Redis (puerto 6380 externo para desarrollo local, Docker usa puerto interno)
    REDIS_URL: str = "redis://localhost:6380/0"

    # LLM - Anthropic
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_MAX_TOKENS: int = 4096

    # LLM - Perplexity
    PERPLEXITY_API_KEY: str = ""
    PERPLEXITY_DEFAULT_MODEL: str = "sonar-pro"
    PERPLEXITY_TIMEOUT_SECONDS: int = 120
    PERPLEXITY_ENABLED: bool = True

    # GIS
    DEFAULT_SRID: int = 4326
    BUFFER_AREAS_PROTEGIDAS_M: int = 50000
    BUFFER_COMUNIDADES_M: int = 30000
    BUFFER_CUERPOS_AGUA_M: int = 10000
    BUFFER_GLACIARES_M: int = 20000
    BUFFER_CENTROS_POBLADOS_M: int = 20000

    # RAG
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384
    RAG_TOP_K: int = 10

    # Uploads
    UPLOAD_DIR: str = "/var/www/mineria/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
