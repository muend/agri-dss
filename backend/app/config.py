"""Uygulama yapılandırması — ortam değişkenlerinden okunur (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # PostgreSQL / PostGIS bağlantısı
    database_url: str = "postgresql+psycopg2://agri:agri@db:5432/agridss"

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Agri-DSS API"

    # Frontend'in erişebileceği originler (CORS). Virgülle ayrılmış.
    cors_origins: str = "http://localhost:8000,http://localhost:3000,https://tarimsalkoridor.online"

    # Seed dosyası (mevcut data.json'un birebir kopyası)
    seed_file: str = "data/data.json"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
