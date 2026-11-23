# SUMMARY: Centraliza la configuraciÃ³n de entorno de la aplicaciÃ³n con carga de .env tolerante a variables adicionales.
"""ConfiguraciÃ³n validada de la aplicaciÃ³n y sus variables de entorno."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Summary: Representa los valores de configuraciÃ³n de la aplicaciÃ³n."""

    # Los nombres de campos se conservan para los consumidores de configuraciÃ³n.
    app_name: str = "SystemBioTrack ETI"
    environment: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/systembiotrack_db"  # Guarda la URL de conexión a PostgreSQL.

    # El archivo .env puede contener variables de otros componentes del backend.
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Summary: Devuelve una instancia cacheada de la configuraciÃ³n validada."""
    return Settings()
