# SUMMARY: Centraliza la configuración de entorno de la aplicación, incluyendo la conexión PostgreSQL y los parámetros del servidor FastAPI.
from __future__ import annotations  # Habilita anotaciones modernas para apoyar tipado fuerte y compatibilidad futura.
from functools import lru_cache  # Proporciona caché memoizada para evitar recrear la configuración en cada acceso.
from pydantic_settings import BaseSettings  # Importa la clase base para settings con soporte de .env.


class Settings(BaseSettings):  # Define la clase de configuración de la aplicación con validación automática.
    app_name: str = "SystemBioTrack ETI"  # Asigna el nombre visible del servicio backend.
    environment: str = "development"  # Guarda el entorno actual para activar comportamientos distintos por ambiente.
    debug: bool = False  # Activa modo depuración cuando se desea diagnóstico detallado.
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/systembiotrack_db"  # Guarda la URL de conexión a PostgreSQL.

    class Config:  # Define metadatos de configuración para Pydantic Settings.
        env_file = ".env"  # Busca el archivo .env en la raíz del proyecto para cargar variables.
        case_sensitive = False  # Hace que nombres de variables sean insensibles a mayúsculas/minúsculas.


@lru_cache  # Mantiene una instancia única de configuración en memoria para el proceso.
def get_settings() -> Settings:  # Retorna la configuración singleton de la aplicación.
    return Settings()  # Instancia Settings y carga las variables desde el entorno y .env.
