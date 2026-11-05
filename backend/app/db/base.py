# SUMMARY: Define la clase base SQLAlchemy que será heredada por todos los modelos de la aplicación para un patrón común y limpio.
from sqlalchemy.orm import DeclarativeBase  # Importa la base declarativa moderna de SQLAlchemy 2.0.


class Base(DeclarativeBase):  # Crea la clase base para que cada modelo declare sus columnas y relaciones.
    pass  # Deja la clase base vacía para que SQLAlchemy maneje el metadato del modelo.
