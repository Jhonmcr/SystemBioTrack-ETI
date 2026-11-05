# SUMMARY: Define el modelo SQLAlchemy User para estudiantes y personal con información básica, grado, sección y estado activo.
from __future__ import annotations  # Permite referencias tipo avanzadas y compatibilidad con Python 3.11+.
from sqlalchemy import Boolean, Integer, String  # Importa tipos SQLAlchemy para columnas de texto, identificador y booleano.
from sqlalchemy.orm import Mapped, mapped_column, relationship  # Importa API declarativa moderna de SQLAlchemy 2.0.
from app.db.base import Base  # Importa Base para que el modelo se registre en metadata.


class User(Base):  # Define la entidad de estudiantes y personal del sistema.
    __tablename__ = "users"  # Establece el nombre de la tabla en PostgreSQL.

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)  # Guarda el identificador único primario del usuario.
    employee_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # Almacena el número de empleado o identificación del usuario.
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Guarda el nombre del estudiante o personal.
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Guarda el apellido del estudiante o personal.
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Guarda el grado escolar si aplica al registro.
    section: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Guarda la sección si la entidad pertenece a un grupo académico.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # Indica si la persona está activa en el sistema.

    attendances: Mapped[list["AttendanceLog"]] = relationship(back_populates="user")  # Relaciona cada usuario con sus marcajes y registros de asistencia.
