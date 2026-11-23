# SUMMARY: Configura el engine, la sesión de SQLAlchemy y la creación de tablas para PostgreSQL con un patrón de inyección de dependencias compatible con FastAPI.
from __future__ import annotations  # Permite usar tipos modernos en funciones y dependencias.
from typing import Generator  # Importa Generator para tipar la dependencia de sesión de FastAPI.
from sqlalchemy import create_engine  # Importa la fábrica del motor de base de datos.
from sqlalchemy.orm import Session, sessionmaker  # Importa la sesión y el constructor de sesiones de SQLAlchemy.
from app.core.config import get_settings  # Importa la configuración centralizada del proyecto.
from app.db.base import Base  # Importa Base para registrar modelos antes de crear tablas.

Configuracion = get_settings()  # Carga la configuración actual del proyecto una sola vez.
Motor_Base_Datos = create_engine(Configuracion.database_url, pool_pre_ping=True)  # Crea el engine con verificación de conexiones activas.
Sesion_Local = sessionmaker(autocommit=False, autoflush=False, bind=Motor_Base_Datos)  # Fabrica sesiones ORM para cada request.


def get_db() -> Generator[Session, None, None]:  # Define la dependencia que FastAPI usará para obtener una sesión por petición.
    Db_Sesion = Sesion_Local()  # Abre una nueva sesión para la ejecución actual.
    try:  # Inicia bloque try/finally para garantizar cierre seguro.
        yield Db_Sesion  # Entrega la sesión al endpoint o servicio que la consume.
    finally:  # Ejecuta limpieza siempre al finalizar la petición.
        Db_Sesion.close()  # Cierra la sesión para liberar recursos del pool de conexiones.


def create_db_and_tables() -> None:  # Crea las tablas de la base de datos si aún no existen.
    Base.metadata.create_all(bind=Motor_Base_Datos)  # Ejecuta creación de todos los modelos ligados a Base.
