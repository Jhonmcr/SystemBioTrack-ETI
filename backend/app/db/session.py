# SUMMARY: Configura el engine, la sesión de SQLAlchemy y la creación de tablas para PostgreSQL con un patrón de inyección de dependencias compatible con FastAPI.
from __future__ import annotations  # Permite usar tipos modernos en funciones y dependencias.
from typing import Generator  # Importa Generator para tipar la dependencia de sesión de FastAPI.
from sqlalchemy import create_engine  # Importa la fábrica del motor de base de datos.
from sqlalchemy.orm import Session, sessionmaker  # Importa la sesión y el constructor de sesiones de SQLAlchemy.
from app.core.config import get_settings  # Importa la configuración centralizada del proyecto.
from app.db.base import Base  # Importa Base para registrar modelos antes de crear tablas.

settings = get_settings()  # Carga la configuración actual del proyecto una sola vez.
engine = create_engine(settings.database_url, pool_pre_ping=True)  # Crea el engine con verificación de conexiones activas.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Fabrica sesiones ORM para cada request.


def get_db() -> Generator[Session, None, None]:  # Define la dependencia que FastAPI usará para obtener una sesión por petición.
    db = SessionLocal()  # Abre una nueva sesión para la ejecución actual.
    try:  # Inicia bloque try/finally para garantizar cierre seguro.
        yield db  # Entrega la sesión al endpoint o servicio que la consume.
    finally:  # Ejecuta limpieza siempre al finalizar la petición.
        db.close()  # Cierra la sesión para liberar recursos del pool de conexiones.


def create_db_and_tables() -> None:  # Crea las tablas de la base de datos si aún no existen.
    Base.metadata.create_all(bind=engine)  # Ejecuta creación de todos los modelos ligados a Base.
