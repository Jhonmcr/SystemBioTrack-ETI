# SUMMARY: Expone los elementos de acceso a la base de datos para que la app pueda importar Base, engine y session de forma centralizada.
from app.db.base import Base  # Importa la clase base declarativa para que todos los modelos se registren correctamente.
from app.db.session import SessionLocal, create_db_and_tables  # Importa la sesión y la utilidad de inicialización de tablas.

__all__ = ["Base", "SessionLocal", "create_db_and_tables"]  # Publica los símbolos principales que usa la aplicación.
