# SUMMARY: Conserva la configuración de base de datos de la implementación heredada.
"""
=============================================================================
SUMMARY DEL MÓDULO
-----------------------------------------------------------------------------
Proyecto: Sistema de Control de Asistencia Biométrico (SystemBioTrack-ETI)
Módulo: Módulo 3 - Motor Biométrico y Asistencia (Core)
Responsable: Pablo
Archivo: database.py
Descripción: Configuración del motor de persistencia relacional PostgreSQL
             empleando SQLAlchemy para gestionar el pool de conexiones.
=============================================================================
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carga de variables de entorno locales
load_dotenv()

# Variables de conexión homologadas
Usuario_Db = os.getenv("DB_USER", "postgres")
Password_Db = os.getenv("DB_PASS", "postgres")
Host_Db = os.getenv("DB_HOST", "127.0.0.1")
Puerto_Db = os.getenv("DB_PORT", "5432")
Nombre_Db = os.getenv("DB_NAME", "systembiotrack_db")

# Cadena de conexión para PostgreSQL especificando el driver psycopg2
Url_Conexion_Postgres = f"postgresql+psycopg2://{Usuario_Db}:{Password_Db}@{Host_Db}:{Puerto_Db}/{Nombre_Db}"

# Motor de conexión SQLAlchemy
Motor_Base_Datos = create_engine(
    Url_Conexion_Postgres,
    pool_pre_ping=True
)

# Fábrica de sesiones para transacciones en endpoints
Sesion_Local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=Motor_Base_Datos
)

# Base declarativa para modelos ORM
Base_Entidad = declarative_base()


def Obtener_Sesion_Db():
    """
    Generador de sesión para inyección de dependencias en FastAPI.
    Asegura la liberación y cierre de la conexión al culminar la petición.
    """
    Sesion_Actual = Sesion_Local()
    try:
        yield Sesion_Actual
    finally:
        Sesion_Actual.close()