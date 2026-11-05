# SUMMARY: Define el modelo SQLAlchemy Schedule para horarios y reglas de entrada con margen de tolerancia.
from __future__ import annotations  # Permite type hints modernas y referencias futuras en relaciones.
from datetime import time  # Importa el tipo time de Python para manejar horarios de entrada.
from sqlalchemy import Integer, String, Time  # Importa tipos SQLAlchemy para la entidad de horario.
from sqlalchemy.orm import Mapped, mapped_column  # Importa la sintaxis declarativa moderna de SQLAlchemy 2.0.
from app.db.base import Base  # Importa Base para registrar el modelo en metadata.


class Schedule(Base):  # Define la entidad del horario escolar y reglas de asistencia.
    __tablename__ = "schedules"  # Establece el nombre de la tabla que representa los horarios.

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)  # Guarda el identificador único del horario.
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)  # Guarda el nombre del horario para distinguir reglas por grupo o aula.
    entry_time: Mapped[time] = mapped_column(Time, nullable=False)  # Guarda la hora oficial de entrada para el cálculo de tardanzas.
    grace_period_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Guarda el margen de tolerancia permitido antes de marcar tardanza.
